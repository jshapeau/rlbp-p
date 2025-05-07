import dash
from dash import html, dcc
import dash_leaflet as dl
import dash_bootstrap_components as dbc
import numpy as np
from config.theme import COLORS, COMPONENT_STYLES, RADIUS, SHADOWS, TYPOGRAPHY, SPACING
from components.collapsible_card import create_collapsible_card
from components.scenario import (
    create_scenario_dropdown_component,
    create_scenario_description_box,
)
from components.controls import (
    create_maximum_bison_display,
    create_model_selection,
)
from data.constants import SCENARIOS, SUBCATEGORIES, LEGEND_COLORS
from callbacks.spatial_view import *

PAGE_NAME = "spatial"
dash.register_page(__name__, path="/spatial")


def apply_offset_to_bounds(bounds, offset_lat=0, offset_lng=0):
    return [
        [bounds[0][0] + offset_lat, bounds[0][1] + offset_lng],
        [bounds[1][0] + offset_lat, bounds[1][1] + offset_lng],
    ]


def meters_to_degrees(meters, latitude):
    earth_radius = 6371000
    lat_rad = np.radians(latitude)
    lat_degrees = meters / 111000
    lng_degrees = meters / (111000 * np.cos(lat_rad))
    return lat_degrees, lng_degrees


ORIGINAL_BOUNDS = [
    [57.5335840830178, -112.14525139453504],
    [58.242577025645986, -111.34645500870555],
]

center_lat = (ORIGINAL_BOUNDS[0][0] + ORIGINAL_BOUNDS[1][0]) / 2
OFFSET_LAT, _ = meters_to_degrees(130, center_lat)

CORRECTED_BOUNDS = apply_offset_to_bounds(
    ORIGINAL_BOUNDS, offset_lat=-OFFSET_LAT, offset_lng=0
)

CENTER = [
    (CORRECTED_BOUNDS[0][0] + CORRECTED_BOUNDS[1][0]) / 2,
    (CORRECTED_BOUNDS[0][1] + CORRECTED_BOUNDS[1][1]) / 2,
]


def create_basemap_dropdown():
    return html.Div(
        [
            dbc.Label("Base Map", className="mb-2"),
            dbc.Select(
                id="basemap-selection",
                options=[
                    {"label": "Default", "value": "carto"},
                    {"label": "Satellite", "value": "satellite"},
                    {"label": "Terrain", "value": "terrain"},
                ],
                value="carto",
                **COMPONENT_STYLES["dropdown"],
            ),
        ],
        className="mb-3",
    )


def create_opacity_slider():
    return html.Div(
        [
            dbc.Label("Layer Opacity", className="mb-2"),
            dcc.Slider(
                id="opacity-slider",
                min=0,
                max=1,
                step=0.1,
                value=0.7,
                marks={
                    0: {"label": "0", "style": {"color": COLORS["secondary"]}},
                    0.2: {"label": "0.2", "style": {"color": COLORS["secondary"]}},
                    0.4: {"label": "0.4", "style": {"color": COLORS["secondary"]}},
                    0.6: {"label": "0.6", "style": {"color": COLORS["secondary"]}},
                    0.8: {"label": "0.8", "style": {"color": COLORS["secondary"]}},
                    1: {"label": "1.0", "style": {"color": COLORS["secondary"]}},
                },
                tooltip={"placement": "bottom", "always_visible": True},
                className="mb-3",
            ),
        ],
    )


def create_scenario_info():
    return html.Div(
        [
            create_scenario_description_box(
                PAGE_NAME,
                custom_styles={
                    "fontSize": "12px",
                    "marginTop": "10px",
                    "padding": "10px 5px 10px 10px",
                    "margin": "-15px 0px 10px 0px",
                    "display": "block",
                },
            ),
            create_model_selection(),
            html.Div(
                [
                    create_maximum_bison_display(0, context_id=PAGE_NAME),
                ],
                className="mb-3",
            ),
        ],
        className="py-2",
    )


def create_color_box(color, margin_left=0):
    return html.Div(
        style={
            "backgroundColor": f"rgb{color}",
            "minWidth": "28px",
            "width": "28px",
            "height": "24px",
            "display": "inline-block",
            "marginRight": "8px",
            "marginLeft": f"{margin_left}px",
            "border": "1px solid #ccc",
            "flexShrink": 0,
        }
    )


def create_subcategory_item(subcat):
    return html.Div(
        [
            create_color_box(subcat["color"], margin_left=10),
            html.Span(
                subcat["name"],
                style={
                    "fontSize": TYPOGRAPHY["size"]["xs"],
                    "overflow": "hidden",
                    "textOverflow": "ellipsis",
                    "whiteSpace": "nowrap",
                },
            ),
        ],
        style={
            "display": "flex",
            "alignItems": "center",
            "marginBottom": "4px",
            "width": "100%",
            "minWidth": 0,
        },
    )


