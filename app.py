from dash import Dash
from layout import layout
import dash_bootstrap_components as dbc

app = Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP
    ]
)

app.layout = layout

import callbacks

if __name__ == '__main__':
    app.run(debug=True)