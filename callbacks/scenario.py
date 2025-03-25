from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from dash import callback_context, no_update, html
import pandas as pd
import numpy as np
from data.table import BisonDataFrame
from data.constants import SCENARIOS, MINE_IMPACT_IN_KM2, create_initial_dataframe
from config import theme
from functools import lru_cache


def initial(bison_data: BisonDataFrame) -> None:
    """Apply transformation for Scenario 0: Initialize current land cover conditions."""
    bison_data.df = create_initial_dataframe()

    for col in ["Change_From_Previous", "Change_From_First"]:
        if col not in bison_data.df.columns:
            bison_data.df[col] = 0


def habitat_loss(bison_data: BisonDataFrame) -> None:
    """Apply transformation for Scenario 1: Remove habitat based on specific mining impacts."""
    df = bison_data.df

    def get_impact(major, minor):
        minor = minor.strip() if isinstance(minor, str) else minor

        if major in MINE_IMPACT_IN_KM2 and minor in MINE_IMPACT_IN_KM2[major]:
            return MINE_IMPACT_IN_KM2[major][minor]
        return 0

    impacts = df.apply(
        lambda row: get_impact(
            row["Land_Cover_Major_Class"], row["Land_Cover_Minor_Class"]
        ),
        axis=1,
    )

    new_areas = (df["Area_km2"] - impacts).clip(lower=0)

    bison_data.update_areas(new_areas)


def habitat_enhancement(bison_data: BisonDataFrame) -> None:
    """Apply transformation for Scenario 2: Convert upland areas and wetlands to optimal habitat."""
    df = bison_data.df
    new_areas = df["Area_km2"].copy()
    new_areas = _convert_upland_to_deciduous(df, new_areas)
    new_areas = _convert_wetlands_to_meadow_marsh(df, new_areas)

    bison_data.update_areas(new_areas)


def _convert_upland_to_deciduous(df, new_areas):
    """Helper function to convert all upland to upland deciduous."""
    upland_mask = df["Land_Cover_Major_Class"] == "Upland"
    upland_sum = df.loc[upland_mask, "Area_km2"].sum()

    new_areas.loc[upland_mask] = 0

    deciduous_upland_mask = (df["Land_Cover_Major_Class"] == "Upland") & (
        df["Land_Cover_Minor_Class"] == "Deciduous"
    )
    if any(deciduous_upland_mask):
        new_areas.loc[deciduous_upland_mask] = upland_sum

    return new_areas


def _convert_wetlands_to_meadow_marsh(df, new_areas):
    """Helper function to convert all wetlands to meadow marsh."""
    wetlands_mask = df["Land_Cover_Major_Class"].isin(["Bog", "Fen", "Marsh", "Swamp"])
    wetlands_sum = df.loc[wetlands_mask, "Area_km2"].sum()

    new_areas.loc[wetlands_mask] = 0

    meadow_marsh_mask = (df["Land_Cover_Major_Class"] == "Marsh") & (
        df["Land_Cover_Minor_Class"] == "Meadow"
    )
    if any(meadow_marsh_mask):
        new_areas.loc[meadow_marsh_mask] = wetlands_sum

    return new_areas


def short_term_drying(bison_data: BisonDataFrame):
    """Apply transformation for Scenario 3a: Convert rich fen to poor fen and meadow marsh to upland meadow."""
    df = bison_data.df
    new_areas = df["Area_km2"].copy()

    new_areas = _convert_rich_fen_to_poor_fen(df, new_areas)
    new_areas = _convert_meadow_marsh_to_upland_meadow(df, new_areas)

    bison_data.update_areas(new_areas)


def _convert_rich_fen_to_poor_fen(df, new_areas):
    """Helper function to convert rich fen types to poor fen types."""
    fen_types = ["Shrubby", "Treed", "Graminoid"]
    for fen_type in fen_types:
        rich_mask = (df["Land_Cover_Major_Class"] == "Fen") & (
            df["Land_Cover_Minor_Class"] == f"{fen_type} Rich"
        )
        poor_mask = (df["Land_Cover_Major_Class"] == "Fen") & (
            df["Land_Cover_Minor_Class"] == f"{fen_type} Poor"
        )

        if any(rich_mask):
            rich_area = df.loc[rich_mask, "Area_km2"].sum()
            new_areas.loc[rich_mask] = 0
            if any(poor_mask):
                new_areas.loc[poor_mask] += rich_area

    return new_areas


