from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from functools import partial
from random_user_agent.user_agent import UserAgent
from tqdm import tqdm 
from bs4 import BeautifulSoup
import requests
import warnings
import re
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
from selenium.webdriver.common.by import By
from loguru import logger
import concurrent.futures
import json
import numpy as np
import datetime
import pytz

warnings.filterwarnings("ignore")

# Função para retornar um driver do selenium configurado para webscraping.
def _get_driver_webscraping():

    chrome_options = Options()
    # chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--log-level=3')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(service=Service(executable_path=ChromeDriverManager().install()), options=chrome_options)

    return driver

# Função para retornar um dicionário com os headers configurados para webscraping.
def _get_headers_webscraping():
    
    ua = UserAgent()
    user_agents = ua.get_random_user_agent()
    headers = {
        'user-agent': user_agents.strip(), 
        'encoding':'utf-8',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'DNT': '1',  # Do Not Track Request Header
    }

    return headers

# Função para retornar o número de páginas disponíveis com base na localidade e no tipo e subtipo escolhidos.
def _number_of_pages(base_url, transaction, type, local):
    '''
        ### Objetivo
        * Função para retornar o total de páginas disponível com base na localidade e no tipo e subtipo escolhidos.
        ### Parâmetros
        #### Transação: 
            * Possui as opções ['aluguel', 'venda'].
        #### Local: 
            * {uf}+{cidade} -> o nome do estado é separado do nome da cidade pelo sinal de +. O nome da cidade, caso tenha espaços, deve ser separado com -
            * Ex: sp+sao-paulo
    '''
    
    headers = _get_headers_webscraping()
    url = f'{base_url}/{transaction}/{type}/{local}/?transacao={transaction}&page=1'
    
    driver = _get_driver_webscraping()
    driver.implicitly_wait(10)
    
    try:

        driver.get(url)

        # Obtenção do total de imóveis disponíveis na url analisada
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        res = soup.find('div', {"class":"result-wrapper__title"}).text # listing-wrapper__title para result-wrapper__title em 22.11.23

        if res:
            properties = int(re.sub('[^0-9]','',res))
            properties_page = properties//100 if properties//100 > 1 else 1
            logger.info(f"Total de imóveis disponíveis na url {url}: {properties}")
        else:
            properties = None
            properties_page = None
            logger.warning(f"Não foi possível obter o total de imóveis disponíveis na url {url}")

        resultado = {
            'Parametros': {'Transacao': transaction, 'Tipo': type, 'Local': local},
            'Requisicao': {'Status': driver.execute_script("return document.readyState") == "complete"},
            'Imóveis': properties, 
            'Páginas': properties_page
        }

        # Retornando possível quantidade de páginas (em geral, cada página tem aproximadamente 100 imóveis)
        return resultado
    
    except Exception as e:
        
        logger.error(e)
        
        r = requests.get(url, headers = headers)
        resultado = {
            'Parametros': {'Transacao': transaction, 'Tipo': type, 'Local': local},
            'Requisicao': {'Status': r.status_code, 'Reason': r.reason, 'OK': r.ok},
            'Imóveis': None,
            'Páginas': None
        }

        return resultado

# Função para retornar o HTML de uma página com vários cards.
def _get_html_with_many_cards(base_url, transaction, type, local, paginas):

    # browser

    browser = _get_driver_webscraping()

    browser.get(f'{base_url}/{transaction}/{type}/{local}/?transacao={transaction}&pagina={paginas}')
    print(f'{base_url}/{transaction}/{type}/{local}/?transacao={transaction}&pagina={paginas}')
            
    time.sleep(2)

    # Rola até o fim da página para que todos os cards apareçam
    total_height = int(browser.execute_script("return document.body.scrollHeight"))
    n = 1

    while n < total_height:
        browser.execute_script(f"window.scrollTo(0, {n});")
        n += 90
        total_height = int(browser.execute_script("return document.body.scrollHeight"))

    time.sleep(2)

    resultado = browser.find_element(By.XPATH, '//*')
    source_code = resultado.get_attribute("innerHTML")

    browser.quit()

    return source_code

