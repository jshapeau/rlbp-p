from dash import html, dcc
import dash_bootstrap_components as dbc
from .controls import create_controls_section
from .table import create_data_table
from .scenario import create_scenario_section
from config.theme import COLORS
from components.collapsible_card import create_collapsible_card
from datetime import date

from components.chart import create_chart_section


def create_footer():
    """Creates the application footer with ACE lab branding and partner links."""
    return html.Div(
        style={
            "backgroundColor": COLORS["header"],
            "borderTop": f"4px solid {COLORS['secondary']}",
            "marginTop": "auto",
        },
        children=[
            dbc.Container(
                [
                    dbc.Row(
                        [
                            _create_footer_logo_component(),
                            _create_footer_links_component(),
                            _create_footer_partners_component(),
                        ],
                        className="py-4",
                        align="center",
                    )
                ]
            ),
        ],
    )


def initialize_application_data_stores(df):
    return html.Div(
        [
            dcc.Store(id="previous-table-data", data=df.to_dict("records")),
            dcc.Store(id="error-store", storage_type="memory"),
            dcc.Store(id="mode-change-in-progress", data=False),
        ]
    )


def create_main_content(df, total_area, total_bison):
    """Creates the main content area with controls and data display."""
    return dbc.Container(
        [
            initialize_application_data_stores(df),
            dbc.Row(
                [
                    dbc.Col(
                        create_controls_section(df, total_area, total_bison),
                        width=12,
                        lg=4,
                        className="mb-4 mb-lg-0",
                    ),
                    dbc.Col(
                        [
                            create_chart_section(),
                            create_scenario_section(),
                            create_collapsible_card(
                                "Data Table",
                                create_data_table(df),
                                "data-table",
                                is_open=False,
                            ),
                        ],
                        width=12,
                        lg=8,
                    ),
                ],
                className="g-4",
            ),
        ],
        className="px-3 px-md-4 mb-5",
        style={"maxWidth": "1400px"},
    )


def create_app_layout(df, total_area):
    """Creates the main application layout."""
    total_bison = (df["Area_km2"] * df["Mean_Bison_Density"]).sum()

    return html.Div(
        [
            create_main_content(df, total_area, total_bison),
            create_footer(),
        ],
        style={"backgroundColor": COLORS["light"], "minHeight": "100vh", "margin": 0},
    )


def _create_footer_links_component():
    return dbc.Col(
        html.Div(
            [
                html.H2(
                    "Applied Conservation Ecology Lab",
                    style={
                        "fontFamily": "Arial, Times, serif",
                        "fontSize": "26px",
                        "color": COLORS["white"],
                    },
                    className="mb-3",
                ),
                html.Div(
                    [
                        html.A(
                            "Research",
                            href="https://ace-lab.ca/research.php",
                            className="text-white text-decoration-none",
                            target="_blank",
                        ),
                        " | ",
                        html.A(
                            "About",
                            href="https://ace-lab.ca/lab.php",
                            className="text-white text-decoration-none",
                            target="_blank",
                        ),
                        " | ",
                        html.A(
                            "Publications",
                            href="https://ace-lab.ca/publications.php",
                            className="text-white text-decoration-none",
                            target="_blank",
                        ),
                        " | ",
                        html.A(
                            "News & Notes",
                            href="https://ace-lab.tumblr.com/",
                            className="text-white text-decoration-none",
                            target="_blank",
                        ),
                    ],
                    className="mb-2",
                ),
                html.Div(
                    f"ACE Lab © {date.today().year}",
                    style={"color": COLORS["white"]},
                    className="small",
                ),
            ],
            className="text-center",
        ),
        width=8,
        className="d-flex align-items-center justify-content-center",
    )


def create_navbar_section():
    return dbc.Navbar(
        dbc.Container(
            [
                dbc.NavbarToggler(id="navbar-toggler"),
                dbc.Col(
                    html.A(
                        html.Img(
                            src="/assets/logo.png",
                            style={
                                "height": "70px",
                                "width": "auto",
                            },
                        ),
                        href="https://ace-lab.ca/",
                        target="_blank",
                    ),
                    className="col-auto d-none d-sm-block",
                ),
                dbc.Col(
                    html.H1(
                        ["Ronald Lake", html.Br(), "Bison Carrying Capacity"],
                        style={
                            "color": COLORS["white"],
                            "fontWeight": "400",
                            "fontSize": "1.6rem",
                            "margin": "0",
                            "textAlign": "center",
                            "lineHeight": "1.2",
                        },
                    ),
                    className="d-flex align-items-center justify-content-center",
                ),
                dbc.Collapse(
                    dbc.Nav(
                        [
                            dbc.NavItem(
                                dbc.NavLink("Table View", href="/", active="exact")
                            ),
                            dbc.NavItem(
                                dbc.NavLink(
                                    "Spatial View", href="/spatial", active="exact"
                                )
                            ),
                        ],
                        className="ms-auto",
                    ),
                    id="navbar-collapse",
                    navbar=True,
                    className="flex-grow-0",
                ),
            ],
            fluid=True,
            style={"maxWidth": "1400px"},
            className="px-3 px-md-4",
        ),
        color=COLORS["header"],
        dark=True,
        style={
            "borderBottom": f"4px solid {COLORS['secondary']}",
            "paddingTop": "1rem",
            "paddingBottom": "1rem",
            "minHeight": "90px",
            "marginBottom": "2rem",
        },
    )


def _create_footer_logo_component():
    return dbc.Col(
        html.A(
            html.Img(
                src="/assets/logo-ace-splash2.png",
                style={
                    "height": "175px",
                    "width": "175px",
                    "objectFit": "contain",
                },
            ),
            href="https://ace-lab.ca/",
            target="_blank",
        ),
        width=2,
        className="d-flex align-items-center",
    )


def _create_footer_partners_component():
    return dbc.Col(
        dbc.Col(
            html.Div(
                [
                    html.A(
                        html.Img(
                            src="/assets/RLBP_logo_dark.png",
                            style={
                                "width": "100%",
                                "height": "auto",
                            },
                        ),
                        href="#",
                        target="_blank",
                        className="mb-2",
                    ),
                ],
                className="d-flex flex-column align-items-end",
            ),
            className="d-flex align-items-center",
        )
    )