def _convert_meadow_marsh_to_upland_meadow(df, new_areas):
    """Helper function to convert meadow marsh to upland meadow."""
    meadow_marsh_mask = (df["Land_Cover_Major_Class"] == "Marsh") & (
        df["Land_Cover_Minor_Class"] == "Meadow"
    )
    upland_meadow_mask = (df["Land_Cover_Major_Class"] == "Upland") & (
        df["Land_Cover_Minor_Class"] == "Meadow"
    )

    if any(meadow_marsh_mask):
        meadow_area = df.loc[meadow_marsh_mask, "Area_km2"].sum()
        new_areas.loc[meadow_marsh_mask] = 0
        if any(upland_meadow_mask):
            new_areas.loc[upland_meadow_mask] += meadow_area

    return new_areas


def long_term_drying(bison_data: BisonDataFrame):
    """Apply transformation for Scenario 3b: Convert fen to bog and meadow marsh to upland deciduous."""
    df = bison_data.df
    new_areas = df["Area_km2"].copy()

    new_areas = _convert_fen_to_bog(df, new_areas)
    new_areas = _convert_meadow_marsh_to_upland_deciduous(df, new_areas)

    return bison_data.update_areas(new_areas)


def _convert_fen_to_bog(df, new_areas):
    """Helper function to convert fen types to corresponding bog types."""
    fen_to_bog_mappings = [
        {"fen_types": ["Shrubby Rich", "Shrubby Poor"], "bog_type": "Shrubby"},
        {"fen_types": ["Treed Rich", "Treed Poor"], "bog_type": "Treed"},
        {"fen_types": ["Graminoid Rich", "Graminoid Poor"], "bog_type": "Open"},
    ]

    for mapping in fen_to_bog_mappings:
        fen_mask = (df["Land_Cover_Major_Class"] == "Fen") & (
            df["Land_Cover_Minor_Class"].isin(mapping["fen_types"])
        )
        bog_mask = (df["Land_Cover_Major_Class"] == "Bog") & (
            df["Land_Cover_Minor_Class"] == mapping["bog_type"]
        )

        if any(fen_mask):
            area_sum = df.loc[fen_mask, "Area_km2"].sum()
            new_areas.loc[fen_mask] = 0
            if any(bog_mask):
                new_areas.loc[bog_mask] += area_sum

    return new_areas


def _convert_meadow_marsh_to_upland_deciduous(df, new_areas):
    """Helper function to convert meadow marsh to upland deciduous."""
    meadow_marsh_mask = (df["Land_Cover_Major_Class"] == "Marsh") & (
        df["Land_Cover_Minor_Class"] == "Meadow"
    )
    upland_deciduous_mask = (df["Land_Cover_Major_Class"] == "Upland") & (
        df["Land_Cover_Minor_Class"] == "Deciduous"
    )

    if any(meadow_marsh_mask):
        meadow_area = df.loc[meadow_marsh_mask, "Area_km2"].sum()
        new_areas.loc[meadow_marsh_mask] = 0
        if any(upland_deciduous_mask):
            new_areas.loc[upland_deciduous_mask] += meadow_area

    return new_areas


def calculate_percentage_change(new_value, old_value):
    """Calculate percentage change with handling for zero values and small changes."""
    if isinstance(new_value, (pd.Series, np.ndarray)) and isinstance(
        old_value, (pd.Series, np.ndarray)
    ):
        # Vectorized
        with np.errstate(divide="ignore", invalid="ignore"):
            change = np.where(old_value != 0, (new_value - old_value) / old_value, 0)
            return np.where(np.abs(change) < 0.001, 0.0, change)
    else:
        # Single value
        if old_value == 0:
            return 0.0
        change = (new_value - old_value) / old_value
        return 0.0 if abs(change) < 0.001 else change


@lru_cache(maxsize=32)
def get_scenario_function(scenario_name):
    """Cache the scenario function lookup."""
    scenario_funcs = {
        "Present Day": initial,
        "Habitat Loss": habitat_loss,
        "Habitat Enhancement": habitat_enhancement,
        "Short-term Drying": short_term_drying,
        "Long-term Drying": long_term_drying,
        "Cumulative Loss and Short-term Drying": lambda data: [
            habitat_loss(data),
            short_term_drying(data),
        ],
        "Cumulative Loss and Long-term Drying": lambda data: [
            habitat_loss(data),
            long_term_drying(data),
        ],
    }
    return scenario_funcs.get(scenario_name)