# Função para aplicar a função em paralelo para as funções de webscraping.
def _apply_functions_in_parallel_to_webscraping(list_use_in_function, function_to_apply, name_file, key_name, workers=3, args=None):

    if args is None: args = []
    info_pages = []
    erro_pages = {}

    
    # Função para salvar os resultados em Parquet
    def save_results():
        # Convertendo o HTML para um DataFrame e salvando como Parquet
        df_html = pd.DataFrame(info_pages)
        df_html.to_parquet(f"{name_file}.parquet", index=False)

        # Salvando os erros em formato Parquet
        df_erros = pd.DataFrame(list(erro_pages.items()), columns=[key_name, 'erro'])
        df_erros.to_parquet(f"{name_file}_erros.parquet", index=False)

    print(args)
    lista_parametros = args
    # Executando as requisições em paralelo
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        items = {executor.submit(function_to_apply, *args, item): item for item in list_use_in_function}

        # Usando tqdm para acompanhar o progresso
        for future in tqdm(concurrent.futures.as_completed(items), total=len(list_use_in_function), desc=f"Processando funções"):
            item = items[future]
            try:
                resultado = future.result()
                info_pages.append({f"{key_name}": item, "content": resultado})
            except Exception as exc:
                erro_pages[item] = str(exc)
                print(f'Erro na página {item}: {exc}')

            # Salva os resultados intermediários após cada execução
            save_results()

    return info_pages, erro_pages

# Função para ler os arquivos Parquet
def _read_results_parquet(name_file: str, key_name: str = 'url_imovel'):
    try:
        # Lendo os resultados de html_pagina e erro_pagina
        html_pages_df = pd.read_parquet(f"{name_file}.parquet")
        erro_pages_df = pd.read_parquet(f"{name_file}_erros.parquet")

        # Convertendo os DataFrames de volta para listas/dicionários
        html_pages = html_pages_df.to_dict(orient="records")
        erro_pages = dict(zip(erro_pages_df[key_name], erro_pages_df[key_name]))

        return html_pages, erro_pages

    except FileNotFoundError:
        print("Arquivo não encontrado.")
        return [], {}

# Função para ler os arquivos JSON
def _read_json_file(file_name):
    with open(file_name, "r") as f:
        try:
            data_list = json.load(f)  # Carrega o conteúdo diretamente
            logger.success("Dados Listas Processados")  # Exibe ou processa a lista de dicionários
        except json.JSONDecodeError as e:
            logger.error(f"Erro de decodificação JSON: {e}")
    
    return data_list

# Função para extrair os dados do HTML de uma página com vários cards.
def _extract_data_in_html_for_page_with_many_cards(dados_lista):

    data_list = []

    for pagina, html in enumerate(dados_lista):

        soup = BeautifulSoup(html['content'], 'html.parser')
        all_results = soup.find('div', {"class":"listing-wrapper__content"})

        try:
            for anuncio_pagina, result in enumerate(all_results):
                
                # id do imóvel
                try:
                    id = result.find_all('a', class_='ListingCard_result-card__Pumtx')[0].get('data-id') 
                except:
                    id = np.nan

                # URL
                try:
                    url_imo = result.find_all('a', class_='ListingCard_result-card__Pumtx')[0].get('href')
                except:
                    url_imo = np.nan

                # Se é destaque ou nao
                try:
                    destaque = result.find('div',{'class':'l-tag-card__content'}).text
                    destaque.replace('\n','')
                except:
                    destaque = np.nan

                # Titulo/Bairro
                try:
                    bairro = result.find_all('section', class_='card__location overflow-hidden')[0].find('h2').text
                except:
                    bairro = np.nan

                # Endereço
                try:
                    endereco = result.find_all('section', class_='card__location overflow-hidden')[0].find('p').text
                except:
                    endereco = np.nan

                # Descricao
                try:
                    descricao = result.find_all('p', class_='ListingCard_card__description__slBTG')[0].text
                except:
                    descricao = np.nan

                # Data completa de Extração
                data = datetime.datetime.now(tz = pytz.timezone('America/Sao_Paulo')).strftime("%Y-%m-%d")

                data_list.append({
                    'pagina': pagina,
                    'anuncio_pagina': anuncio_pagina,
                    'id_imovel': id,
                    'url_imovel': url_imo,
                    'destaque': destaque,
                    'bairro': bairro,
                    'endereco': endereco,
                    'descricao': descricao,
                    'data_completa': data,
                })

        except Exception as e:
            pass

    dataframe_property_urls = pd.DataFrame(data_list)
    return dataframe_property_urls

