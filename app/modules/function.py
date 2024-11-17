import base64
import pandas as pd



def imagens_para_base64(*args):
    imagens_base64 = []
    for caminho_imagem in args:
        imagem_base64 = base64.b64encode(open(caminho_imagem, 'rb').read()).decode('ascii')
        imagens_base64.append(imagem_base64)
    return imagens_base64

def formatar_dinheiro_brasileiro(valor):
        if valor != " ":
            return 'R$ ' + '{:,.2f}'.format(valor).replace(",", " ").replace(".", ",").replace(" ", ".")
        else:
            return valor

def formatar_inteiros_brasileiro(valor):
        return '{:,.0f}'.format(valor).replace(",", ".")

def formatar_porcentagem_brasileiro(valor):
        return '{:,.2f}'.format(valor).replace(".", ",") + "%"

def tooltip_de_cada_tabela(dataframe: pd.DataFrame):

    tooltip = [{
            column: {"value": str(value), "type": "markdown"}
            for column, value in row.items() if len(str(value)) > 11
        }for row in  dataframe.to_dict("records")
    ]

    return tooltip