def update_scenarios_data(existing_scenarios, stored_scenarios, current_data):
    """Update scenario data with model-specific calculations."""

    df_current = pd.DataFrame(current_data)

    total_area_val = df_current["Area_km2"].sum()

    current_is_nm = df_current["Mean_Bison_Density"].equals(
        df_current["Mean_Bison_Density_NM"]
    )

    total_bison_val = df_current["Maximum_Bison_Supported"].sum()
    total_bison_nm = df_current["Maximum_Bison_Supported_NM"].sum()
    total_bison_br = df_current["Maximum_Bison_Supported_BR"].sum()

    if not existing_scenarios:
        change_from_previous = change_from_first = 0.0
        change_from_previous_nm = change_from_first_nm = 0.0
        change_from_previous_br = change_from_first_br = 0.0
    else:
        changes = _process_scenario_changes(
            df_current,
            existing_scenarios,
            stored_scenarios,
            total_bison_val,
            total_bison_nm,
            total_bison_br,
        )

        if current_is_nm:
            change_from_previous = changes["change_from_previous_nm"]
            change_from_first = changes["change_from_first_nm"]
        else:
            change_from_previous = changes["change_from_previous_br"]
            change_from_first = changes["change_from_first_br"]

        change_from_previous_nm = changes["change_from_previous_nm"]
        change_from_first_nm = changes["change_from_first_nm"]
        change_from_previous_br = changes["change_from_previous_br"]
        change_from_first_br = changes["change_from_first_br"]

    new_scenario_display = {
        "description": f"Scenario {len(existing_scenarios) + 1}",
        "total_area": total_area_val,
        "total_bison": total_bison_val,
        "change_from_previous": change_from_previous,
        "change_from_first": change_from_first,
        "total_bison_NM": total_bison_nm,
        "total_bison_BR": total_bison_br,
        "change_from_previous_NM": change_from_previous_nm,
        "change_from_previous_BR": change_from_previous_br,
        "change_from_first_NM": change_from_first_nm,
        "change_from_first_BR": change_from_first_br,
    }

    new_scenario_full = {**new_scenario_display, "data": df_current.to_dict("records")}
    return new_scenario_display, new_scenario_full


def _process_scenario_changes(
    df_current,
    existing_scenarios,
    stored_scenarios,
    total_bison_val,
    total_bison_nm,
    total_bison_br,
):
    """Process changes between current scenario and historical scenarios for both models."""
    first_scenario = existing_scenarios[0]
    prev_scenario = existing_scenarios[-1]

    previous_bison = prev_scenario["total_bison"]
    first_bison = first_scenario["total_bison"]

    change_from_previous = calculate_percentage_change(total_bison_val, previous_bison)
    change_from_first = calculate_percentage_change(total_bison_val, first_bison)

    first_bison_nm = first_scenario.get("total_bison_NM", first_scenario["total_bison"])
    prev_bison_nm = prev_scenario.get("total_bison_NM", prev_scenario["total_bison"])
    change_from_first_nm = calculate_percentage_change(total_bison_nm, first_bison_nm)
    change_from_previous_nm = calculate_percentage_change(total_bison_nm, prev_bison_nm)

    first_bison_br = first_scenario.get("total_bison_BR", first_scenario["total_bison"])
    prev_bison_br = prev_scenario.get("total_bison_BR", prev_scenario["total_bison"])
    change_from_first_br = calculate_percentage_change(total_bison_br, first_bison_br)
    change_from_previous_br = calculate_percentage_change(total_bison_br, prev_bison_br)

    # Bundle up all the change values
    changes = {
        "change_from_previous": change_from_previous,
        "change_from_first": change_from_first,
        "change_from_previous_nm": change_from_previous_nm,
        "change_from_first_nm": change_from_first_nm,
        "change_from_previous_br": change_from_previous_br,
        "change_from_first_br": change_from_first_br,
    }

    return changes