# Função para retornar o HTML de uma página específica para um imóvel.
def _get_html_especifc_for_wich_property(url_imo):

    dicionario_informacoes = {}
    browser = _get_driver_webscraping()
    browser.get(url_imo)

    try:
        botao = WebDriverWait(browser, 3).until(
            EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/div[1]/div[1]/div[1]/div[4]/div/a"))
        ).click()
    except:
        pass
    
    resultado = browser.find_element(By.XPATH, '//*')
    source_code = resultado.get_attribute("innerHTML")

    browser.quit()

    soup = BeautifulSoup(source_code, 'html.parser')

    try:
        preco = soup.find_all('p', class_='l-text l-u-color-neutral-28 l-text--variant-display-regular l-text--weight-bold price-info-value')[0].text
        dicionario_informacoes['preco'] = preco
    except:
        preco = np.nan

    try:
        dicionario_de_itens = soup.find_all("div", "amenities-list")
        todos_os_itens = dicionario_de_itens[0].find_all('p', class_="l-text l-u-color-neutral-28 l-text--variant-body-small l-text--weight-regular amenities-item")
        dicionario_itens_final = dict(map(lambda item: (item.get("itemprop"), item.text), todos_os_itens))
        dicionario_informacoes.update(dicionario_itens_final)
    except:
        pass

    try:
        condominio = soup.find_all('span', class_='l-text l-u-color-neutral-28 l-text--variant-body-regular l-text--weight-bold undefined')
        condominio = condominio[0].text
    except:
        condominio = np.nan

    try:
        iptu = soup.find_all('span', class_='l-text l-u-color-neutral-28 l-text--variant-body-regular l-text--weight-bold undefined')
        iptu = iptu[1].text
    except: 
        iptu = np.nan

    try:
        endereco = soup.find_all('p', class_='l-text l-u-color-neutral-28 l-text--variant-body-regular l-text--weight-bold address-info-value')
        endereco = endereco[0].text
    except:
        endereco = np.nan   

    dicionario_informacoes['condominio'] = condominio
    dicionario_informacoes['iptu'] = iptu
    dicionario_informacoes['endereco'] = endereco

    return dicionario_informacoes

