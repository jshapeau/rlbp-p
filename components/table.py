"""
data_display.py - Refactored data table component using the centralized theme system
"""

from dash import html, dash_table
import dash.dash_table.FormatTemplate as FormatTemplate
from config.theme import (
    COMPONENT_STYLES,
    DATA_TABLE_CONFIG,
    get_data_table_conditional_styles,
)


def create_data_table(df, previous_data=None):
    """
    Creates the data table component with consistent styling.

    Args:
        df: DataFrame containing the current data
        previous_data: Optional previous data state for change highlighting
    """
    # df = prepare_dataframe(df)

    current_data = df.to_dict("records")

    columns = []
    for col_config in DATA_TABLE_CONFIG["column_config"]:
        # Handle special percentage formatting
        if "format" in col_config and "specifier" in col_config["format"]:
            if col_config["format"]["specifier"] == "percentage(1)":
                col_config = {**col_config, "format": FormatTemplate.percentage(1)}
        columns.append(col_config)

    return dash_table.DataTable(
        id="table",
        columns=columns,
        data=current_data,
        page_size=20,
        style_cell=COMPONENT_STYLES["table"]["style_cell"],
        style_header=COMPONENT_STYLES["table"]["style_header"],
        style_header_conditional=[
            {
                "if": {"header_index": 1},
                "borderTop": "1px solid #f0f0f0",
            }
        ],
        style_data=COMPONENT_STYLES["table"]["style_data"],
        style_table=COMPONENT_STYLES["table"]["style_table"],
        style_data_conditional=get_data_table_conditional_styles(
            current_data, previous_data
        ),
        merge_duplicate_headers=True,
        tooltip_delay=0,
        tooltip_duration=None,
        tooltip=DATA_TABLE_CONFIG["tooltip_config"],
        cell_selectable=True,
        row_selectable=False,
    )


def prepare_dataframe(df):
    threshold = DATA_TABLE_CONFIG["threshold_small_change"]

    df.loc[abs(df["Change_From_Previous"]) < threshold, "Change_From_Previous"] = 0
    df.loc[abs(df["Change_From_First"]) < threshold, "Change_From_First"] = 0

    return df


def create_data_table_container(df, previous_data=None):
    return html.Div(
        create_data_table(df, previous_data),
        style=COMPONENT_STYLES["container"]["style"],
    )
