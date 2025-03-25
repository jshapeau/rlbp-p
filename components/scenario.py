from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
import dash.dash_table.FormatTemplate as FormatTemplate

from config.theme import COLORS, COMPONENT_STYLES
from data.constants import SCENARIOS, create_initial_dataframe
from callbacks.scenario import update_scenarios_data
from components.collapsible_card import create_collapsible_card


def create_scenario_section():
    """Creates the scenario management section with consistent styling."""
    scenario_storage, scenario_data = update_scenarios_data(
        [], [], create_initial_dataframe()
    )
    scenario_storage["description"] = "Present Day"
    scenario_data["description"] = "Present Day"

    return html.Div(
        [
            dcc.Store(
                id="scenarios-storage", storage_type="memory", data=[scenario_data]
            ),
            # Main Container
            html.Div(
                [
                    create_collapsible_card(
                        title="Saved Scenarios",
                        content=create_saved_scenarios_component(scenario_storage),
                        card_id="saved-scenarios",
                        is_open=True,
                    ),
                    create_collapsible_card(
                        title="Create Scenarios",
                        content=create_create_scenarios_component(),
                        card_id="create-scenarios",
                        is_open=False,
                    ),
                ],
                style={"maxWidth": "100%"},
            ),
        ]
    )


def create_create_scenarios_component():
    """Creates the content for the Create Scenarios card."""
    return html.Div(
        [
            create_preset_scenario_component(),
            create_divider_with_text_component("or"),
            create_create_custom_scenario_component(),
        ]
    )


def create_scenario_dropdown_component(
    id_prefix="preset", placeholder="Select a preset scenario...", default_index=None
):
    """
    Creates a dropdown component for preset scenarios.

    Parameters:
    id_prefix (str): Prefix for the dropdown ID to make it unique
    placeholder (str): Placeholder text for the dropdown
    default_index (int, optional): Index of the default selected option. If None, no default is selected.

    Returns:
    dash component: A dbc.Select dropdown for scenarios
    """
    scenario_keys = list(SCENARIOS.keys())

    default_value = None
    if default_index is not None and 0 <= default_index < len(scenario_keys):
        default_value = scenario_keys[default_index]

    return dbc.Select(
        id=f"{id_prefix}-scenario-dropdown",
        options=[
            {
                "label": v,
                "value": v,
            }
            for v in scenario_keys
        ],
        placeholder=placeholder,
        value=default_value,
        className=f"{COMPONENT_STYLES['dropdown']['className']} me-2",
        style={
            **COMPONENT_STYLES["dropdown"]["style"],
            "margin-bottom": "0px",
        },
    )


def create_preset_scenario_component():
    """Creates the preset scenarios section."""
    return html.Div(
        [
            html.Div(
                [
                    html.Label(
                        "From Preset:",
                        style={
                            "fontWeight": "600",
                        },
                    ),
                    dbc.Badge(
                        "?",
                        id="preset-help",
                        color=COLORS["secondary"],
                        className="ms-2 rounded-circle",
                        style={
                            "cursor": "pointer",
                        },
                    ),
                    dbc.Tooltip(
                        "Creating a preset scenario will apply the transformations described by the preset to the current data.",
                        target="preset-help",
                        placement="right",
                        **COMPONENT_STYLES["tooltip"],
                    ),
                ],
                className="d-flex align-items-center mb-2",
            ),
            html.Div(
                [
                    create_scenario_dropdown_component(
                        id_prefix="preset", placeholder="Select a preset scenario..."
                    ),
                    html.Button(
                        "Create",
                        id="create-preset-scenario",
                        style={
                            **COMPONENT_STYLES["button"]["style"],
                            "backgroundColor": COLORS["secondary"],
                            "color": COLORS["white"],
                            "height": "38px",
                            "alignSelf": "center",
                        },
                        className=COMPONENT_STYLES["button"]["className"],
                    ),
                ],
                className="d-flex align-items-center",
                style={
                    "display": "flex",
                    "alignItems": "center",
                    "marginBottom": "15px",
                    "gap": "10px",
                },
            ),
            create_scenario_description_box("default"),
        ]
    )


def create_scenario_description_box(
    context_id="default", custom_styles=None, custom_class=None
):
    display_id = f"preset-scenario-description-{context_id}"

    default_styles = {
        "padding": "10px",
        "backgroundColor": COLORS["light"],
        "borderRadius": "6px",
        "minHeight": "40px",
        "display": "none",
    }

    if custom_styles:
        styles = {**default_styles, **custom_styles}
    else:
        styles = default_styles

    class_name = "scenario-description-box"
    if custom_class:
        class_name += f" {custom_class}"

    return html.Div(
        id=display_id,
        style=styles,
        className=class_name,
    )


