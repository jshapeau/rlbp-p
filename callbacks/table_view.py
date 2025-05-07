from dash.dependencies import Input, Output, State, ALL
from dash.exceptions import PreventUpdate
from dash import callback_context, no_update, callback
import math
import pandas as pd

from config.theme import get_data_table_conditional_styles
from components.controls import create_slider_marks
from data.constants import SLIDER_MAX_VALUES
from data.sliders import SliderState
from data.table import BisonDataFrame


@callback(
    [
        Output("table", "data", allow_duplicate=True),
        Output("total-bison-display-table", "children", allow_duplicate=True),
        Output("mode-change-in-progress", "data", allow_duplicate=True),
        Output("scenarios-table", "data", allow_duplicate=True),
    ],
    Input("model-dropdown", "value"),
    [
        State("table", "data"),
        State("scenarios-table", "data"),
        State("scenarios-storage", "data"),
    ],
    prevent_initial_call=True,
)
def update_density_model(
    model_type, table_data, scenarios_table_data, stored_scenarios
):
    """
    Updates display values based on the selected model. No recalculations occur here:
    this callback only updates which model-specific values are displayed.

    Args:
        model_type: Selected density model type ("Nutritional Maximum" or "Behaviour Restricted")
        table_data: Current table data
        scenarios_table_data: Current scenarios table data
        stored_scenarios: Stored scenario data with values for both models

    Returns:
        Tuple containing:
        - Updated table data
        - Formatted total bison count
        - Flag indicating mode change is in progress
        - Updated scenarios table data
    """
    data = BisonDataFrame(table_data)

    if model_type == "Nutritional Maximum":
        data.df["Mean_Bison_Density"] = data.df["Mean_Bison_Density_NM"]
        data.df["Maximum_Bison_Supported"] = data.df["Maximum_Bison_Supported_NM"]
    else:  # "Behaviour Restricted"
        data.df["Mean_Bison_Density"] = data.df["Mean_Bison_Density_BR"]
        data.df["Maximum_Bison_Supported"] = data.df["Maximum_Bison_Supported_BR"]

    updated_scenarios = []
    for i, scenario in enumerate(scenarios_table_data):
        if i < len(stored_scenarios):
            stored = stored_scenarios[i]
            updated = scenario.copy()

            if model_type == "Nutritional Maximum":
                updated["total_bison"] = stored.get(
                    "total_bison_NM", scenario["total_bison"]
                )
                updated["change_from_previous"] = stored.get(
                    "change_from_previous_NM", scenario["change_from_previous"]
                )
                updated["change_from_first"] = stored.get(
                    "change_from_first_NM", scenario["change_from_first"]
                )
            else:  # "Behaviour Restricted"
                updated["total_bison"] = stored.get(
                    "total_bison_BR", scenario["total_bison"]
                )
                updated["change_from_previous"] = stored.get(
                    "change_from_previous_BR", scenario["change_from_previous"]
                )
                updated["change_from_first"] = stored.get(
                    "change_from_first_BR", scenario["change_from_first"]
                )

            updated_scenarios.append(updated)
        else:
            updated_scenarios.append(scenario)

    return (
        data.df.to_dict("records"),
        f"{data.total_bison:.0f}",
        True,
        updated_scenarios,
    )