# Função para transformar os dados em um DataFrame
def _transform_data_to_dataframe(dados_lista, aluguel=False):

    def _apply_identify_property_type(url):
        # Keywords to identify property types
        residential_keywords = ["apartamento", "casa", "condominio"]
        commercial_keywords = ["loja", "conjunto", "sala", "galpao", "laje", "terreno"]
        
        # Check if the URL contains any keywords for each property type
        for keyword in residential_keywords:
            if keyword in url:
                return "residencial", keyword
        for keyword in commercial_keywords:
            if keyword in url:
                return "comercial", keyword
        return "nao_identificado", np.nan

    def limpar_preco(valor):

        if isinstance(valor, str):
            valor = valor.replace("/mês", "").replace("R$", "").replace(".", "").replace(",", ".").strip()
            try:
                valor = float(valor)
            except:
                valor = None
        
        return valor

    def limpar_m2(valor):
        
        if isinstance(valor, str):
            valor = valor.replace("m²", "").replace(",", ".").strip()
            try:
                valor = float(valor)
            except:
                valor = None
        
        return valor

    def limpar_numero_ou_zero(valor):
        if isinstance(valor, str):
            if "-" not in valor:
                valor = re.sub(r"[^0-9]", "", valor)  # Remove qualquer coisa que não seja número
                return int(valor) if valor else 0
            else:
                valor = 0
        else:
            valor = 0
            
        return valor

    def limpar_numero(valor):
        if isinstance(valor, str):
            if "-" not in valor:
                valor = re.sub(r"[^0-9]", "", valor)  # Remove qualquer coisa que não seja número
                return int(valor) if valor else None
            else:
                valor = None
        return valor

    def limpar_booleano(valor):
        if isinstance(valor, str):
            if valor:
                return True
            else:
                return False
        else:
            return False

    value_coluns = "conteudo" if not aluguel else "content"
    colunas_relevantes = [
        f'{value_coluns}.floorsize', f'{value_coluns}.numberofrooms', f'{value_coluns}.numberofbathroomsTotal',
        f'{value_coluns}.numberofsuites', f'{value_coluns}.numberofparkingspaces', f'{value_coluns}.preco',
        f'{value_coluns}.endereco', f'{value_coluns}.floorlevel', f'{value_coluns}.condominio', f'{value_coluns}.iptu',
        f'{value_coluns}.pool', f'{value_coluns}.garden', f'{value_coluns}.sports_court', f'{value_coluns}.gym',
        f'{value_coluns}.elevator', f'{value_coluns}.gated_community',
        f'{value_coluns}.furnished', "url_imovel", "url"
    ]

    colunas_funcoes = {
        'preco': limpar_preco,
        'area': limpar_m2,
        'valor_condominio': limpar_preco,
        'iptu': limpar_preco,
        'banheiros': limpar_numero,
        'vagas_de_carro': limpar_numero_ou_zero,
        'quartos': limpar_numero,
        'suites': limpar_numero,
        'mobiliado': limpar_booleano,
        'andar': limpar_numero,
        'piscina': limpar_booleano,
        'condominio': limpar_booleano,
        'elevador': limpar_booleano,
        'jardim': limpar_booleano,
        'quadra_esportiva': limpar_booleano,
        'academia': limpar_booleano,
        
    }

    colunas_organizadas = [
        "url",           # URL do imóvel, para referência
        "endereco",      # Endereço do imóvel
        "preco",         # Preço do imóvel
        "area",          # Área total do imóvel
        "andar",         # Andar em que o imóvel está (se aplicável)
        "quartos",       # Número de quartos
        "suites",        # Número de suítes
        "banheiros",     # Número de banheiros
        "vagas_de_carro",# Número de vagas de estacionamento
        "valor_condominio",    # Valor do condomínio
        "iptu",          # Valor do IPTU
        "mobiliado",     # Indicação se o imóvel é mobiliado
        "piscina",       # Presença de piscina
        "condominio",    # Indicação se o imóvel está em condomínio fechado
        "elevador",      # Indicação se o imóvel tem elevador
        "jardim",        # Indicação se o imóvel tem jardim
        "quadra_esportiva",# Indicação se o imóvel tem quadra esportiva
        "academia",
        "finalidade",    # Finalidade do imóvel
        "tipo"           # Tipo de imóvel
    ]

    colunas_renomeadas = {
        f"{value_coluns}.condominio": "valor_condominio",
        f"{value_coluns}.endereco": "endereco",
        f"{value_coluns}.floorsize": "area",
        f"{value_coluns}.iptu": "iptu",
        f"{value_coluns}.numberofbathroomsTotal": "banheiros",
        f"{value_coluns}.numberofparkingspaces": "vagas_de_carro",
        f"{value_coluns}.numberofrooms": "quartos",
        f"{value_coluns}.numberofsuites": "suites",
        f"{value_coluns}.preco": "preco",
        f'{value_coluns}.floorlevel': 'andar',
        f'{value_coluns}.pool': 'piscina',
        f'{value_coluns}.gated_community': 'condominio',
        f"{value_coluns}.furnished": "mobiliado",
        f"{value_coluns}.elevator": "elevador",
        f"{value_coluns}.garden": "jardim",
        f"{value_coluns}.sports_court": "quadra_esportiva",
        f"{value_coluns}.gym": "academia",
        "url_imovel": "url"
    }

    dados_imoveis = pd.json_normalize(dados_lista)
    dados_imoveis.columns = dados_imoveis.columns.str.lower()

    colunas_existentes = [coluna for coluna in colunas_relevantes if coluna in dados_imoveis.columns]
    dados_imoveis = dados_imoveis[colunas_existentes].copy()

    dados_resumidos = dados_imoveis.rename(columns=colunas_renomeadas).copy()

    for coluna, funcao in colunas_funcoes.items():
        if coluna in dados_resumidos.columns:
            dados_resumidos[coluna] = dados_resumidos[coluna].apply(funcao)

    dados_resumidos["finalidade"], dados_resumidos["tipo"] = zip(*dados_resumidos["url"].apply(_apply_identify_property_type))

    colunas_existentes = [coluna for coluna in colunas_organizadas if coluna in dados_resumidos.columns]
    dados_resumidos_organizado = dados_resumidos[colunas_existentes]

    return dados_resumidos_organizado