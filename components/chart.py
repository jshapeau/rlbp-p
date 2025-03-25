import pandas as pd
import plotly.graph_objects as go
from dash import html, dcc
from config.theme import COLORS
from .collapsible_card import create_collapsible_card
import dash_bootstrap_components as dbc

_SORTED_MAJOR_CLASSES = None


def create_chart_section():
    return create_collapsible_card(
        title="Bison Supported by Land Cover Type",
        content=html.Div(
            [
                dcc.Graph(
                    id="bison-distribution-chart",
                    figure=create_empty_figure(),
                    config={"displayModeBar": True, "responsive": True},
                    style={"height": "500px"},
                ),
            ],
            className="mt-3",
        ),
        card_id="bison-chart",
        is_open=True,
    )


def create_empty_figure():
    fig = go.Figure()
    fig.update_layout(
        template="plotly_white",
        font=dict(family="Arial, sans-serif", size=12),
        margin=dict(l=50, r=50, t=80, b=50),
        yaxis=dict(range=[0, 100]),
    )
    return fig


def format_rgb_for_plotly(rgb_tuple):
    """Converts RGB tuple to plotly-compatible RGB string."""
    return f"rgb({rgb_tuple[0]}, {rgb_tuple[1]}, {rgb_tuple[2]})"


def px_colors_from_subcategories():
    """Extracts colors from SUBCATEGORIES for plotly."""
    from data.constants import SUBCATEGORIES

    colors = []

    all_subcategories = []
    for major_class, subcats in SUBCATEGORIES.items():
        all_subcategories.extend(subcats)

    all_subcategories.sort(key=lambda x: x["id"])

    for subcat in all_subcategories:
        colors.append(format_rgb_for_plotly(subcat["color"]))

    return colors


def prepare_chart_data(current_data, scenarios_data, model_type="Behaviour Restricted"):
    df_current = pd.DataFrame(current_data)
    current_state_name = "Current Data"
    current_state = process_dataframe_for_chart(
        df_current, current_state_name, model_type
    )

    scenario_states = []
    for i, scenario in enumerate(scenarios_data):
        df_scenario = pd.DataFrame(scenario["data"])
        scenario_name = str(i) + ". " + scenario.get("description", f"Scenario {i+1}")
        scenario_state = process_dataframe_for_chart(
            df_scenario, scenario_name, model_type
        )
        scenario_states.append(scenario_state)

    return scenario_states + [current_state]


def process_dataframe_for_chart(df, state_name, model_type="Behaviour Restricted"):
    df = df.copy()

    area_by_landcover = (
        df.groupby(["Land_Cover_Major_Class", "Land_Cover_Minor_Class"])["Area_km2"]
        .sum()
        .to_dict()
    )

    if model_type == "Nutritional Maximum":
        df["Maximum_Bison_Supported"] = df["Area_km2"] * df["Mean_Bison_Density_NM"]
    else:
        df["Maximum_Bison_Supported"] = df["Maximum_Bison_Supported_BR"]

    grouped = (
        df.groupby(["Land_Cover_Major_Class", "Land_Cover_Minor_Class"])[
            "Maximum_Bison_Supported"
        ]
        .sum()
        .reset_index()
    )

    # Add area information to the grouped data
    grouped["Area_km2"] = grouped.apply(
        lambda row: area_by_landcover.get(
            (row["Land_Cover_Major_Class"], row["Land_Cover_Minor_Class"]), 0
        ),
        axis=1,
    )

    grouped["State"] = state_name
    grouped["Land_Cover_Minor_Class"] = grouped["Land_Cover_Minor_Class"].str.strip()
    grouped["Color"] = grouped.apply(
        lambda row: get_fixed_color_for_landcover(
            row["Land_Cover_Major_Class"], row["Land_Cover_Minor_Class"]
        ),
        axis=1,
    )

    return {"name": state_name, "data": grouped}