@callback(
    [
        Output({"type": "major-slider", "index": ALL}, "max"),
        Output({"type": "major-slider", "index": ALL}, "marks"),
        Output({"type": "major-slider", "index": ALL}, "step"),
        Output({"type": "major-slider", "index": ALL}, "value", allow_duplicate=True),
        Output({"type": "slider", "index": ALL}, "max"),
        Output({"type": "slider", "index": ALL}, "marks"),
        Output({"type": "slider", "index": ALL}, "step"),
        Output({"type": "slider", "index": ALL}, "value", allow_duplicate=True),
        Output("mode-change-in-progress", "data", allow_duplicate=True),
        Output("area-adjustment-title", "children"),
    ],
    Input("proportional-checkbox", "value"),
    [
        State({"type": "major-slider", "index": ALL}, "value"),
        State({"type": "slider", "index": ALL}, "value"),
        State("table", "data"),
    ],
    prevent_initial_call=True,
)
def update_slider_mode(
    is_proportional_checked, major_slider_values, minor_slider_values, table_data
):
    """
    Updates slider properties when switching between percentage and absolute modes.

    Recalculates slider values, maximums, steps, and marks based on the selected mode.

    Args:
        is_proportional_checked: Boolean indicating if percentage mode is active
        major_slider_values: Current values of all major sliders
        minor_slider_values: Current values of all minor sliders
        table_data: Current table data

    Returns:
        Multiple outputs for updating slider properties and values
    """
    data = pd.DataFrame(table_data)
    total_area = sum(data["Area_km2"])
    num_minor_sliders = len(minor_slider_values)
    num_major_sliders = len(major_slider_values)

    if is_proportional_checked:
        max_val_major, max_val_minor = 100, 100
        updated_minor_values = [(val / total_area * 100) for val in data["Area_km2"]]
        updated_major_values = _calculate_major_class_values(data, is_percentage=True)

        area_text = "Area Adjustment (%)"
    else:
        max_val_major, max_val_minor = _calculate_adaptive_slider_maximums(data)
        updated_minor_values = list(data["Area_km2"])
        updated_major_values = _calculate_major_class_values(data, is_percentage=False)

        area_text = "Area Adjustment (km\u00b2)"

    marks_major, marks_minor, _, _, steps_major, steps_minor = create_slider_marks(
        max_val_major, max_val_minor
    )

    return (
        [max_val_major] * num_major_sliders,
        [marks_major] * num_major_sliders,
        [steps_major] * num_major_sliders,
        updated_major_values,
        [max_val_minor] * num_minor_sliders,
        [marks_minor] * num_minor_sliders,
        [steps_minor] * num_minor_sliders,
        updated_minor_values,
        True,
        area_text,
    )


def _calculate_major_class_values(data, is_percentage=False):
    """
    Calculate values for major class sliders based on dataframe data.

    Args:
        data: DataFrame containing land cover data
        is_percentage: If True, calculates values as percentages of total area
                      If False, uses absolute area values

    Returns:
        List of values for each major class
    """
    major_classes = list(dict.fromkeys(data["Land_Cover_Major_Class"]))
    result = []

    for major_class in major_classes:
        class_sum = sum(data[data["Land_Cover_Major_Class"] == major_class]["Area_km2"])
        if is_percentage:
            total_area = sum(data["Area_km2"])
            result.append(class_sum / total_area * 100 if total_area > 0 else 0)
        else:
            result.append(class_sum)

    return result


def _calculate_adaptive_slider_maximums(data):
    """
    Calculate appropriate maximum values for sliders based on current data.

    Ensures sliders always have sufficient headroom for value increases
    by providing at least 10% margin above current maximum values.

    Args:
        data: DataFrame containing land cover data

    Returns:
        Tuple of (major_slider_max, minor_slider_max)
    """
    max_value_in_data = data["Area_km2"].max()

    major_class_sums = data.groupby("Land_Cover_Major_Class")["Area_km2"].sum()
    max_major_in_data = major_class_sums.max() if not major_class_sums.empty else 0

    max_val_minor = SLIDER_MAX_VALUES["minor_sliders"]
    if max_value_in_data > max_val_minor * 0.9:
        max_val_minor = math.ceil(max_value_in_data * 1.1 / 100) * 100

    max_val_major = SLIDER_MAX_VALUES["major_sliders"]
    if max_major_in_data > max_val_major * 0.9:
        max_val_major = math.ceil(max_major_in_data * 1.1 / 100) * 100

    return max_val_major, max_val_minor


