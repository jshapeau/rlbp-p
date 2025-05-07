# app.py
import dash
from dash import html, Dash
import dash_bootstrap_components as dbc
from components.layout import create_footer, create_navbar_section
from config.theme import COLORS
from callbacks.scenario import register_scenario_callbacks
from callbacks.collapse_callbacks import (
    register_collapse_callbacks,
    register_legend_callbacks,
    register_slider_callbacks,
)
from callbacks.chart import register_bison_chart_callbacks

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], use_pages=True)
server = app.server


@app.callback(
    dash.Output("navbar-collapse", "is_open"),
    [dash.Input("navbar-toggler", "n_clicks")],
    [dash.State("navbar-collapse", "is_open")],
)
def toggle_navbar_collapse(n, is_open):
    if n:
        return not is_open
    return is_open


app.layout = html.Div(
    [
        html.Div(create_navbar_section()),
        dash.page_container,
        create_footer(),
    ],
    style={
        "backgroundColor": COLORS["light"],
        "minHeight": "100vh",
        "margin": 0,
        "display": "flex",
        "flexDirection": "column",
    },
)

register_scenario_callbacks(app)
register_collapse_callbacks(app)
register_legend_callbacks(app)
register_slider_callbacks(app)
register_bison_chart_callbacks(app)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8050)
# # if __name__ == "__main__":
# #     app.run(debug=True)
