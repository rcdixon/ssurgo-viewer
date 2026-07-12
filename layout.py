from dash import html, dcc
import dash_bootstrap_components as dbc

from utils.configLoader import MAP_LAYERS
from components.plots import empty_map

layout = html.Div(
    [
        # Header
        dbc.Navbar(
            dbc.Container(
                [
                    dbc.NavbarBrand(
                        "SSURGO Data Explorer",
                        className="fw-bold"
                    ),
                    # html.Div(
                    #     "GIS Data Visualization Platform",
                    #     className="text-light"
                    # ),
                ]
            ),
            color="dark",
            dark=True,
            className="mb-3"
        ),

        # Main application
        dbc.Container(
            [
                dbc.Row(
                    [
                        # Sidebar
                        dbc.Col(
                            [
                                dbc.Card(
                                    dbc.CardBody(
                                        [
                                            html.H5(
                                                "Upload Dataset",
                                                className="fw-bold"
                                            ),
                                            dcc.Upload(
                                                id="upload-data",
                                                children=html.Div(
                                                    [
                                                        html.Div(
                                                            "📂",
                                                            className="upload-icon"
                                                        ),
                                                        html.Div(
                                                            [
                                                                "Drop files or ",
                                                                html.Span(
                                                                    "browse",
                                                                    className="upload-link"
                                                                )
                                                            ]
                                                        ),
                                                        html.Small(
                                                            "GeoJSON, ZIP, or shapefile components",
                                                            className="text-muted"
                                                        )
                                                    ],
                                                    className="text-center"
                                                ),
                                                multiple=True,
                                                className=(
                                                    "upload-box "
                                                    "d-flex "
                                                    "align-items-center "
                                                    "justify-content-center"
                                                )
                                            ),
                                            html.Div(
                                                id="upload-status-message",
                                                className="status-message"
                                            ),
                                        ]
                                    ),
                                    className="mb-3"
                                ),
                                # Store shapefile upload
                                dcc.Store(
                                    id="shapefile-upload",
                                    storage_type="memory"
                                ),
                                dbc.Card(
                                    dbc.CardBody(
                                        [
                                            html.H5(
                                                "Filter Polygons By...",
                                                className="fw-bold"
                                            ),
                                            dcc.Dropdown(
                                                id="polygon-filter-column",
                                                placeholder="Select field to filter on"
                                            ),
                                            dcc.Dropdown(
                                                id="polygon-filter-values",
                                                multi=True,
                                                placeholder="Select polygons to view"
                                            ),
                                            dcc.Store(
                                                id="polygon-selected-indices",
                                                storage_type="memory"
                                            ),
                                            dcc.Store(
                                                id="boundary-gdf",
                                                storage_type="memory"
                                            ),
                                            dcc.Store(
                                                id="ssurgo-gdf",
                                                storage_type="memory" # I'M HERE: FIXING CIRCULAR SSURGO SELECTION
                                            )
                                        ]
                                    )
                                ),
                                dbc.Card(
                                    dbc.CardBody(
                                        [
                                            html.H5(
                                                "Select Soil Characteristic",
                                                className="fw-bold"
                                            ),
                                            dcc.Dropdown(
                                                id="soil-characteristic-dropdown",
                                                placeholder=""
                                            ),
                                        ]
                                    )
                                ),
                            ],
                            width=3,
                            className="sidebar"
                        ),
                        # Map panel
                        dbc.Col(
                            [
                                dbc.Card(
                                    dbc.CardBody(
                                        [
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        html.H5(
                                                            "Map View",
                                                            className="fw-bold mb-0"
                                                        ),
                                                        width="auto",
                                                    ),
                                                    dbc.Col(
                                                        dcc.Dropdown(
                                                            id="map_layer",
                                                            options=[
                                                                {
                                                                    "label": layer,
                                                                    "value": layer
                                                                }
                                                                for layer in MAP_LAYERS.keys()
                                                            ],
                                                            value=list(MAP_LAYERS.keys())[0],
                                                            clearable=False,
                                                        ),
                                                        width=4,
                                                    ),
                                                ],
                                                justify="between",
                                                align="center",
                                                className="mb-3",
                                            ),
                                            dcc.Graph(
                                                id="output-data-graph",
                                                figure=empty_map(),
                                                style={"height": "calc(100vh - 170px)"},
                                                config={"displayModeBar": True},
                                            )
                                        ]
                                    ),
                                    className="map-card",
                                )
                            ],
                            width=9,
                        )
                    ],
                    className="g-3"
                )
            ],
            fluid=True,
            className="px-4"
        )
    ]
)