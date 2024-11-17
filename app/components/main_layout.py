import os
import sys
from dash import html, dcc
from datetime import datetime
from dash_iconify import DashIconify
import dash_mantine_components as dmc
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output

caminho = os.path.join(os.path.dirname(__file__), '../')
sys.path.append(caminho)
from modules.function import imagens_para_base64

def navbar_or_bigcard(app, tipo, lista_paginas):

    caminho_imagens = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), "..", "images"
    )
    imagens = ["Menu.png"]
    caminhos_completos = [os.path.join(caminho_imagens, imagem) for imagem in imagens]
    entrada_base64, menu_base64, logout_base64 = "", "", ""
    
    logo_base64 = imagens_para_base64(*caminhos_completos)
    
    def function_listando_paginas(tipo, lista_paginas, entrada_base64):

        return dbc.Nav(
            [
                html.Div(
                    [
                        # html.A(
                        #     html.Img(
                        #         src="data:image/png;base64,{}".format(entrada_base64),
                        #         className="Logo-in-Card",
                        #     ),
                        #     href="/dashboards",
                        # )
                    ]
                ),
                html.Ul(
                    [
                        dbc.NavItem(
                            [
                                html.Div(
                                    [
                                        dbc.NavLink(
                                            html.Div(
                                                [
                                                    html.Div([f"{page['name']}"]),
                                                    html.Div(
                                                        [
                                                            html.A(
                                                                html.Div(
                                                                    DashIconify(
                                                                        icon="ic:sharp-arrow-right",
                                                                        className="Arrow-Right",
                                                                    )
                                                                ),
                                                                href=page[
                                                                    "relative_path"
                                                                ],
                                                                style={"padding": "0"},
                                                            )
                                                        ]
                                                    ),
                                                ],
                                                className="Item-List-in-Card",
                                            ),
                                            id=f"nav-link-{page['name']}-{tipo}",
                                            href=page["relative_path"],
                                        )
                                    ]
                                ),
                            ]
                        )
                        for page in lista_paginas
                    ],
                    className="List-in-Card",
                ),
            ],
            pills=True,
        )

    if tipo == "smll":

        main_menu = dmc.Menu(
            [
                dmc.MenuTarget(
                    html.A(
                        html.Img(
                            src="data:image/png;base64,{}".format(menu_base64),
                            className="Menu-in-Nav-Bar",
                        )
                    )
                ),
                dmc.MenuDropdown(
                    [
                        function_listando_paginas(
                            "smll", lista_paginas, entrada_base64
                        ),
                        html.Div(
                            [
                                html.A(
                                    html.Img(
                                        src="data:image/png;base64,{}".format(
                                            logout_base64
                                        ),
                                        className="Logout-in-Card",
                                    ),
                                    href="/logout",
                                )
                            ]
                        ),
                    ]
                ),
            ],
            closeOnItemClick=True,
            closeOnEscape=True,
        )

        layout = html.Div(
            [
                html.Div(
                    [
                        html.Img(
                            src="data:image/png;base64,{}".format(logo_base64),
                            className="Logo-in-Nav-Bar",
                        )
                    ]
                ),
                html.Div([main_menu], className="Menu-in-Div"),
            ],
            id="nav-bar",
            className="nav-bar",
        )

    elif tipo == "big":

        layout = html.Div(
            [
                function_listando_paginas("big", lista_paginas, entrada_base64),
                html.Div(
                    [
                        html.A(
                            html.Img(
                                src="data:image/png;base64,{}".format(logout_base64),
                                className="Logout-in-Card",
                            ),
                            href="/logout",
                        )
                    ]
                ),
            ],
            className="First-Big-Card",
        )

    outputs_main = [
        Output(f"nav-link-{page['name']}-{tipo}", "active") for page in lista_paginas
    ]
    outputs_main.extend(
        [Output(f"nav-link-{page['name']}-{tipo}", "style") for page in lista_paginas]
    )

    @app.callback(outputs_main, [Input("url", "pathname")])
    def update_login_link(pathname):

        updated_pages = []

        for page in lista_paginas:

            if page["relative_path"] in pathname:

                variable = True
                style_variable = {"background-color": "#E2E5EB"}

            else:

                variable = False
                if tipo == "smll":
                    style_variable = {"background-color": "white"}
                else:
                    style_variable = {"background-color": "#F2F4F8"}

            updated_pages.append(
                {"variable": variable, "style_variable": style_variable}
            )

        outputs = []
        outputs = [page["variable"] for page in updated_pages]
        outputs.extend(page["style_variable"] for page in updated_pages)

        return outputs

    return layout


def page_refresh(app):

    layout = html.Div(
        [
            html.H6(
                children="Não atualizado ainda",
                id="Page-Refresh-Title",
                className="Page-Refresh-Title",
            ),
            dcc.Interval(id="ultima-atualizacao", interval=5 * 1000),
        ]
    )

    @app.callback(
        Output("Page-Refresh-Title", "children"),
        [Input("ultima-atualizacao", "n_intervals")],
    )
    def atualizando_o_horario_no_site(n_intervals):

        caminho_atual = os.getcwd()

        if "data" in caminho_atual:
            caminho_dos_arquivos = caminho_atual

        elif "app" not in caminho_atual:
            caminho_dos_arquivos = os.path.join(caminho_atual, "app/data")

        else:
            caminho_dos_arquivos = os.path.join(caminho_atual, "data")

        with open(f"{caminho_dos_arquivos}/ultima_att.txt", "r") as arquivo:
            linhas = arquivo.readlines()
            ultima_att = linhas[-1]
            ultima_att = datetime.strptime(ultima_att, "%Y-%m-%d %H:%M:%S.%f%z")
            ultima_att = ultima_att.strftime("%d de %B de %Y, %H:%M:%S")

        return f"Última atualização: {ultima_att}"

    return layout


if __name__ == "__main__":

    lista_paginas = [
        {
            "name": "Home",
            "relative_path": "/dashboards/dashboard-perpetuo/home",
            "variable": False,
            "style_variable": {"background-color": "#white"},
        },
        {
            "name": "Detalhamento Vendas",
            "relative_path": "/dashboards/dashboard-perpetuo/detalhamento-vendas",
            "variable": False,
            "style_variable": {"background-color": "#white"},
        },
        {
            "name": "Detalhamento Tráfego",
            "relative_path": "/dashboards/dashboard-perpetuo/detalhamento-trafego",
            "variable": False,
            "style_variable": {"background-color": "#white"},
        },
        {
            "name": "Detalhamento Orgânico",
            "relative_path": "/dashboards/dashboard-perpetuo/detalhamento-organico",
            "variable": False,
            "style_variable": {"background-color": "#white"},
        },
        {
            "name": "Detalhamento Leads",
            "relative_path": "/dashboards/dashboard-perpetuo/detalhamento-leads",
            "variable": False,
            "style_variable": {"background-color": "#white"},
        },
    ]

    def update_login_link(pathname):

        for page in lista_paginas:

            if page["relative_path"] in pathname:

                page["variable"] = True
                page["style_variable"] = {"background-color": "#E2E5EB"}

            else:

                page["variable"] = False
                page["style_variable"] = {"background-color": "#white"}

        return [page["variable"] for page in lista_paginas], [
            page["style_variable"] for page in lista_paginas
        ]

    update_login_link("/dashboards/dashboard-perpetuo/home")