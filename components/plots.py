import plotly.graph_objects as go
from components.data_processing import zoom_from_bounds
import numpy as np

def add_boundary_polygon(fig, poly, color="black"):
    """Add a boundary polygon and any interior holes to a Plotly figure.

    Args:
        fig: A Plotly Figure object to which the polygon traces will be added.
        poly: A Shapely Polygon geometry representing the boundary.
        color: Line color for the boundary and interior edges.
    """
    x, y = poly.exterior.xy
    fig.add_trace(
        go.Scattermap(
            lon=list(x),
            lat=list(y),
            mode="lines",
            line=dict(color=color, width=2),
            hoverinfo="skip",
            showlegend=False,
        )
    )

    for interior in poly.interiors:
        x, y = interior.xy
        fig.add_trace(
            go.Scattermap(
                lon=list(x),
                lat=list(y),
                mode="lines",
                line=dict(color=color, width=2, dash="dot"),  # optional styling
                hoverinfo="skip",
                showlegend=False,
            )
        )

def add_ssurgo_polygon(fig, poly, color_id):
    """Add a SSURGO polygon layer to a Plotly figure as a choropleth map.

    Args:
        fig: A Plotly Figure object to which the choropleth will be added.
        poly: A GeoDataFrame containing SSURGO polygon geometries and attributes.
        color_id: The column name in `poly` to use for fill coloring.

    Returns:
        The updated Plotly Figure object.
    """
    poly['id'] = poly.index.astype(str)
    categories = poly[color_id].astype("category")
    poly["_color"] = categories.cat.codes
    cats = categories.cat.categories

    fig.add_trace(
        go.Choroplethmap(
            geojson=poly.__geo_interface__,
            locations=poly["id"],
            featureidkey="properties.id",
            z=poly["_color"],
            colorscale="Viridis",
            customdata=np.column_stack([
                poly["mukey"],
                poly[color_id]
            ]),
            hovertemplate=(
                "MUKEY: %{customdata[0]}<br>"
                "<extra></extra>"
            ),
            colorbar=dict(
                title="Legend Title",
                tickvals=list(range(len(cats))),
                ticktext=list(cats),
            )
        )
    )

    return fig

def interactive_ssurgo_map(boundary_gdf, ssurgo_gdf, basemap_type, soil_characteristic):
    """Build an interactive SSURGO map with boundary and soil polygon layers.

    Args:
        boundary_gdf: GeoDataFrame containing the boundary polygon(s).
        ssurgo_gdf: GeoDataFrame containing SSURGO soil polygons.
        basemap_type: Base map layer specification for Plotly.
        soil_characteristic: Column name in `ssurgo_gdf` used for choropleth coloring.

    Returns:
        A Plotly Figure configured for interactive display.
    """
    fig = go.Figure()

    for geom in boundary_gdf.geometry:
        if geom.geom_type == "Polygon":
            add_boundary_polygon(fig, geom)

        elif geom.geom_type == "MultiPolygon":
            for poly in geom.geoms:
                add_boundary_polygon(fig, poly)

    add_ssurgo_polygon(fig, ssurgo_gdf, soil_characteristic)

    xmin, ymin, xmax, ymax = boundary_gdf.total_bounds

    fig.update_layout(
        map_style="white-bg", 
        map_layers=[basemap_type],
        map_center={
            "lon": (xmin + xmax) / 2,
            "lat": (ymin + ymax) / 2,
        },
        map_zoom=zoom_from_bounds(xmin, ymin, xmax, ymax),
        margin=dict(l=1, r=1, t=1, b=1),
    )

    return fig

def empty_map():
    """Create a fallback empty Plotly figure when no polygons are available.

    Returns:
        A Plotly Figure containing a centered annotation.
    """
    fig = go.Figure()

    fig.update_layout(
        annotations=[
            dict(
                text="No polygons selected",
                x=0.5,
                y=0.5,
                xref="paper",
                yref="paper",
                showarrow=False,
                font=dict(size=20)
            )
        ],
        xaxis_visible=False,
        yaxis_visible=False,
    )

    return fig