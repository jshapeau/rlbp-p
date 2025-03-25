"""
collapsible_card.py - Enhanced reusable collapsible card component
"""

from dash import html
import dash_bootstrap_components as dbc
from config.theme import COLORS, COMPONENT_STYLES


def create_collapsible_card(title, content, card_id, is_open=True, **card_props):
    """
    Creates a standardized card that can be collapsed/expanded.

    Args:
        title: Card title
        content: Card content (dash components)
        card_id: Unique ID for collapse functionality (no spaces or special chars)
        is_open: Whether card starts expanded or collapsed
        **card_props: Additional properties to pass to the Card component

    Returns:
        dbc.Card component with collapsible functionality
    """

    default_card_style = {
        "className": "mb-4 shadow-sm",
        "style": {
            "border": "none",
            "borderRadius": "8px",
        },
    }

    merged_props = {**default_card_style}
    if card_props:
        if "className" in card_props:
            merged_props["className"] = (
                f"{default_card_style['className']} {card_props.pop('className')}"
            )
        if "style" in card_props:
            merged_props["style"] = {
                **default_card_style["style"],
                **card_props.pop("style"),
            }
        merged_props.update(card_props)

    collapse_button_style = {
        "border": "none",
        "background": "none",
        "color": COLORS["muted"],
        "cursor": "pointer",
        "fontSize": "20px",
        "fontWeight": "bold",
        "transition": "transform 0.2s ease",
        "display": "flex",
        "alignItems": "center",
        "justifyContent": "center",
        "width": "28px",
        "height": "28px",
        "borderRadius": "4px",
    }

    collapse_button_hover = {
        **collapse_button_style,
        "backgroundColor": f"{COLORS['light']}",
    }

    return dbc.Card(
        [
            dbc.CardHeader(
                html.Div(
                    [
                        html.H5(
                            title,
                            className="mb-0",
                            style={
                                "color": COLORS["dark"],
                                "fontWeight": "600",
                            },
                            id=f"{card_id}-title",
                        ),
                        html.Button(
                            "-" if is_open else "+",
                            id=f"collapse-{card_id}",
                            style=collapse_button_style,
                            **{"data-hover-bg": f"{COLORS['light']}"},
                        ),
                    ],
                    className="d-flex justify-content-between align-items-center",
                ),
                style={
                    "backgroundColor": "transparent",
                    "borderBottom": "none",
                    "padding": "16px 20px",
                },
            ),
            dbc.Collapse(
                dbc.CardBody(content, style={"padding": "5px 20px 20px 20px"}),
                id=f"{card_id}-collapse",
                is_open=is_open,
            ),
        ],
        **merged_props,
    )


def create_section_header(title, help_text=None, help_id=None):
    """
    Creates a standardized section header with an optional help tooltip.

    Args:
        title: Section title text
        help_text: Optional tooltip text
        help_id: ID for the help tooltip (required if help_text is provided)

    Returns:
        A header component with optional help tooltip
    """
    if help_text and not help_id:
        raise ValueError("help_id is required when help_text is provided")

    header_components = [
        html.Label(
            title,
            style={
                "fontWeight": "600",
                "color": COLORS["dark"],
                "fontSize": "15px",
            },
        )
    ]

    # Add help badge if text is provided
    if help_text:
        header_components.extend(
            [
                dbc.Badge(
                    "?",
                    id=help_id,
                    color=COLORS["secondary"],
                    className="ms-2 rounded-circle",
                    style={
                        "cursor": "pointer",
                        "fontSize": "10px",
                        "width": "18px",
                        "height": "18px",
                        "display": "flex",
                        "alignItems": "center",
                        "justifyContent": "center",
                    },
                ),
                dbc.Tooltip(
                    help_text,
                    target=help_id,
                    placement="right",
                    **COMPONENT_STYLES["tooltip"],
                ),
            ]
        )

    return html.Div(
        header_components,
        className="d-flex align-items-center mb-3",
    )
