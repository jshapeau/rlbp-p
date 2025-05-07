from dash import html, dcc
import dash_bootstrap_components as dbc
from config.theme import (
    COLORS,
    COMPONENT_STYLES,
    SPACING,
    LAND_COVER_COLORS,
    get_land_cover_style,
)
from components.collapsible_card import create_collapsible_card
from data.constants import SLIDER_MAX_VALUES


def create_total_area_display(total_area, context_id="default"):
    display_id = f"total-area-display-{context_id}"

    return dbc.Row(
        [
            dbc.Col(
                [
                    html.H5("Total Area:", className="d-inline me-2"),
                    html.H5(
                        id=display_id,
                        children=f"{total_area:.2f} km²",
                        className="d-inline",
                    ),
                ],
                className="mb-3",
            ),
        ]
    )


def create_maximum_bison_display(total_bison, context_id="default"):
    display_id = f"total-bison-display-{context_id}"

    return dbc.Row(
        [
            dbc.Col(
                [
                    html.H5(
                        "Bison Supported:",
                        className="d-inline me-2",
                    ),
                    html.H5(
                        id=display_id,
                        children=f"{total_bison:.0f}",
                        className="d-inline",
                    ),
                ]
            ),
        ]
    )


def create_stats_display(total_area, total_bison):
    return html.Div(
        [
            create_total_area_display(total_area, "table"),
            create_maximum_bison_display(total_bison, "table"),
        ],
        className="py-2",
    )


def create_model_selection_tooltop():
    return dbc.Tooltip(
        [
            html.Div(
                [
                    "Choose between different models for calculating bison capacity.",
                    html.Br(),
                    html.Br(),
                    html.B("Nutritional Maximum"),
                    ": Carrying capacity of each land cover type is determined by the theoretical nutritional yield of each land cover type.",
                    html.Br(),
                    html.Br(),
                    html.B("Behaviour Restricted"),
                    ": Carrying capacity of each land cover type is determined by empirical experimental values.",
                ],
                style={"textAlign": "left"},
            )
        ],
        target="model-tooltip-target",
        placement="right",
        **COMPONENT_STYLES["tooltip"],
    )


def create_model_selection():
    return dbc.Row(
        [
            dbc.Col(
                [
                    dbc.Label(
                        [
                            "Model Selection",
                            dbc.Badge(
                                "?",
                                id="model-tooltip-target",
                                color=COLORS["secondary"],
                                className="ms-2 rounded-circle",
                                style={"cursor": "pointer"},
                            ),
                        ],
                        className="mb-2",
                    ),
                    create_model_selection_tooltop(),
                    dbc.Select(
                        id="model-dropdown",
                        options=[
                            {
                                "label": "Nutritional Maximum",
                                "value": "Nutritional Maximum",
                            },
                            {
                                "label": "Behaviour Restricted",
                                "value": "Behaviour Restricted",
                            },
                        ],
                        value="Nutritional Maximum",
                        **COMPONENT_STYLES["dropdown"],
                    ),
                ]
            )
        ],
        className="mb-4",
    )


def create_percentages_toggle_tooltop():
    return dbc.Tooltip(
        [
            html.Div(
                [
                    html.B("Disabled"),
                    ": sliders will directly affect the total amount in squared kilometers of the selected land cover type.",
                    html.Br(),
                    html.Br(),
                    html.B("Enabled"),
                    ": sliders will affect the percentage of land cover of each type, holding the total area constant.",
                ],
                style={"textAlign": "left"},
            )
        ],
        target="percentage-tooltip-target",
        placement="right",
        **COMPONENT_STYLES["tooltip"],
    )


def create_use_percentages_toggle():
    return dbc.Row(
        [
            dbc.Col(
                [
                    dbc.Label(
                        [
                            "Use Percentages",
                            dbc.Badge(
                                "?",
                                id="percentage-tooltip-target",
                                color=COLORS["secondary"],
                                className="ms-2 rounded-circle",
                                style={"cursor": "pointer"},
                            ),
                        ],
                        className="d-inline-block me-3",
                    ),
                    dbc.Switch(
                        id="proportional-checkbox",
                        value=True,
                        className="custom-switch d-inline-block",
                    ),
                    create_percentages_toggle_tooltop(),
                ]
            )
        ]
    )


def create_show_chart_trend_toggle():
    return dbc.Row(
        [
            dbc.Col(
                [
                    dbc.Label(
                        [
                            "View Chart Trend",
                        ],
                        className="d-inline-block me-3",
                    ),
                    dbc.Switch(
                        id="show-trend-line",
                        value=False,
                        className="custom-switch d-inline-block",
                    ),
                    create_percentages_toggle_tooltop(),
                ]
            )
        ],
        className="mb-3",
    )


def create_settings_panel():
    return html.Div(
        [
            create_show_chart_trend_toggle(),
            create_model_selection(),
            create_use_percentages_toggle(),
        ],
        className="py-2",
    )


def create_slider_marks(max_val_major=None, max_val_minor=None):
    if max_val_major is None:
        max_val_major = SLIDER_MAX_VALUES["major_sliders"]
    if max_val_minor is None:
        max_val_minor = SLIDER_MAX_VALUES["minor_sliders"]

    steps_major = 0.5
    steps_minor = 0.5

    def create_marks(max_val):
        return {
            i: {"label": str(i), "style": {"color": COLORS["secondary"]}}
            for i in [
                0,
                max_val // 4,
                max_val // 2,
                3 * max_val // 4,
                max_val,
            ]
        }

    return (
        create_marks(max_val_major),
        create_marks(max_val_minor),
        max_val_major,
        max_val_minor,
        steps_major,
        steps_minor,
    )