def register_scenario_callbacks(app):
    @app.callback(
        [
            Output("scenarios-table", "data"),
            Output("scenario-description", "value"),
            Output("scenarios-storage", "data"),
            Output("load-scenario-button", "n_clicks"),
            Output("scenarios-table", "selected_rows"),
        ],
        [
            Input("save-scenario-button", "n_clicks"),
            Input("delete-last-scenario-button", "n_clicks"),
            Input("create-preset-scenario", "n_clicks"),
        ],
        [
            State("scenario-description", "value"),
            State("table", "data"),
            State("scenarios-table", "data"),
            State("scenarios-storage", "data"),
            State("preset-scenario-dropdown", "value"),
        ],
    )
    def update_scenarios(
        save_clicks,
        delete_clicks,
        create_preset_clicks,
        description,
        current_data,
        existing_scenarios,
        stored_scenarios,
        preset_scenario_dropdown,
    ):
        """Main callback for processing scenario changes."""
        load_scenario_clicks = no_update
        selected_rows = no_update

        ctx = callback_context
        if not ctx.triggered:
            existing_scenarios = existing_scenarios or []
            stored_scenarios = stored_scenarios or []
            return (
                existing_scenarios,
                "",
                stored_scenarios,
                load_scenario_clicks,
                selected_rows,
            )

        triggered_id = ctx.triggered[0]["prop_id"]
        existing_scenarios = existing_scenarios or []
        stored_scenarios = stored_scenarios or []

        if triggered_id == "save-scenario-button.n_clicks" and save_clicks:
            return _handle_save_scenario(
                existing_scenarios, stored_scenarios, current_data, description
            )
        elif (
            triggered_id == "create-preset-scenario.n_clicks"
            and create_preset_clicks
            and preset_scenario_dropdown
        ):
            return _handle_preset_scenario(
                existing_scenarios,
                stored_scenarios,
                current_data,
                preset_scenario_dropdown,
            )
        elif triggered_id == "delete-last-scenario-button.n_clicks" and delete_clicks:
            return _handle_delete_scenario(existing_scenarios, stored_scenarios)

        return (
            existing_scenarios,
            "",
            stored_scenarios,
            load_scenario_clicks,
            selected_rows,
        )

    @app.callback(
        [
            Output("preset-scenario-description-default", "children"),
            Output("preset-scenario-description-default", "style"),
        ],
        Input("preset-scenario-dropdown", "value"),
        prevent_initial_call=True,
    )
    def update_preset_description(selected_preset):
        """Fetch scenario information for the selected scenario and format for display in scenario preview box."""
        if not selected_preset:
            return "", {"display": "none"}

        scenario_data = SCENARIOS.get(selected_preset, {})
        description = scenario_data.get("description", "")

        style = {
            "padding": "10px",
            "backgroundColor": theme.COLORS["light"],
            "borderRadius": "6px",
            "minHeight": "40px",
            "display": "block",
        }

        lines = [description] if isinstance(description, str) else description

        return (
            html.Div(
                [
                    html.Strong(f"Scenario {selected_preset}"),
                    html.Ul(
                        [html.Li(line) for line in lines],
                        style={
                            "listStyleType": "disc",
                            "marginLeft": "20px",
                            "marginTop": "20px",
                        },
                    ),
                ]
            ),
            style,
        )


def _handle_save_scenario(
    existing_scenarios, stored_scenarios, current_data, description
):
    """Save a new scenario from the current state of the data."""
    new_scenario_display, new_scenario_full = update_scenarios_data(
        existing_scenarios, stored_scenarios, current_data
    )

    if description:
        new_scenario_display["description"] = description
        new_scenario_full["description"] = description

    existing_scenarios.append(new_scenario_display)
    stored_scenarios.append(new_scenario_full)

    load_scenario_clicks = 1
    selected_rows = [len(stored_scenarios) - 1]

    return (
        existing_scenarios,
        "",
        stored_scenarios,
        load_scenario_clicks,
        selected_rows,
    )


def _handle_preset_scenario(
    existing_scenarios, stored_scenarios, current_data, preset_scenario_dropdown
):
    """Handle creating a preset scenario."""
    bison_data = BisonDataFrame(current_data)
    func = get_scenario_function(preset_scenario_dropdown)

    if not func:
        return [no_update] * 5

    if callable(func):
        result = func(bison_data)
        # Provide the option of returning a result directly rather than a function
    else:
        return [no_update] * 5

    new_scenario_display, new_scenario_full = update_scenarios_data(
        existing_scenarios,
        stored_scenarios,
        bison_data.df.to_dict("records"),
    )

    new_scenario_display["description"] = preset_scenario_dropdown
    new_scenario_full["description"] = preset_scenario_dropdown

    existing_scenarios.append(new_scenario_display)
    stored_scenarios.append(new_scenario_full)

    load_scenario_clicks = 1
    selected_rows = [len(stored_scenarios) - 1]

    return (
        existing_scenarios,
        "",
        stored_scenarios,
        load_scenario_clicks,
        selected_rows,
    )


def _handle_delete_scenario(existing_scenarios, stored_scenarios):
    """Delete the most recent scenario."""
    if existing_scenarios:
        existing_scenarios.pop()
        stored_scenarios.pop()

    return (
        existing_scenarios,
        "",
        stored_scenarios,
        no_update,
        no_update,
    )
