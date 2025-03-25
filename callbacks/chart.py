from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from dash import callback_context
import pandas as pd
from components.chart import prepare_chart_data, create_bison_distribution_figure


def register_bison_chart_callbacks(app):
    @app.callback(
        Output("bison-distribution-chart", "figure"),
        [
            Input("table", "data"),
            Input("scenarios-storage", "data"),
            Input("load-scenario-button", "n_clicks"),
            Input("save-scenario-button", "n_clicks"),
            Input("delete-last-scenario-button", "n_clicks"),
            Input("create-preset-scenario", "n_clicks"),
            Input("show-trend-line", "value"),
            Input("model-dropdown", "value"),
        ],
        [
            State("scenarios-table", "selected_rows"),
        ],
    )
    def update_bison_chart(
        table_data,
        scenarios_data,
        load_scenario_clicks,
        save_scenario_clicks,
        delete_scenario_clicks,
        create_preset_clicks,
        show_trend_line,
        model_type,
        selected_rows,
    ):
        if not callback_context.triggered or not table_data:
            raise PreventUpdate

        if not scenarios_data:
            scenarios_data = []

        all_states = prepare_chart_data(table_data, scenarios_data, model_type)
        show_trend = show_trend_line
        fig = create_bison_distribution_figure(all_states, show_trend)

        return fig
