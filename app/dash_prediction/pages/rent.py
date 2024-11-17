import sys
import locale
import numpy as np
import pandas as pd
import urllib.parse
from dash import html, dcc
from datetime import datetime
import plotly.graph_objects as go
import folium
import pandas as pd
import geopandas as gpd
import os

locale.setlocale(locale.LC_ALL, 'pt_BR.utf8')
caminho = os.path.join(os.path.dirname(__file__), '..', '..', 'data')

def layout():

    layout = html.Div([

                html.H2("Aluguel Imóveis", className="Title-of-Page"),

                html.Div(children=[
                    
                    html.Div([html.Iframe(srcDoc=open(f"{caminho}/dados_map/map.html").read(), width='100%', height='100%')], className="Div-With-Map-Left-Side"),
                    html.Div([html.H3("Rentabilidade")], className="Div-With-Map-Right-Side"),
                    
                ], className="Div-With-Map"),


        ], className="First-Main-Div-Home")

    return layout
    
def explicitando_app_rent(app):
    
    ...

        
