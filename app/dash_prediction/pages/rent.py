import os
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
from shapely import wkt
from shapely.geometry import Point
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

locale.setlocale(locale.LC_ALL, 'pt_BR.utf8')
caminho = os.path.join(os.path.dirname(__file__), '..', '..', 'data')

tiles_list = [
    'OpenStreetMap', 
    'CartoDB positron',
    'CartoDB dark_matter'
]

def layout():

    layout = html.Div([

                html.H2("Aluguel Imóveis", className="Title-of-Page"),

                html.Div(children=[
                    
                    html.Div([html.Iframe(width='100%', height='100%', id="Iframe-Mapa")], className="Div-With-Map-Left-Side"),
                    html.Div([
                                                
                        html.Div([
                        
                            html.H3("Background", className="Title-About-Graph"),
                            dcc.RadioItems(
                                id="RadioItems-Opcoes",
                                options=[
                                    {'label': 'OpenStreetMap', 'value': 'OpenStreetMap'},
                                    {'label': 'CartoDB positron', 'value': 'CartoDB positron'},
                                    {'label': 'CartoDB dark_matter', 'value': 'CartoDB dark_matter'}
                                ],
                                className="RadioItems-Options-Map",
                                persistence=True,
                                persistence_type='local',
                            )
                        ], className="RadioItems-Div"),


                        html.Div([

                            html.H3("Exibição", className="Title-About-Graph"),

                            dcc.Checklist(
                                id="Checklist-Opcoes",
                                options=[
                                    {'label': 'Imóveis', 'value': 'imoveis'},
                                    {'label': 'Escolas', 'value': 'escolas'},
                                    {'label': 'Favelas', 'value': 'favelas'},
                                    {'label': 'Bairros', 'value': 'bairros'},
                                    {'label': 'Metrô', 'value': 'metro'},
                                    {'label': 'Hospitais', 'value': 'hospitais'},
                                ],
                                persistence=True,
                                persistence_type='local',
                                className="Checklist-Options-Map"
                            )
                        ], className="Checklist-Div"),
                                                
                    ], className="Div-With-Map-Right-Side"),
                    
                ], className="Div-With-Map"),


        ], className="First-Main-Div-Home")

    return layout
    
def explicitando_app_rent(app):

    def _adicionando_pontos_ao_mapa(mapa, geo_df, coluna1, coluna2, cor, coluna_ref, fields=None, tipo='ponto'):

        if tipo == 'ponto':
            if coluna1 == 'geometry.y' and coluna2 == 'geometry.x':

                for _, row in geo_df.iterrows():
                    folium.CircleMarker(
                        location=[row['geometry'].y, row['geometry'].x],
                        color=cor,
                        radius=1,
                        fill=True,
                        fill_color=cor,
                        fill_opacity=0.7,
                        popup=row[coluna_ref]
                    ).add_to(mapa)
            else:
                # Adicione os pontos do geo_df ao mapa
                valid_rows = geo_df.dropna(subset=[coluna1, coluna2])
                locations = valid_rows[[coluna1, coluna2]].values.tolist()
                popups = valid_rows[coluna_ref].tolist()
                markers = [
                    folium.CircleMarker(
                        location=location,
                        radius=1,
                        color=cor,
                        fill=True,
                        fill_color=cor,
                        fill_opacity=0.5,
                        popup=popup
                    )
                    for location, popup in zip(locations, popups)
                ]
                for marker in markers:
                    marker.add_to(mapa)
        else:
            folium.GeoJson(
                geo_df,
                style_function=lambda feature: {
                    'fillColor': cor,
                    'color': cor,
                    'weight': 1,
                    'fillOpacity': 0.3,
                },
                tooltip=folium.GeoJsonTooltip(fields=fields)
            ).add_to(mapa)


    @app.callback(
        Output("Iframe-Mapa", "srcDoc"),
        [Input("Checklist-Opcoes", "value"),
         Input("RadioItems-Opcoes", "value")]
    )
    def atualizar_os_dados_do_mapa(selected_options, background):

        if selected_options:

            if 'bairros' in selected_options:

                limites_bairros = gpd.read_file('dados_demograficos/Limite_de_Bairros/Limite_de_Bairros.shp')
                limites_bairros = limites_bairros.to_crs(epsg=4326)
                mapa_html = limites_bairros.explore('regiao_adm', marker_type=None, legend=False, location=[-22.9068, -43.1729], zoom_start=12, tiles=background)

            else:

                mapa_html = folium.Map(location=[-22.9068, -43.1729], zoom_start=12, tiles=background)


            if 'metro' in selected_options:
                paradas_de_metro = gpd.read_file('dados_demograficos/Estações_Metrô/Estações_Metrô.shp')
                paradas_de_metro = paradas_de_metro.to_crs(epsg=4326)
                _adicionando_pontos_ao_mapa(mapa_html, paradas_de_metro, 'geometry.y', 'geometry.x', 'red', 'flg_atm')
            
            if 'favelas' in selected_options:
                limite_favelas = gpd.read_file('dados_demograficos/Limite_Favelas/Limite_Favelas.shp').drop(columns=['data_cadas'])
                limite_favelas = limite_favelas.to_crs(epsg=4326)
                _adicionando_pontos_ao_mapa(mapa_html, limite_favelas, 'geometry.y', 'geometry.x', 'green', 'nome', tipo='poligono', fields=['nome', 'bairro', 'complexo'])
            
            if 'imoveis' in selected_options:
                imoveis = pd.read_parquet(f'{caminho}/dados_webscraping/dataframe_imoveis_aluguel_tratados_com_localizacao.parquet')
                geometry = [Point(xy) for xy in zip(imoveis['longitude'], imoveis['latitude'])]
                imoveis_gdf = gpd.GeoDataFrame(imoveis, geometry=geometry)
                imoveis_gdf = imoveis_gdf.set_crs(epsg=4326)
                _adicionando_pontos_ao_mapa(mapa_html, imoveis_gdf, 'geometry.y', 'geometry.x', 'blue', 'url', tipo='ponto')
            
            if 'escolas' in selected_options:
                escolas_municipais = gpd.read_file('dados_demograficos/Escolas_Municipais/Escolas_Municipais.shp')
                escolas_municipais = escolas_municipais.to_crs(epsg=4326)
                _adicionando_pontos_ao_mapa(mapa_html, escolas_municipais, 'geometry.y', 'geometry.x', 'orange', 'denominaca')

            if 'hospitais' in selected_options:
                hospitais = gpd.read_file('dados_demograficos/Unidades_de_Saúde_Municipais/Unidades_de_Saúde_Municipais.shp')
                hospitais = hospitais.to_crs(epsg=4326)
                _adicionando_pontos_ao_mapa(mapa_html, hospitais, 'geometry.y', 'geometry.x', 'purple', 'NOME')

        else:

            mapa_html = folium.Map(location=[-22.9068, -43.1729], zoom_start=12, tiles=background)

        return mapa_html.get_root().render()

    @app.callback(
        Output("RadioItems-Opcoes", "value"),
        [Input("RadioItems-Opcoes", "value")]
    )
    def atualizar_o_background_do_mapa(value):
        return value if value else tiles_list[1]