@callback(
    [
        Output({"type": "slider", "index": ALL}, "value"),
        Output({"type": "major-slider", "index": ALL}, "value"),
        Output("error-store", "data"),
        Output("table", "data"),
        Output("total-bison-display-table", "children"),
        Output("total-area-display-table", "children"),
        Output("mode-change-in-progress", "data"),
        Output({"type": "major-slider", "index": ALL}, "max", allow_duplicate=True),
        Output({"type": "major-slider", "index": ALL}, "marks", allow_duplicate=True),
        Output({"type": "slider", "index": ALL}, "max", allow_duplicate=True),
        Output({"type": "slider", "index": ALL}, "marks", allow_duplicate=True),
    ],
    [
        Input({"type": "slider", "index": ALL}, "value"),
        Input({"type": "major-slider", "index": ALL}, "value"),
        Input("proportional-checkbox", "value"),
        Input("load-scenario-button", "n_clicks"),
        Input("table", "data"),
    ],
    [
        State("previous-table-data", "data"),
        State("scenarios-storage", "data"),
        State("scenarios-table", "selected_rows"),
        State("mode-change-in-progress", "data"),
        State({"type": "major-slider", "index": ALL}, "max"),
        State({"type": "slider", "index": ALL}, "max"),
        State("model-dropdown", "value"),
    ],
    prevent_initial_call=True,
)
def update_application_state(
    minor_slider_values,
    major_slider_values,
    is_proportional_checked,
    load_clicks,
    table_data,
    previous_state_table_data,
    stored_scenarios,
    selected_table_rows,
    is_mode_change,
    current_major_slider_maxes,
    current_minor__slider_maxes,
    model_type,
):
    if not callback_context.triggered:
        raise PreventUpdate

    if is_mode_change:
        return _get_no_update_response(minor_slider_values, major_slider_values)

    trigger_id = callback_context.triggered_id
    minor_slider_ids = callback_context.inputs_list[0]
    major_slider_ids = callback_context.inputs_list[1]

    if trigger_id == "proportional-checkbox":
        raise PreventUpdate

    table = BisonDataFrame(table_data)
    sliders = _initialize_slider_state(
        table,
        minor_slider_ids,
        major_slider_ids,
        is_proportional_checked,
        current_major_slider_maxes,
        current_minor__slider_maxes,
    )

    _process_trigger_event(
        trigger_id,
        table,
        sliders,
        previous_state_table_data,
        stored_scenarios,
        load_clicks,
        selected_table_rows,
        model_type,
    )

    return _prepare_callback_output(
        table,
        sliders,
        is_proportional_checked,
        major_slider_values,
        minor_slider_values,
    )


def _initialize_slider_state(
    table,
    minor_slider_ids,
    major_slider_ids,
    is_proportional_checked,
    current_major_slider_maxes,
    current_minor_slider_maxes,
):
    """
    Initialize the slider state object with current values and settings.

    Args:
        table: BisonDataFrame instance with current data
        minor_slider_ids: List of minor slider ID dictionaries
        major_slider_ids: List of major slider ID dictionaries
        is_proportional_checked: Boolean indicating if percentage mode is active
        current_major_slider_maxes: Current maximum values for major sliders
        current_minor_slider_maxes: Current maximum values for minor sliders

    Returns:
        Initialized SliderState object
    """
    sliders = SliderState(
        table, minor_slider_ids, major_slider_ids, is_proportional_checked
    )

    # Preserve existing maximum values to prevent unwanted resets
    if current_major_slider_maxes and len(current_major_slider_maxes) > 0:
        sliders.major_max = current_major_slider_maxes[0]
    if current_minor_slider_maxes and len(current_minor_slider_maxes) > 0:
        sliders.minor_max = current_minor_slider_maxes[0]

    return sliders


def _process_trigger_event(
    trigger_id,
    table,
    sliders,
    previous_data,
    stored_scenarios,
    load_clicks,
    selected_rows,
    model_type,
):
    """
    Process the event that triggered the callback based on the trigger ID.

    Routes the update process to the appropriate handler function based on
    whether the change originated from the table, a scenario load, or a slider.

    Args:
        trigger_id: ID of the component that triggered the callback
        table: BisonDataFrame instance with current data
        sliders: SliderState instance managing slider values
        previous_data: Previous table data for detecting changes
        stored_scenarios: List of saved scenarios
        load_clicks: Number of times the load scenario button was clicked
        selected_rows: Currently selected rows in the scenarios table
    """
    if trigger_id == "table":
        _handle_table_update(
            table, sliders, previous_data, stored_scenarios, model_type
        )
    elif trigger_id == "load-scenario-button":
        _handle_scenario_load(
            table, sliders, load_clicks, selected_rows, stored_scenarios, model_type
        )
    else:
        _handle_slider_change(table, sliders, trigger_id, stored_scenarios, model_type)


