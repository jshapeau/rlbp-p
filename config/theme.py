"""
theme.py - Enhanced unified theme system for the Bison Habitat Analysis Tool
"""

import dash_bootstrap_components as dbc
import json

# =============================================================================
# THEME CONSTANTS
# =============================================================================

# Color Palette
COLORS = {
    # Brand Colors
    "primary": "#6CA5FC",  # Bright blue
    "secondary": "#62533E",  # Warm taupe
    "success": "#244F18",  # Deep forest green
    "danger": "#B83232",  # Red
    "warning": "#D4A968",  # Gold
    "info": "#427CFC",  # Blue
    # UI Colors
    "light": "#F8F9FA",  # Light grey
    "dark": "#301C02",  # Dark brown
    "white": "#FFFFFF",  # white
    "muted": "#8C8275",  # Muted warm grey
    # Special UI Colors
    "header": "#62533EBB",
    "highlight": "#1ef0609b",  # For changed cells
}

# Land Cover Type Styling
LAND_COVER_COLORS = {
    "Marsh": {"bg": "#F5CA7A44", "border": "#F5CA7A", "light_bg": "#F5CA7A22"},
    "Upland": {"bg": "#72894444", "border": "#728944", "light_bg": "#72894422"},
    "Swamp": {"bg": "#89444444", "border": "#894444", "light_bg": "#89444422"},
    "Fen": {"bg": "#B87FA844", "border": "#B87FA8", "light_bg": "#B87FA822"},
    "Bog": {"bg": "#4C007344", "border": "#4C0073", "light_bg": "#4C007322"},
}

# Typography
TYPOGRAPHY = {
    "font_family": '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
    "size": {
        "xs": "12px",
        "sm": "14px",
        "md": "16px",
        "lg": "18px",
        "xl": "20px",
    },
    "weight": {
        "normal": "400",
        "medium": "500",
        "semibold": "600",
        "bold": "700",
    },
}

# Layout Spacing
SPACING = {
    "xs": "4px",
    "sm": "8px",
    "md": "16px",
    "lg": "24px",
    "xl": "32px",
}

# Border Radius
RADIUS = {
    "xs": "2px",
    "sm": "4px",
    "md": "8px",
    "lg": "12px",
    "xl": "16px",
}

# Shadows
SHADOWS = {
    "none": "none",
    "xs": "0 1px 2px rgba(0,0,0,0.1)",
    "sm": "0 1px 3px rgba(0,0,0,0.1)",
    "md": "0 2px 4px rgba(0,0,0,0.1)",
    "lg": "0 4px 8px rgba(0,0,0,0.1)",
}

# Transitions
TRANSITIONS = {
    "fast": "all 0.1s ease",
    "medium": "all 0.2s ease",
    "slow": "all 0.3s ease",
}

# =============================================================================
# COMPONENT STYLES
# =============================================================================

# Common container style - reused in many places
CONTAINER_STYLE = {
    "padding": SPACING["md"],
    "backgroundColor": COLORS["white"],
    "borderRadius": RADIUS["md"],
    "boxShadow": SHADOWS["md"],
    "marginBottom": SPACING["md"],
}