def create_subcategories_list(category):
    subcategories = SUBCATEGORIES.get(category, [])

    return html.Div(
        [create_subcategory_item(subcat) for subcat in subcategories],
        style={"paddingLeft": "10px", "marginBottom": "10px"},
    )


def create_category_header(category, color, has_subcategories):
    category_id = f"category-{category.lower().replace(' ', '-')}"

    return html.Div(
        [
            create_color_box(color),
            html.Span(
                category,
                style={"fontSize": TYPOGRAPHY["size"]["sm"]},
            ),
            # Spacer to push the plus sign to the right
            html.Div(style={"flexGrow": 1}) if has_subcategories else None,
            # Plus sign at the right edge
            (
                html.Span(
                    "+",  # Simple text plus sign as a fallback
                    id=f"toggle-{category.lower().replace(' ', '-')}",
                    style={
                        "marginLeft": "8px",
                        "fontSize": "12px",
                        "fontWeight": "bold",
                        "display": "inline-block" if has_subcategories else "none",
                    },
                )
                if has_subcategories
                else None
            ),
        ],
        id=category_id,
        style={
            "display": "flex",
            "alignItems": "center",
            "marginBottom": "5px",
            "cursor": "pointer" if has_subcategories else "default",
            "padding": "4px",
            "borderRadius": RADIUS["sm"],
            "transition": "background-color 0.2s",
        },
        **({"n_clicks": 0} if has_subcategories else {}),
    )


def create_category_item(category, color):
    collapse_id = f"collapse-{category.lower().replace(' ', '-')}"
    has_subcategories = (
        category in SUBCATEGORIES and len(SUBCATEGORIES.get(category, [])) > 0
    )

    return html.Div(
        [
            create_category_header(category, color, has_subcategories),
            (
                dbc.Collapse(
                    create_subcategories_list(category),
                    id=collapse_id,
                    is_open=False,
                )
                if has_subcategories
                else None
            ),
        ]
    )


def create_land_cover_legend():
    legend_items = [
        create_category_item(category, color)
        for category, color in LEGEND_COLORS.items()
    ]

    return html.Div(
        legend_items,
        style={
            "backgroundColor": COLORS["white"],
            "padding": SPACING["md"],
            "borderRadius": RADIUS["md"],
            "boxShadow": SHADOWS["xs"],
            "maxWidth": "300px",
        },
    )


def create_map_controls():
    return html.Div(
        [
            html.Div(
                [
                    dbc.Label("Scenario Selection", className="mb-2"),
                    create_scenario_dropdown_component(
                        id_prefix="layer",
                        placeholder="Select a layer...",
                        default_index=0,
                    ),
                ],
                className="mb-3",
            ),
            create_basemap_dropdown(),
            create_opacity_slider(),
        ],
        className="py-2",
    )


def create_map_container():
    return html.Div(
        [
            dl.Map(
                id="map",
                center=CENTER,
                zoom=10,
                style={
                    "width": "100%",
                    "height": "70vh",
                    "borderRadius": RADIUS["md"],
                },
                children=[
                    dl.TileLayer(id="base-layer"),
                    dl.ImageOverlay(
                        id="layer-overlay",
                        url=SCENARIOS[list(SCENARIOS.keys())[0]]["path"],
                        bounds=CORRECTED_BOUNDS,
                        opacity=0.5,
                    ),
                    dl.ScaleControl(position="bottomleft"),
                ],
            ),
        ],
        className="shadow-sm",
    )


def create_spatial_sidebar():
    return dbc.Col(
        [
            create_collapsible_card(
                "Map Controls",
                create_map_controls(),
                "map-controls",
                is_open=True,
            ),
            create_collapsible_card(
                "Scenario Information",
                create_scenario_info(),
                "scenario-info",
                is_open=True,
            ),
            create_collapsible_card(
                "Legend",
                create_land_cover_legend(),
                "legend",
                is_open=True,
            ),
        ],
        xs=12,
        md=4,
        lg=3,
        className="order-2 order-md-1",
    )


def create_map_section():
    return dbc.Col(
        [
            create_map_container(),
            html.Div(id="coordinate-info", className="mt-2 text-muted"),
        ],
        xs=12,
        md=8,
        lg=9,
        className="order-1 order-md-2",
    )


layout = dbc.Container(
    [
        dbc.Row(
            [
                create_spatial_sidebar(),
                create_map_section(),
            ]
        ),
    ],
    fluid="md",
    className="px-4 py-4",
)
