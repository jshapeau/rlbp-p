from dash import html, callback, Input, Output
from data.constants import SCENARIOS

PAGE_NAME = "spatial"


@callback(
    [
        Output("base-layer", "url"),
        Output("layer-overlay", "url"),
        Output("layer-overlay", "opacity"),
        Output(f"preset-scenario-description-{PAGE_NAME}", "children"),
        Output(f"total-bison-display-{PAGE_NAME}", "children"),
    ],
    [
        Input("basemap-selection", "value"),
        Input("layer-scenario-dropdown", "value"),
        Input("opacity-slider", "value"),
        Input("model-dropdown", "value"),
    ],
)
def update_map(basemap, selected_layer, opacity, model):
    """Update map visuals based on selected basemap and layer view."""
    basemap_urls = {
        "carto": "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
        "satellite": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        "terrain": "https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png",
    }
    url = basemap_urls.get(basemap, basemap_urls["carto"])

    if not selected_layer or selected_layer not in SCENARIOS:
        selected_layer = list(SCENARIOS.keys())[0]

    scenario_data = SCENARIOS[selected_layer]
    layer_path = scenario_data["path"]
    description = scenario_data.get("description", "")

    lines = [description] if isinstance(description, str) else description
    formatted_description = html.Div(
        [
            html.Strong(f"Scenario {selected_layer}"),
            html.Ul(
                [html.Li(line) for line in lines],
                style={
                    "listStyleType": "disc",
                    "marginLeft": "20px",
                    "marginTop": "10px",
                    "fontSize": "12px",
                },
            ),
        ],
        style={"fontSize": "12px"},
    )

    bison_value = (
        scenario_data.get("nutritional_maximum", 0)
        if model == "Nutritional Maximum"
        else scenario_data.get("behaviour_restricted", 0)
    )

    return (
        url,
        layer_path,
        opacity,
        formatted_description,
        f"{bison_value}",
    )