# Component-specific styles
COMPONENT_STYLES = {
    # Cards
    "card": {
        "className": "mb-4 shadow-sm",
        "style": {
            "border": "none",
            "borderRadius": RADIUS["md"],
            "boxShadow": SHADOWS["sm"],
        },
    },
    # Buttons
    "button": {
        "className": "px-4 py-2",
        "style": {
            "borderRadius": RADIUS["sm"],
            "fontWeight": TYPOGRAPHY["weight"]["medium"],
            "transition": TRANSITIONS["medium"],
            "border": "none",
            "fontSize": TYPOGRAPHY["size"]["sm"],
        },
    },
    # Collapse Toggle
    "collapse_toggle": {
        "className": "collapse-toggle",
        "style": {
            "backgroundColor": "transparent",
            "border": "none",
            "fontSize": TYPOGRAPHY["size"]["sm"],
            "cursor": "pointer",
            "float": "right",
            "marginRight": "3px",
        },
    },
    # Sliders
    "slider": {
        "className": "my-2",
        "style": {
            "color": COLORS["primary"],
        },
    },
    # Dropdowns
    "dropdown": {
        "className": "",
        "style": {
            "borderRadius": RADIUS["sm"],
            "border": f'1px solid {COLORS["muted"]}',
            "fontSize": TYPOGRAPHY["size"]["sm"],
        },
    },
    # Tooltips
    "tooltip": {
        "className": "",
        "style": {
            "fontSize": TYPOGRAPHY["size"]["sm"],
            "padding": f"{SPACING['sm']} {SPACING['md']}",
            "textAlign": "left",
            "color": COLORS["white"],
            "borderRadius": RADIUS["sm"],
        },
    },
    # Tables
    "table": {
        "style_table": {
            "overflowX": "auto",
            "width": "100%",
            "borderRadius": RADIUS["md"],
            "boxShadow": SHADOWS["sm"],
            "padding": "0 1px",
        },
        "style_cell": {
            "padding": f"{SPACING['sm']} {SPACING['md']}",
            "textAlign": "left",
            "fontWeight": TYPOGRAPHY["weight"]["normal"],
            "fontFamily": TYPOGRAPHY["font_family"],
            "fontSize": TYPOGRAPHY["size"]["sm"],
            "maxWidth": "200px",
            "overflow": "hidden",
            "textOverflow": "ellipsis",
        },
        "style_header": {
            "backgroundColor": COLORS["light"],
            "fontWeight": TYPOGRAPHY["weight"]["semibold"],
            "border": "none",
            "padding": f"{SPACING['md']} {SPACING['md']}",
            "fontFamily": TYPOGRAPHY["font_family"],
        },
        "style_data": {
            "backgroundColor": COLORS["white"],
            "color": COLORS["dark"],
        },
    },
    # Generic Container
    "container": {"style": CONTAINER_STYLE},
    # Section Headers
    "section_header": {
        "style": {
            "color": COLORS["dark"],
            "fontWeight": TYPOGRAPHY["weight"]["semibold"],
            "fontSize": TYPOGRAPHY["size"]["lg"],
            "marginBottom": SPACING["md"],
        }
    },
    # Form Groups
    "form_group": {
        "style": {
            "marginBottom": SPACING["md"],
        }
    },
}

# =============================================================================
# DATA TABLE SPECIFIC CONFIG
# =============================================================================

# Table display constants
DATA_TABLE_CONFIG = {
    "threshold_small_change": 0.001,
    "threshold_cell_highlight": 0.0005,
    "column_config": [
        {
            "name": ["Land Cover Class", "Major"],
            "id": "Land_Cover_Major_Class",
        },
        {
            "name": ["Land Cover Class", "Minor"],
            "id": "Land_Cover_Minor_Class",
        },
        {
            "name": ["Area", "(km²) ✎"],
            "id": "Area_km2",
            "type": "numeric",
            "format": {"specifier": ".2f"},
            "editable": True,
        },
        {
            "name": ["Area", "(%) ✎"],
            "id": "Area_percentage",
            "type": "numeric",
            "format": {"specifier": ".2f"},
            "editable": True,
        },
        {
            "name": ["Bison", "Density"],
            "id": "Mean_Bison_Density",
            "type": "numeric",
            "format": {"specifier": ".2f"},
        },
        {
            "name": ["Bison", "Supported"],
            "id": "Maximum_Bison_Supported",
            "type": "numeric",
            "format": {"specifier": ".2f"},
        },
        {
            "name": ["% Change From Scenario", "Previous"],
            "id": "Change_From_Previous",
            "type": "numeric",
            "format": {"specifier": "percentage(1)"},
        },
        # {
        #     "name": ["% Change From Scenario", "Previous_BR"],
        #     "id": "Change_From_Previous_BR",
        #     "type": "numeric",
        #     "format": {"specifier": "percentage(1)"},
        # },
        # {
        #     "name": ["% Change From Scenario", "Previous_NM"],
        #     "id": "Change_From_Previous_NM",
        #     "type": "numeric",
        #     "format": {"specifier": "percentage(1)"},
        # },
        {
            "name": ["% Change From Scenario", "First"],
            "id": "Change_From_First",
            "type": "numeric",
            "format": {"specifier": "percentage(1)"},
        },
    ],
    "tooltip_config": {
        "Area_km2": {
            "value": "✎ Click to edit",
            "use_with": "both",
        },
        "Area_percentage": {
            "value": "✎ Click to edit",
            "use_with": "both",
        },
    },
    "change_columns": [
        "Area_km2",
        "Area_percentage",
        "Maximum_Bison_Supported",
        "Mean_Bison_Density",
        "Change_From_Previous",
        "Change_From_First",
    ],
}