def _prepare_callback_output(
    table, sliders, is_proportional_checked, major_slider_values, minor_slider_values
):
    """
    Prepare the final output values for the callback.

    Formats slider values, error data, and display values,
    and determines whether slider marks need to be updated.

    Args:
        table: BisonDataFrame instance with current data
        sliders: SliderState instance with current slider values
        is_proportional_checked: Boolean indicating if percentage mode is active
        major_slider_values: Current values of all major sliders
        minor_slider_values: Current values of all minor sliders

    Returns:
        Tuple containing all output values for the callback
    """
    slider_minor_values, slider_major_values, error_data = sliders.format_output()
    total_bison = table.total_bison
    total_area = table.total_area

    if not is_proportional_checked and error_data.get("update_marks", False):
        max_major = error_data.get("major_max", SLIDER_MAX_VALUES["major_sliders"])
        max_minor = error_data.get("minor_max", SLIDER_MAX_VALUES["minor_sliders"])
        major_marks, minor_marks, _, _, _, _ = create_slider_marks(max_major, max_minor)

        return (
            slider_minor_values,
            slider_major_values,
            error_data,
            table.df.to_dict("records"),
            f"{total_bison:.0f}",
            f"{total_area:.2f}",
            False,
            [max_major] * len(major_slider_values),
            [major_marks] * len(major_slider_values),
            [max_minor] * len(minor_slider_values),
            [minor_marks] * len(minor_slider_values),
        )
    else:
        return (
            slider_minor_values,
            slider_major_values,
            error_data,
            table.df.to_dict("records"),
            f"{total_bison:.0f}",
            f"{total_area:.2f}",
            False,
            [no_update] * len(major_slider_values),
            [no_update] * len(major_slider_values),
            [no_update] * len(minor_slider_values),
            [no_update] * len(minor_slider_values),
        )


def _get_no_update_response(minor_values, major_values):
    """
    Return a response with no updates for all callback outputs.
    Used when no actual changes should be made (e.g., during mode transitions).

    Args:
        minor_values: List of minor slider values
        major_values: List of major slider values

    Returns:
        Tuple of no_update values for all outputs
    """
    return (
        [no_update] * len(minor_values),
        [no_update] * len(major_values),
        no_update,
        no_update,
        no_update,
        no_update,
        False,
        [no_update] * len(major_values),
        [no_update] * len(major_values),
        [no_update] * len(minor_values),
        [no_update] * len(minor_values),
    )


def _handle_table_update(table, sliders, previous_data, stored_scenarios, model_type):
    """
    Update data when changes come from the table editor.

    Args:
        table: BisonDataFrame instance with current data
        sliders: SliderState instance managing slider values
        previous_data: Previous table data for detecting changes
        stored_scenarios: List of saved scenarios
    """
    table.update_from_table(table.df.to_dict("records"), previous_data)
    table.calculate_changes_from_scenario(stored_scenarios, model_type)
    sliders.sync()


def _handle_scenario_load(
    table, sliders, load_clicks, selected_rows, stored_scenarios, model_type
):
    """
    Handle loading a saved scenario into the current state.

    Args:
        table: BisonDataFrame instance with current data
        sliders: SliderState instance managing slider values
        load_clicks: Number of times the load scenario button was clicked
        selected_rows: Currently selected rows in the scenarios table
        stored_scenarios: List of saved scenarios
    """
    if load_clicks and selected_rows and stored_scenarios:
        table.update_from_scenario(
            stored_scenarios[selected_rows[0]]["data"], model_type
        )

        sliders.sync()


def _handle_slider_change(table, sliders, trigger_id, stored_scenarios, model_type):
    """
    Process changes originating from slider movements.

    Args:
        table: BisonDataFrame instance with current data
        sliders: SliderState instance managing slider values
        trigger_id: ID of the slider that triggered the change
        stored_scenarios: List of saved scenarios
    """
    slider_type = trigger_id["type"]
    slider_index = trigger_id["index"]

    if slider_type == "major-slider":
        sliders.update_from_major_change(slider_index)
    elif slider_type == "slider":
        sliders.update_from_minor_change([slider_index])

    table.calculate_changes_from_scenario(stored_scenarios, model_type)


# @callback(
#     [
#         Output("table", "style_data_conditional"),
#         Output("previous-table-data", "data"),
#     ],
#     [Input("table", "data")],
#     [State("previous-table-data", "data")],
# )
# def update_table_conditional_styles(current_data, previous_data):
#     """
#     Updates the conditional styling of the data table and stores current data.

#     Args:
#         current_data: Current table data
#         previous_data: Previous table data

#     Returns:
#         Tuple containing:
#         - Updated conditional styling rules
#         - Current data (to be stored as previous data for next update)
#     """
#     if not current_data:
#         raise PreventUpdate

#     style_conditional = get_data_table_conditional_styles(current_data, previous_data)
#     return style_conditional, current_data