def get_fixed_color_for_landcover(major_class, minor_class):
    """
    Get the appropriate color for a land cover type using SUBCATEGORIES.
    Uses a direct approach to match colors to land cover combinations.
    """
    from data.constants import SUBCATEGORIES

    minor_class = minor_class.strip() if isinstance(minor_class, str) else minor_class

    if major_class in SUBCATEGORIES:

        for subcat in SUBCATEGORIES[major_class]:
            subcat_name = subcat["name"]
            if (
                minor_class in subcat_name
                or f"{major_class} {minor_class}" == subcat_name
            ):
                return format_rgb_for_plotly(subcat["color"])

    return "rgb(150, 150, 150)"  # Fallback


def data_states_are_equal(state1, state2):
    if state1["name"] != state2["name"]:
        return False

    df1 = state1["data"]
    df2 = state2["data"]

    if len(df1) != len(df2):
        return False

    merged = pd.merge(
        df1,
        df2,
        on=["Land_Cover_Major_Class", "Land_Cover_Minor_Class"],
        suffixes=("_1", "_2"),
    )

    return (
        merged["Maximum_Bison_Supported_1"] - merged["Maximum_Bison_Supported_2"]
    ).abs().max() < 0.01


def create_bison_distribution_figure(all_states, show_trend_line=False):
    if not all_states:
        return create_empty_figure()

    fig = go.Figure()

    fixed_major_class_order = ["Marsh", "Upland", "Swamp", "Fen", "Bog"]
    all_major_classes = fixed_major_class_order

    scenario_totals = {}
    for state in all_states:
        state_name = state["name"]
        scenario_totals[state_name] = state["data"]["Maximum_Bison_Supported"].sum()

    bar_opacity = 0.5 if show_trend_line else 1.0

    organized_data = {}

    for state in all_states:
        state_name = state["name"]
        organized_data[state_name] = {}

        # Group data by major class
        for _, row in state["data"].iterrows():
            major_class = row["Land_Cover_Major_Class"]
            minor_class = row["Land_Cover_Minor_Class"]
            bison_count = row["Maximum_Bison_Supported"]
            area_km2 = row["Area_km2"]
            color = row["Color"]

            if major_class not in organized_data[state_name]:
                organized_data[state_name][major_class] = {
                    "minor_classes": [],
                    "total": 0,
                }

            # Add this minor class
            organized_data[state_name][major_class]["minor_classes"].append(
                {
                    "name": minor_class,
                    "value": bison_count,
                    "area": area_km2,
                    "color": color,
                }
            )

            organized_data[state_name][major_class]["total"] += bison_count

    tickvals = []
    ticktext = []

    scenario_positions = {}
    x_position = 0

    for i, state in enumerate(all_states):

        state_name = state["name"]
        scenario_positions[state_name] = {}

        for j, major_class in enumerate(all_major_classes):
            x_pos = x_position + j
            tickvals.append(x_pos)
            ticktext.append(major_class)
            scenario_positions[state_name][major_class] = x_pos

        x_position += len(all_major_classes) + 0.5

    # Add traces for each minor class in each major class for each scenario
    for state in all_states:
        state_name = state["name"]

        for major_class in all_major_classes:
            if major_class not in organized_data[state_name]:
                continue

            x_pos = scenario_positions[state_name][major_class]

            # Sort minor classes by bison support (for consistent stacking)
            minor_classes = organized_data[state_name][major_class]["minor_classes"]
            minor_classes.sort(key=lambda x: x["value"], reverse=True)

            # Add each minor class as a stack component
            for minor_data in minor_classes:
                minor_class = minor_data["name"]
                bison_count = minor_data["value"]
                area_km2 = minor_data["area"]
                color = minor_data["color"]

                # Skip if bison count is negligible
                if bison_count < 0.1:
                    continue

                hover_text = (
                    f"Scenario: {state_name}<br>"
                    f"Land Cover: {major_class} - {minor_class}<br>"
                    f"Area: {area_km2:.1f} km²<br>"
                    f"Bison Supported: {bison_count:.1f}"
                )

                fig.add_trace(
                    go.Bar(
                        name=f"{major_class} - {minor_class}",
                        x=[x_pos],
                        y=[bison_count],
                        marker_color=color,
                        marker_opacity=bar_opacity,
                        hoverinfo="text",
                        hovertext=hover_text,
                        legendgroup=major_class,
                        showlegend=False,
                    )
                )

    # Calculate appropriate y-axis ranges
    max_major_class = 0
    for state in all_states:
        major_class_sums = (
            state["data"]
            .groupby("Land_Cover_Major_Class")["Maximum_Bison_Supported"]
            .sum()
        )
        if not major_class_sums.empty:
            max_major_class = max(max_major_class, major_class_sums.max())

    max_bar_y_value = max_major_class * 1.1
    max_total = max(scenario_totals.values()) if scenario_totals else 0
    max_total_y_value = max_total * 1.1

    # Add trend line
    if show_trend_line:
        trend_x_positions = []
        trend_y_values = []

        for state in all_states:
            state_name = state["name"]
            scenario_positions_values = list(scenario_positions[state_name].values())
            if scenario_positions_values:
                center_pos = sum(scenario_positions_values) / len(
                    scenario_positions_values
                )
                trend_x_positions.append(center_pos)
                trend_y_values.append(scenario_totals[state_name])

        fig.add_trace(
            go.Scatter(
                x=trend_x_positions,
                y=trend_y_values,
                mode="lines+markers",
                name="Total Bison Supported",
                line=dict(color="rgba(0, 0, 0, 0.8)", width=3),
                marker=dict(size=8, color="rgba(0, 0, 0, 0.8)"),
                yaxis="y2",
                hoverinfo="text",
                hovertext=[f"Total Bison: {val:.1f}" for val in trend_y_values],
                showlegend=False,
            )
        )

    # Create scenario group labels for bottom level of x-axis
    scenario_annotations = []
    should_alternate = len(all_states) > 2

    for i, state in enumerate(all_states):
        state_name = state["name"]
        display_name = state_name[:20] + "..." if len(state_name) > 20 else state_name
        positions = list(scenario_positions[state_name].values())

        if positions:
            center_pos = sum(positions) / len(positions)
            y_pos = -0.20 if not should_alternate or i % 2 == 0 else -0.25

            scenario_annotations.append(
                dict(
                    x=center_pos,
                    y=y_pos,
                    xref="x",
                    yref="paper",
                    text=f"<b>{display_name}</b>",
                    showarrow=False,
                    font=dict(family="Arial, sans-serif", size=11, color="black"),
                )
            )

    # Add dotted lines between scenario groups
    separator_shapes = []
    prev_end = None

    for state in all_states:
        state_name = state["name"]
        positions = list(scenario_positions[state_name].values())

        if positions and prev_end is not None:
            separator_pos = (prev_end + min(positions)) / 2
            separator_shapes.append(
                {
                    "type": "line",
                    "x0": separator_pos,
                    "y0": 0,
                    "x1": separator_pos,
                    "y1": max_bar_y_value,
                    "line": {"color": "rgba(0, 0, 0, 0.2)", "width": 1, "dash": "dash"},
                }
            )

        if positions:
            prev_end = max(positions)

    # Set layout with proper axis configuration
    layout = {
        "template": "plotly_white",
        "barmode": "stack",
        "bargap": 0,
        "bargroupgap": 0.05,
        "font": dict(family="Arial, sans-serif", size=12),
        "margin": dict(l=50, r=70, t=30, b=100),
        "xaxis": dict(
            tickvals=tickvals,
            ticktext=ticktext,
            tickangle=90,
            tickfont=dict(size=12),
            ticksuffix="  ",
            ticklen=8,
            domain=[0, 1],
        ),
        "annotations": scenario_annotations,
        "yaxis": {
            "domain": [0, 0.95],
            "range": [0, max_bar_y_value],
            "title": dict(
                text="Bison Supported by Land Cover Type",
                font=dict(
                    color="rgba(0,0,0," + ("0.3" if show_trend_line else "1.0") + ")"
                ),
            ),
            "tickfont": dict(
                color="rgba(0,0,0," + ("0.3" if show_trend_line else "1.0") + ")"
            ),
        },
        "yaxis2": {
            "title": "Total Bison Supported",
            "side": "right",
            "overlaying": "y",
            "range": [0, max_total_y_value],
            "showgrid": False,
            "visible": show_trend_line,
        },
        "shapes": separator_shapes,
    }

    fig.update_layout(**layout)
    return fig