def get_land_cover_style(major_class, is_minor=False):
    """
    Get styling for a land cover container based on class name

    Args:
        major_class: Land cover class name
        is_minor: Whether this is for a minor slider

    Returns:
        dict: Style dictionary
    """
    if major_class not in LAND_COVER_COLORS:
        return {}  # Fallback

    land_cover = LAND_COVER_COLORS[major_class]

    # Use appropriate styling based on type
    bg_color = land_cover["light_bg"] if is_minor else land_cover["bg"]
    border_width = "1px" if is_minor else "2px"
    padding = "6px" if is_minor else "10px"
    border_radius = "5px"

    return {
        "backgroundColor": bg_color,
        "border": f"{border_width} solid {land_cover['border']}",
        "borderRadius": border_radius,
        "padding": padding,
        "paddingBottom": "7px" if not is_minor else padding,
        "marginBottom": "6px" if is_minor else None,
    }


def get_data_table_conditional_styles(current_data=None, previous_data=None):
    """
    Get conditional styling for the data table, with optional change highlighting

    Args:
        current_data: Current table data
        previous_data: Previous table data for comparison

    Returns:
        list: Style rules for conditional formatting
    """
    threshold = DATA_TABLE_CONFIG["threshold_small_change"]

    # Base conditional styles
    styles = [
        # Positive changes
        {
            "if": {
                "column_id": "Change_From_Previous",
                "filter_query": f"{{Change_From_Previous}} > {threshold}",
            },
            "color": COLORS["success"],
            "fontWeight": TYPOGRAPHY["weight"]["medium"],
        },
        {
            "if": {
                "column_id": "Change_From_First",
                "filter_query": f"{{Change_From_First}} > {threshold}",
            },
            "color": COLORS["success"],
            "fontWeight": TYPOGRAPHY["weight"]["medium"],
        },
        # Negative changes
        {
            "if": {
                "column_id": "Change_From_Previous",
                "filter_query": f"{{Change_From_Previous}} < -{threshold}",
            },
            "color": COLORS["danger"],
            "fontWeight": TYPOGRAPHY["weight"]["medium"],
        },
        {
            "if": {
                "column_id": "Change_From_First",
                "filter_query": f"{{Change_From_First}} < -{threshold}",
            },
            "color": COLORS["danger"],
            "fontWeight": TYPOGRAPHY["weight"]["medium"],
        },
        # Selected cells
        {
            "if": {"state": "selected"},
            "backgroundColor": "rgba(51, 68, 135, 0.1)",
            "border": "1px solid rgb(51, 68, 135)",
        },
        # Editable cells
        {
            "if": {"column_editable": True},
            "backgroundColor": f"{COLORS['light']}50",
            "cursor": "pointer",
        },
        # Right-align numeric columns
        {"if": {"column_type": "numeric"}, "textAlign": "right"},
    ]

    # Add highlighting for changed cells if comparing data
    if current_data and previous_data:
        highlight_threshold = DATA_TABLE_CONFIG["threshold_cell_highlight"]

        for idx, (current_row, previous_row) in enumerate(
            zip(current_data, previous_data)
        ):
            for col in DATA_TABLE_CONFIG["change_columns"]:
                current_val = current_row.get(col, 0)
                previous_val = previous_row.get(col, 0)

                if abs(current_val - previous_val) > highlight_threshold:
                    styles.append(
                        {
                            "if": {"row_index": idx, "column_id": col},
                            "backgroundColor": f"{COLORS['info']}15",
                            "transition": "background-color 0.5s ease",
                        }
                    )

    return styles
