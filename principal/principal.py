#!/usr/bin/env python
# coding: utf-8


import sys
from selenium import webdriver
from bs4 import BeautifulSoup
import re
import pandas as pd
import numpy as np


def raspa_pagina(soup, tag_html, atributo, match_atributo, regex):
    data_soup = soup.find_all(tag_html, attrs={atributo, match_atributo})
    x = []
    for prov in (data_soup):
        _ = re.findall(regex, str(prov))
        if _ != []:
            if regex == 'rating bubble_(..)':
                x.append(int(_[0]) // 10)
            else:
                x.append(_[0])
        else:
            x.append("ERRO!!!")
    return x


hotel_inicio = int(sys.argv[1])
hotel_fim = int(sys.argv[2])
ano_limite = 2020

driver = webdriver.Chrome('/home/murilo/.chromedriver_linux64/chromedriver')
# link da lista de ganhadores
url = 'https://www.tripadvisor.com.br/TravelersChoice-Hotels-cTop-g294280'
driver.get(url)
soup = BeautifulSoup(driver.page_source, 'html.parser')
driver.quit()

#Dados de todos os hoteis
all_hotel = soup.find_all("div", attrs={"class", "winnerName"})

data = []
for pos, prov in enumerate(all_hotel):
    endereco = prov.find_all("a")[0]['href']
    cidade = re.search(f'target="_blank">(.*), Brasil<\/a>', str(prov.find_all("a")[1])).group(1)
    nome = re.search(r'target="_blank">[0-9\. ]*(.*)<\/a>', str(prov.find_all("a")[0])).group(1)
    data.append([nome, cidade, "https://www.tripadvisor.com.br" + endereco])

df_lista = pd.DataFrame(data, columns=['nome_hotel', 'cidade', 'link'])
links_hoteis = df_lista['link'].to_list()  # Lista com link de todos os hoteis

#Esse for cria lista de links das paginas para um hotel.
df_hotel = pd.DataFrame(columns=['ranking', 'nome_hotel', 'nota', 'titulo', 'texto', 'data', 'ano'])
for Seleciona_hotel in range(hotel_inicio, hotel_fim):
    pagina = 0
    
    driver = webdriver.Chrome('/home/murilo/.chromedriver_linux64/chromedriver')
    driver.get(links_hoteis[Seleciona_hotel]) # Pega o link de um dado Hotel
    soup_hotel = BeautifulSoup(driver.page_source, 'html.parser')
    driver.quit()

    nome_hotel = re.findall(r'HEADING">(.*)<\/h1>', str(soup_hotel.find_all("h1", attrs={"class", "QdLfr b d Pn"}))) * 5
    prox_page = soup_hotel.find_all("a", attrs={"class", "ui_button nav next primary"})
    link_split = prox_page[0]['href'].split('-or5-')

    link_hotel_paginas = []
    limite = 70000

    for num_coment_inf in range(0, limite, 5): #Cria a lista  o link das paginas
        if num_coment_inf == 0:
            link_hotel_paginas.append("https://www.tripadvisor.com.br" + link_split[0] + '-' + link_split[1])
        else:
            link_hotel_paginas.append(
        "https://www.tripadvisor.com.br" + link_split[0] + '-' + 'or' + str(num_coment_inf) + '-' + link_split[1])


    _data = ['2021']
    while int(_data[-1].split()[-1]) >= ano_limite and pagina < (limite - 1) / 5: #Aqui acontece a raspagem de fato.
        driver = webdriver.Chrome('/home/murilo/.chromedriver_linux64/chromedriver')
        driver.get(link_hotel_paginas[pagina])
        soup_hotel_paginas = BeautifulSoup(driver.page_source, 'html.parser')
        driver.quit()

        #Extraindoos dados
        _nota = raspa_pagina(soup_hotel_paginas, 'div', 'class', 'Hlmiy F1', 'rating bubble_(..)')  # NOTAS
        _texto = raspa_pagina(soup_hotel_paginas, 'q', 'class', 'QewHA H4 _a', '<span>(.*)<\/span>')  # TEXTO
        _titulo = raspa_pagina(soup_hotel_paginas, 'div', 'class', 'KgQgP MC _S b S6 H5 _a',
                               '<span><span>(.*)<\/span><\/span>')  # TITULO
        _data = raspa_pagina(soup_hotel_paginas, 'div', 'class', 'cRVSd',
                             'escreveu uma avaliação (.*)<\/span><\/div>')  # DATA
        _ano = []
        for i in _data:
            _ano.append(i[-4:])

        #Escrevendo no dataframe
        df_prov = pd.DataFrame(np.transpose(np.array([[Seleciona_hotel] * 5, nome_hotel, _nota, _titulo, _texto, _data, _ano])), \
                               columns=['ranking', 'nome_hotel', 'nota', 'titulo', 'texto', 'data', 'ano'])

        df_hotel = pd.concat([df_hotel, df_prov], ignore_index=True)

        print(nome_hotel[0], _data[-1])
        pagina += 1

        #Checkpoint
        if pagina % 5 == 0:
            df_hotel.to_csv(f'hoteis_de_{hotel_inicio}_{hotel_fim - 1}.csv', index=False)

        if _data[-1].split()[-1] not in ['2019', '2020', '2021', '2022']:
            _data[-1] = '2022'

df_hotel.to_csv(f'hoteis_de_{hotel_inicio}_{hotel_fim - 1}.csv', index=False)

