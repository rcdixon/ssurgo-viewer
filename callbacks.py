from dash import callback, Input, Output, State, dash, exceptions
from io import StringIO
import geopandas as gpd
import asyncio
from soildb import spatial_query
import pandas as pd

from utils.configLoader import MAP_LAYERS
from components.data_processing import parse_uploaded_files, query_ssurgo_inside_polygons
from components.plots import interactive_ssurgo_map, empty_map

@callback(
    Output("shapefile-upload", "data"),
    Output("upload-status-message", "children"),
    Output("polygon-filter-column", "options"),
    Output("polygon-filter-column", "value"),
    Input("upload-data", "contents"),
    State("upload-data", "filename"),
    prevent_initial_call=True,
)
def store_uploaded_data(list_of_contents, list_of_filenames):
    """Parse uploaded spatial files and expose their columns as polygon filter options."""
    if not list_of_contents:
        raise exceptions.PreventUpdate

    try:
        gdf = parse_uploaded_files(
            list_of_contents,
            list_of_filenames
        )

        source_label = ", ".join(list_of_filenames)
        
        filter_cols = [c for c in gdf.columns if c != gdf.geometry.name]
        options = [{"label": c, "value": c} for c in filter_cols]

        return (
            gdf.to_json(),
            f"Success! Read data from: {source_label}",
            options,
            options[0]["label"]
        )

    except Exception as e:
        return (
            dash.no_update,
            f"Error processing file: {str(e)}",
            dash.no_update,
            dash.no_update,
        )

@callback(
    Output("polygon-filter-values", "options"),
    Output("polygon-filter-values", "value"),
    Output("polygon-selected-indices", "data"),
    Input("polygon-filter-column", "value"),
    State("shapefile-upload", "data"),
    State("polygon-selected-indices", "data"),
)
def update_filter_values(field, stored_data, selected_indices):
    """Populate the available values for the selected polygon filter column."""
    if not stored_data or not field:
        raise exceptions.PreventUpdate
    
    gdf = gpd.read_file(StringIO(stored_data))

    values = sorted(gdf[field].dropna().unique())
    options = [{"label": str(v), "value": v} for v in values]

    if selected_indices is None:
        selected_indices = [0]
        return options, [values[0]], selected_indices
    
    else:
        # Preserve selected row indices when changing fields
        selected_values = [
            gdf.iloc[i][field]
            for i in selected_indices
            if i < len(gdf) and field in gdf.columns
        ]
        return options, selected_values, selected_indices

@callback(
    Output("polygon-selected-indices", "data", allow_duplicate=True),
    Input("polygon-filter-values", "value"),
    State("polygon-filter-column", "value"),
    State("shapefile-upload", "data"),
    prevent_initial_call=True,
)
def update_selected_indices(selected_values, field, stored_data):
    """Return the indices of polygons whose selected filter values match the current choice."""
    if not stored_data or not field or not selected_values:
        return []

    gdf = gpd.read_file(StringIO(stored_data))

    indices = gdf[
        gdf[field].isin(selected_values)
    ].index.tolist()

    return indices
    
@callback(
    Output("output-data-graph", "figure"),
    Input("boundary-gdf", "data"),
    Input("ssurgo-gdf", "data"),
    Input("map_layer", "value"),
    Input("soil-characteristic-dropdown", "value"),
    prevent_initial_call=True
)
async def update_graph_from_state(boundary_json, ssurgo_json, basemap_name, soil_characteristic):
    """Render the map visualization from the current boundary, ssurgo polygon, and map settings."""
    if not boundary_json:
        raise exceptions.PreventUpdate

    boundary_gdf = gpd.read_file(StringIO(boundary_json))
    ssurgo_gdf = gpd.read_file(StringIO(ssurgo_json))

    if boundary_gdf.empty:
        return empty_map(), None
    
    else:
        return interactive_ssurgo_map(boundary_gdf, ssurgo_gdf, MAP_LAYERS[basemap_name], soil_characteristic)
    
@callback(
    Output("soil-characteristic-dropdown", "options"),
    Output("soil-characteristic-dropdown", "value"),
    Input("ssurgo-gdf", "data")
)
def update_soil_options(stored_data):
    """Populate the soil-characteristic dropdown from the columns available in SSURGO data."""
    if not stored_data:
        raise exceptions.PreventUpdate
    
    gdf = gpd.read_file(StringIO(stored_data))

    filter_cols = [c for c in gdf.columns if c != gdf.geometry.name]
    options = [{"label": c, "value": c} for c in filter_cols]

    return options, options[0]["label"]

@callback(
    Output("boundary-gdf", "data"),
    Input("polygon-filter-column", "value"),
    Input("polygon-filter-values", "value"),
    State("shapefile-upload", "data")
)
def filter_boundary_polygons(filter_column, filter_values, stored_data):
    """Filter the uploaded boundary polygons to the currently selected values."""
    if not stored_data:
        raise exceptions.PreventUpdate
    
    boundary_gdf = gpd.read_file(StringIO(stored_data))
    boundary_gdf = boundary_gdf[boundary_gdf[filter_column].isin(filter_values)]

    return boundary_gdf.to_json()

@callback(
    Output("ssurgo-gdf", "data"),
    Input("boundary-gdf", "data")
)
async def retrieve_ssurgo_in_boundary(boundary_json):
    """Query SSURGO polygons that intersect the selected boundary and clip them to that boundary."""
    boundary_gdf = gpd.read_file(StringIO(boundary_json))

    ssurgo_gdf = await query_ssurgo_inside_polygons(boundary_gdf)
    ssurgo_gdf = gpd.clip(ssurgo_gdf, boundary_gdf)

    return ssurgo_gdf.to_json()