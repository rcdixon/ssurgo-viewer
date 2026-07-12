import os
import json
import base64
import zipfile
import tempfile
import geopandas as gpd
from soildb import spatial_query
import pandas as pd
import asyncio
import math

from utils.configLoader import QUERIES
from components.api_tools import query_sda


def decode_upload(contents):
    """Decode Dash upload content into raw bytes.

    Args:
        contents: Base64-encoded upload string from Dash.

    Returns:
        Decoded bytes of the uploaded file.
    """
    _, content_string = contents.split(",", 1)
    return base64.b64decode(content_string)


def load_geojson(file_bytes):
    """Convert GeoJSON bytes into a GeoDataFrame.

    Args:
        file_bytes: Raw bytes representing a GeoJSON file.

    Returns:
        GeoDataFrame loaded from the GeoJSON content.
    """
    geojson_data = json.loads(file_bytes.decode("utf-8"))
    gdf = gpd.GeoDataFrame.from_features(geojson_data["features"])

    if gdf.crs is None:
        gdf.set_crs(epsg=4326, inplace=True)

    return gdf


def find_shapefile(directory):
    """Locate a .shp file recursively inside a directory.

    Args:
        directory: Root directory to search.

    Returns:
        Full path to the first .shp file found, or None if not found.
    """
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(".shp"):
                return os.path.join(root, file)

    return None


def load_zipped_shapefile(file_bytes):
    """Extract and load a zipped shapefile upload.

    Args:
        file_bytes: Raw bytes of the uploaded ZIP archive.

    Returns:
        GeoDataFrame loaded from the extracted shapefile.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = os.path.join(tmpdir, "upload.zip")

        with open(zip_path, "wb") as f:
            f.write(file_bytes)

        with zipfile.ZipFile(zip_path) as zip_ref:
            zip_ref.extractall(tmpdir)

        shp_file = find_shapefile(tmpdir)

        if shp_file is None:
            raise ValueError("Could not locate a .shp file inside zip.")

        return gpd.read_file(shp_file)


def load_shapefile_parts(contents, filenames):
    """Load shapefile components uploaded separately.

    Args:
        contents: List of base64-encoded file contents.
        filenames: List of uploaded filenames.

    Returns:
        GeoDataFrame loaded from the assembled shapefile.
    """
    extensions = {
        os.path.splitext(f)[1].lower().replace(".", "")
        for f in filenames
    }

    required = {"shp", "shx", "dbf"}

    if not required.issubset(extensions):
        raise ValueError(
            "Missing mandatory components. "
            "Upload .shp, .shx, and .dbf together."
        )

    with tempfile.TemporaryDirectory() as tmpdir:
        shp_path = None

        for content, filename in zip(contents, filenames):
            file_path = os.path.join(tmpdir, filename)

            with open(file_path, "wb") as f:
                f.write(decode_upload(content))

            if filename.lower().endswith(".shp"):
                shp_path = file_path

        return gpd.read_file(shp_path)


def normalize_crs(gdf):
    """Ensure the GeoDataFrame is in WGS84 (EPSG:4326).

    Args:
        gdf: Input GeoDataFrame.

    Returns:
        GeoDataFrame reprojected or assigned to EPSG:4326.
    """
    if gdf.crs and gdf.crs != "EPSG:4326":
        return gdf.to_crs(epsg=4326)

    if gdf.crs is None:
        return gdf.set_crs(epsg=4326)

    return gdf


def parse_uploaded_files(contents, filenames):
    """Parse uploaded file contents into a normalized GeoDataFrame.

    Supports single GeoJSON, zipped shapefile, or multiple shapefile parts.

    Args:
        contents: List of base64-encoded upload contents.
        filenames: List of upload filenames.

    Returns:
        Normalized GeoDataFrame in EPSG:4326.
    """
    if len(filenames) == 1:
        filename = filenames[0].lower()
        file_bytes = decode_upload(contents[0])

        if filename.endswith((".geojson", ".json")):
            gdf = load_geojson(file_bytes)

        elif filename.endswith(".zip"):
            gdf = load_zipped_shapefile(file_bytes)

        else:
            raise ValueError(
                f"Unsupported file extension: {filenames[0]}"
            )

    else:
        gdf = load_shapefile_parts(contents, filenames)

    return normalize_crs(gdf)


async def _query_ssurgo_inside_polygons(boundary_polygon):
    """Query SSURGO data for each polygon asynchronously.

    Args:
        boundary_polygon: GeoDataFrame containing boundary polygons.

    Returns:
        GeoDataFrame with merged SSURGO spatial and tabular data.
    """
    ssurgo_list = []
    for _, row in boundary_polygon.iterrows():
        response = await spatial_query(row.geometry, "mupolygon", "spatial")
        ssurgo_list.append(response.to_geodataframe())

    ssurgo_gdf = pd.concat(ssurgo_list)
    ssurgo_gdf["mukey"] = ssurgo_gdf["mukey"].astype(str)

    mukeys = ssurgo_gdf["mukey"].unique()
    mukeys_sql = ",".join([f"'{key}'" for key in mukeys])

    query_info = QUERIES["ssurgo"]
    query = query_info["query"].replace(query_info["replace"], mukeys_sql)
    ssurgo_tabular = query_sda(query)

    return ssurgo_gdf.merge(ssurgo_tabular, on="mukey", how="left")


def query_ssurgo_inside_polygons(boundary_polygon):
    """Run SSURGO queries from synchronous or asynchronous contexts.

    If called outside of an async loop, this function runs the async query
    to completion. If called from within an async loop, it returns a task.

    Args:
        boundary_polygon: GeoDataFrame containing boundary polygons.

    Returns:
        GeoDataFrame or asyncio.Task for the SSURGO query result.
    """
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(_query_ssurgo_inside_polygons(boundary_polygon))

    return asyncio.create_task(_query_ssurgo_inside_polygons(boundary_polygon))


def zoom_from_bounds(xmin, ymin, xmax, ymax):
    """Estimate a map zoom level from bounding box extents.

    Args:
        xmin: Minimum x-coordinate.
        ymin: Minimum y-coordinate.
        xmax: Maximum x-coordinate.
        ymax: Maximum y-coordinate.

    Returns:
        Integer zoom level between 1 and 20.
    """
    width = xmax - xmin
    height = ymax - ymin

    max_dim = max(width, height)

    if max_dim <= 0:
        return 15

    else:
        return max(1, min(20, math.log2(360 / max_dim)))