def create_minor_slider(row, marks, max_val, step, color_class):
    style = get_land_cover_style(row["Land_Cover_Major_Class"], is_minor=True)
    initial_value = row["Area_percentage"]

    return html.Div(
        [
            html.Label(
                row["Land_Cover_Minor_Class"].replace("_", " "),
                className="minor-slider-label mb-2",
                style={"fontSize": "0.9em", "paddingBottom": SPACING["sm"]},
            ),
            dcc.Slider(
                id={
                    "type": "slider",
                    "index": f"{row['Land_Cover_Major_Class']}-{row['Land_Cover_Minor_Class']}",
                },
                min=0,
                max=max_val,
                step=step,
                marks=marks,
                value=initial_value,  # Changed from row["Area_km2"]
                tooltip={"placement": "right", "always_visible": True},
                className=f"slider minor-slider {color_class}-minor-slider",
            ),
        ],
        className=f"{color_class}-minor-container minor-slider-container",
        style=style,
    )


def create_major_slider(
    major_class,
    major_class_percent,
    marks_major,
    max_val_major,
    steps_major,
    color_class,
):
    style = get_land_cover_style(major_class)

    return html.Div(
        [
            html.Div(
                [
                    html.Label(
                        f"Total {major_class}",
                        className="fw-bold",
                        style={"marginLeft": "10px"},
                    ),
                    html.Button(
                        "More Detail",
                        id={"type": "collapse-button", "index": major_class},
                        **COMPONENT_STYLES["collapse_toggle"],
                    ),
                ],
                style={
                    "display": "flex",
                    "justifyContent": "space-between",
                    "alignItems": "center",
                    "marginBottom": "15px",
                },
            ),
            dcc.Slider(
                id={"type": "major-slider", "index": major_class},
                min=0,
                max=max_val_major,
                step=steps_major,
                marks=marks_major,
                value=major_class_percent,
                tooltip={"placement": "right", "always_visible": True},
                className=f"slider major-slider {color_class}-slider",
            ),
        ],
        className=f"{color_class}-container major-slider-container",
        style=style,
    )


def create_minor_sliders_group(
    df, major_class, marks_minor, max_val_minor, steps_minor, color_class
):
    """Creates a group of minor sliders for a major land cover class."""
    return html.Div(
        [
            create_minor_slider(
                row, marks_minor, max_val_minor, steps_minor, color_class
            )
            for _, row in df[df["Land_Cover_Major_Class"] == major_class].iterrows()
        ],
        className="minor-sliders-group",
    )


def create_slider_group(df, major_class, total_area):
    """Creates a slider group for a major land cover class."""
    major_class_percent = df[df["Land_Cover_Major_Class"] == major_class][
        "Area_percentage"
    ].sum()

    marks_major, marks_minor, max_val_major, max_val_minor, steps_major, steps_minor = (
        create_slider_marks(100, 100)
    )

    color_class = major_class.lower().replace(" ", "-")

    return html.Div(
        [
            create_major_slider(
                major_class,
                major_class_percent,
                marks_major,
                max_val_major,
                steps_major,
                color_class,
            ),
            dbc.Collapse(
                create_minor_sliders_group(
                    df,
                    major_class,
                    marks_minor,
                    max_val_minor,
                    steps_minor,
                    color_class,
                ),
                id={"type": "collapse-content", "index": major_class},
                is_open=False,
            ),
        ],
        className="slider-group mb-3",
    )


def create_slider_groups(df, total_area):
    return html.Div(
        [
            html.Div(
                [
                    create_slider_group(df, major_class, total_area)
                    for major_class in LAND_COVER_COLORS
                ],
                className="slider-groups mt-4",
            ),
        ]
    )


def create_instructions_display():
    return html.Div(
        [
            html.P(
                "Compare and explore estimated changes to Ronald Lake wood bison carrying capacity through simplified habitat change scenarios. This application allows users to:",
                className="",
            ),
            html.Ul(
                [
                    html.Li(
                        "Select between two different carrying capacity models: nutritional maximum vs. behaviour restricted.",
                        className="",
                    ),
                    html.Li(
                        "Adjust the area of each land cover type either proportionately (percentage of existing winter range) or increase/decrease land cover types beyond the predetermined range.",
                        className="",
                    ),
                    html.Li(
                        "Create your own scenarios or load preset scenarios of habitat loss, enhancement, and change.",
                        className="",
                    ),
                ]
            ),
        ],
        className="py-2",
    )


def create_controls_section(df, total_area, total_bison):
    """Creates the control panel section with consistent styling."""
    return html.Div(
        [
            create_collapsible_card(
                title="Instructions",
                content=create_instructions_display(),
                card_id="instructions-display",
                is_open=False,
            ),
            create_collapsible_card(
                title="Summary Statistics",
                content=create_stats_display(total_area, total_bison),
                card_id="stats-display",
                is_open=True,
            ),
            create_collapsible_card(
                title="Area Adjustment (%)",
                content=create_slider_groups(df, total_area),
                card_id="area-adjustment",
                is_open=True,
            ),
            # html.Div(
            #     create_slider_groups(df, total_area),
            #     style=COMPONENT_STYLES["container"]["style"],
            # ),
            create_collapsible_card(
                title="Settings",
                content=create_settings_panel(),
                card_id="settings-panel",
                is_open=True,
            ),
        ],
    )
