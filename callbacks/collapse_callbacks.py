from dash import ClientsideFunction
from dash.dependencies import Input, Output, State, MATCH, ALL
from data.constants import SUBCATEGORIES, LEGEND_COLORS


def register_collapse_callbacks(app):
    """Register all collapsible card callbacks"""
    collapse_pairs = [
        ("instructions-display-collapse", "collapse-instructions-display"),
        ("stats-display-collapse", "collapse-stats-display"),
        ("settings-panel-collapse", "collapse-settings-panel"),
        ("create-scenarios-collapse", "collapse-create-scenarios"),
        ("saved-scenarios-collapse", "collapse-saved-scenarios"),
        ("data-table-collapse", "collapse-data-table"),
        ("map-controls-collapse", "collapse-map-controls"),
        ("scenario-info-collapse", "collapse-scenario-info"),
        ("legend-collapse", "collapse-legend"),
        ("bison-chart-collapse", "collapse-bison-chart"),
        ("area-adjustment-collapse", "collapse-area-adjustment"),
    ]

    for collapse_id, button_id in collapse_pairs:
        app.clientside_callback(
            ClientsideFunction(namespace="bison", function_name="toggleCardCollapse"),
            [
                Output(collapse_id, "is_open"),
                Output(button_id, "children"),
            ],
            Input(button_id, "n_clicks"),
            State(collapse_id, "is_open"),
            prevent_initial_call=True,
        )


def register_legend_callbacks(app):
    """Register callbacks for legend categories"""
    for category in LEGEND_COLORS.keys():
        if category in SUBCATEGORIES and SUBCATEGORIES.get(category, []):
            category_id = f"category-{category.lower().replace(' ', '-')}"
            collapse_id = f"collapse-{category.lower().replace(' ', '-')}"

            app.clientside_callback(
                ClientsideFunction(
                    namespace="bison", function_name="toggleLegendCollapse"
                ),
                Output(collapse_id, "is_open"),
                Input(category_id, "n_clicks"),
                State(collapse_id, "is_open"),
                prevent_initial_call=True,
            )


def register_slider_callbacks(app):
    """Register callbacks for major sliders"""
    app.clientside_callback(
        ClientsideFunction(namespace="bison", function_name="toggleSliderCollapse"),
        [
            Output({"type": "collapse-content", "index": MATCH}, "is_open"),
            Output({"type": "collapse-button", "index": MATCH}, "children"),
        ],
        Input({"type": "collapse-button", "index": MATCH}, "n_clicks"),
        State({"type": "collapse-content", "index": MATCH}, "is_open"),
        prevent_initial_call=True,
    )
