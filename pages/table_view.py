import dash
from components.layout import create_main_content, initialize_application_data_stores
from data.constants import create_initial_dataframe

from callbacks.table_view import *

dash.register_page(__name__, path="/")


def layout():
    df = create_initial_dataframe()
    initialize_application_data_stores(df),
    total_area = df["Area_km2"].sum()
    total_bison = (df["Area_km2"] * df["Mean_Bison_Density"]).sum()
    return create_main_content(df, total_area, total_bison)
