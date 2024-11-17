import os
import sys
from flask import Flask
import dash_mantine_components as dmc
import dash_bootstrap_components as dbc
from dash import html, dcc, Dash
from dash.dependencies import Input, Output

caminho = os.path.join(os.path.dirname(__file__), '../')
sys.path.append(caminho)

from components.main_layout import navbar_or_bigcard
from dash_prediction.pages.rent import layout as rent_layout
from dash_prediction.pages.rent import explicitando_app_rent

def criando_dash_perpetuo(server: Flask):

    os.environ["TZ"] = "America/Sao_Paulo"

    lista_paginas = [

        {
            "name": "Aluguel",
            "relative_path": "/prediction/aluguel",
            "variable": False,
            "style_variable": {"background-color": "#white"},
        },


        {
            "name": "Venda",
            "relative_path": "/prediction/venda",
            "variable": False,
            "style_variable": {"background-color": "#white"},
        },
    
    ]

    scripts = [
        "https://cdnjs.cloudflare.com/ajax/libs/dayjs/1.10.8/dayjs.min.js",
        "https://cdnjs.cloudflare.com/ajax/libs/dayjs/1.10.8/locale/pt-br.min.js",
    ]
    styles = [
        "https://fonts.googleapis.com",
        "https://fonts.googleapis.com/css2?family=Red+Hat+Display:ital,wght@0,300..900;1,300..900&display=swap",
        dbc.themes.BOOTSTRAP,
    ]

    app = Dash(
        __name__,
        url_base_pathname="/prediction/",
        external_stylesheets=styles,
        external_scripts=scripts,
        server=server,
        assets_folder=f'{os.path.join(os.path.abspath(os.path.dirname(__file__)), "..","assets")}',
        suppress_callback_exceptions=True,
    )

    # Layout do aplicativo
    app.layout = dmc.MantineProvider(  # Insere o MantineProvider como wrapper principal
        children=[
            dbc.Container(
                [
                    dcc.Location(id="url", refresh=True),
                    html.Div(
                        [
                            navbar_or_bigcard(
                                app, tipo="big", lista_paginas=lista_paginas
                            ),
                            navbar_or_bigcard(
                                app, tipo="smll", lista_paginas=lista_paginas
                            ),
                            html.Div(
                                [
                                    dmc.LoadingOverlay(  # Componente Mantine
                                        [
                                            html.Div(
                                                id="page-content",
                                                className="Container-Pages",
                                            ),
                                        ],
                                        loaderProps={
                                            "id": "custom-loader-id",
                                            "display": "none",
                                        },
                                        loading_state={
                                            "component_name": "my_component",
                                            "is_loading": False,
                                            "prop_name": "spinner",
                                        },
                                        className="Loading-Refresh-Pages",
                                    ),
                                ],
                                className="Second-Big-Div-in-First-Container",
                            ),
                        ],
                        className="First-Div-App",
                    ),
                ],
                fluid=True,
                className="First-Big-Container",
            )
        ]
    )

    explicitando_app_rent(app)


    @app.callback(
        Output("page-content", "children"), [Input("url", "pathname")]
    )
    def display_page(pathname):
        if pathname.endswith("/"):
            pathname = pathname[:-1]

        if (
            pathname == "/prediction/aluguel"
            or pathname == "/prediction/aluguel/"
        ):
            return rent_layout()

        else:
            return "404 - Page Not Found"

    return app


if __name__ == "__main__":
    server = Flask(__name__)
    app = criando_dash_perpetuo(server=server)
    app.run_server(debug=True, port=8080)