def create_create_custom_scenario_component():
    """Creates the custom scenario section."""
    return html.Div(
        [
            html.Div(
                [
                    html.Label(
                        "Create Custom:",
                        style={
                            "fontWeight": "600",
                        },
                    ),
                    dbc.Badge(
                        "?",
                        id="custom-help",
                        color=COLORS["secondary"],
                        className="ms-2 rounded-circle",
                        style={"cursor": "pointer"},
                    ),
                    dbc.Tooltip(
                        "Save the current data as a scenario. Saved data can be loaded under Saved Scenarios.",
                        target="custom-help",
                        placement="right",
                        **COMPONENT_STYLES["tooltip"],
                    ),
                ],
                className="d-flex align-items-center mb-2",
            ),
            html.Div(
                [
                    dbc.Input(
                        id="scenario-description",
                        placeholder="Enter a brief scenario name",
                        className="me-2",
                        style=COMPONENT_STYLES["dropdown"]["style"],
                    ),
                    html.Button(
                        "Create",
                        id="save-scenario-button",
                        style={
                            **COMPONENT_STYLES["button"]["style"],
                            "backgroundColor": COLORS["secondary"],
                            "color": COLORS["white"],
                        },
                        className=COMPONENT_STYLES["button"]["className"],
                    ),
                ],
                className="d-flex",
            ),
        ]
    )


def create_saved_scenarios_component(initial):
    """Creates the content for the Saved Scenarios card."""
    return html.Div(
        [
            create_saved_scenarios_table(initial),
            html.Div(
                [
                    html.Button(
                        "Load Selected",
                        id="load-scenario-button",
                        style={
                            **COMPONENT_STYLES["button"]["style"],
                            "backgroundColor": COLORS["secondary"],
                            "color": COLORS["white"],
                            "marginRight": "10px",
                        },
                        className=COMPONENT_STYLES["button"]["className"],
                    ),
                    html.Button(
                        "Delete Last",
                        id="delete-last-scenario-button",
                        style={
                            **COMPONENT_STYLES["button"]["style"],
                            "backgroundColor": COLORS["secondary"],
                            "color": COLORS["white"],
                        },
                        className=COMPONENT_STYLES["button"]["className"],
                    ),
                ],
                className="d-flex justify-content-end mt-3",
            ),
        ]
    )


def create_divider_with_text_component(text):
    """Creates a horizontal divider with text in the middle."""
    return html.Div(
        [
            html.Hr(style={"flex": 1}),
            html.Span(
                text,
                style={
                    "margin": "0 15px",
                    "color": "#666",
                    "backgroundColor": "white",
                    "padding": "0 10px",
                },
            ),
            html.Hr(style={"flex": 1}),
        ],
        style={
            "display": "flex",
            "alignItems": "center",
            "margin": "20px 0",
        },
    )


def create_saved_scenarios_table(initial):
    """Creates the scenarios table with consistent styling."""
    return dash_table.DataTable(
        id="scenarios-table",
        columns=[
            {"name": "Description", "id": "description"},
            {
                "name": "Total Area (km²)",
                "id": "total_area",
                "type": "numeric",
                "format": {"specifier": ".2f"},
            },
            {
                "name": "Max Bison Supported",
                "id": "total_bison",
                "type": "numeric",
                "format": {"specifier": ".0f"},
            },
            {
                "name": "% Change, Previous",
                "id": "change_from_previous",
                "type": "numeric",
                "format": FormatTemplate.percentage(1),
            },
            {
                "name": "% Change, First",
                "id": "change_from_first",
                "type": "numeric",
                "format": FormatTemplate.percentage(1),
            },
        ],
        data=[initial],
        row_selectable="single",
        style_table=COMPONENT_STYLES["table"]["style_table"],
        style_cell=COMPONENT_STYLES["table"]["style_cell"],
        style_header=COMPONENT_STYLES["table"]["style_header"],
        style_data=COMPONENT_STYLES["table"]["style_data"],
        style_data_conditional=[
            {
                "if": {"state": "selected"},
                "backgroundColor": f"{COLORS['primary']}22",
                "border": f"1px solid {COLORS['primary']}",
            },
            {
                "if": {
                    "column_id": "change_from_previous",
                    "filter_query": "{change_from_previous} > 0.001",
                },
                "color": COLORS["success"],
            },
            {
                "if": {
                    "column_id": "change_from_previous",
                    "filter_query": "{change_from_previous} < -0.001",
                },
                "color": COLORS["danger"],
            },
            {
                "if": {
                    "column_id": "change_from_first",
                    "filter_query": "{change_from_first} > 0.001",
                },
                "color": COLORS["success"],
            },
            {
                "if": {
                    "column_id": "change_from_first",
                    "filter_query": "{change_from_first} < -0.001",
                },
                "color": COLORS["danger"],
            },
        ],
    )
