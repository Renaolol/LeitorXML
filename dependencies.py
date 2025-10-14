from dotenv import load_dotenv
import os
import requests
import json
import base64
from io import BytesIO
import xml.etree.ElementTree as ET
import psycopg2
import pandas as pd
from decimal import Decimal, InvalidOperation
import datetime as dt
load_dotenv()
# CONSTANTES
api_key_sieg = os.getenv("api_key_sieg")
ns = {'ns': 'http://www.portalfiscal.inf.br/nfe'}
ns_cte = {'ns_cte':'http://www.portalfiscal.inf.br/cte'}
#VARIAVEIS
def get_xml_sieg(cnpj, data_inicial, data_final):
    cont = 0
    resultados = []

    while True:
        url = f"https://api.sieg.com/BaixarXmls?api_key={api_key_sieg}"
        payload = {
            "XmlType": 1,
            "Take": 50,
            "Skip": (cont * 50),
            "DataEmissaoInicio": data_inicial.strftime("%Y-%m-%d"),
            "DataEmissaoFim": data_final.strftime("%Y-%m-%d"),
            "CnpjDest": cnpj,
            "Downloadevent": False,
        }
        headers = {"Content-Type": "application/json"}

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
        except requests.RequestException as exc:
            print(f"Erro na requisição: {exc}")
            break
        try:
            dados = response.json()
        except ValueError:
            dados = response.text.strip()

        if isinstance(dados, dict):
            itens = dados.get("Xmls") or dados.get("xmls") or []
        elif isinstance(dados, list):
            itens = dados
        elif isinstance(dados, str):
            itens = [item for item in dados.split(",") if item]
        else:
            print(f"Formato não suportado: {type(dados).__name__}")
            break

        if not itens:
            break

        resultados.extend(itens)
        cont += 1

        if len(itens) < 50:
            break

    return resultados   
def processa_xml(xml):
    tree = ET.parse(xml)
    root = tree.getroot()

    inf_nfe = root.find(".//ns:infNFe", ns)
    chave_nfe = inf_nfe.attrib.get("Id", "").replace("NFe", "") if inf_nfe is not None else ""

    numero_nota_elem = root.find(".//ns:ide/ns:nNF", ns).text
    numero_nota = int(numero_nota_elem) if numero_nota_elem is not None else 0
    emissor = root.find(".//ns:emit/ns:xNome", ns).text
    cnpj_emissor = root.find(".//ns:emit/ns:CNPJ", ns).text

    produtos = []
    total_icms_nota = 0
    total_notas_fiscais = 0
    total_quantidade_produtos = 0

    for item in root.findall(".//ns:det", ns):
        # Dados do Produto
        nome_produto = item.find(".//ns:prod/ns:xProd", ns).text
        quantidade = float(item.find(".//ns:prod/ns:qCom", ns).text)
        unidade_medida = item.find(".//ns:prod/ns:uCom", ns).text
        valor_unitario = float(item.find(".//ns:prod/ns:vUnCom", ns).text)
        valor_total = valor_unitario * quantidade

        # Verificação do CST
        cst_elem = item.find(".//ns:imposto/ns:ICMS//ns:CST", ns)
        cst = cst_elem.text if cst_elem is not None else "N/A"

        # Verificação da Base de Cálculo ICMS
        base_calculo_icms_elem = item.find(".//ns:imposto/ns:ICMS//ns:vBC", ns)
        base_calculo_icms = float(base_calculo_icms_elem.text) if base_calculo_icms_elem is not None else 0

        # Verificação da Alíquota ICMS
        aliquota_icms_elem = item.find(".//ns:imposto/ns:ICMS//ns:pICMS", ns)
        aliquota_icms = float(aliquota_icms_elem.text) if aliquota_icms_elem is not None else 0

        # Verificação do Valor ICMS
        valor_icms_elem = item.find(".//ns:imposto/ns:ICMS//ns:vICMS", ns)
        valor_icms = float(valor_icms_elem.text) if valor_icms_elem is not None else 0

        # Verificação do qBCMonoRet (Base de Cálculo ICMS Retido por Substituição)
        qBCMonoRet_elem = item.find(".//ns:imposto/ns:ICMS//ns:qBCMonoRet", ns)
        qBCMonoRet = float(qBCMonoRet_elem.text) if qBCMonoRet_elem is not None else 0

        # Verificação do adRemICMSRet (Adicional ICMS Retido)
        adRemICMSRet_elem = item.find(".//ns:imposto/ns:ICMS//ns:adRemICMSRet", ns)
        adRemICMSRet = float(adRemICMSRet_elem.text) if adRemICMSRet_elem is not None else 0

        # Verificação do vICMSMonoRet (Valor ICMS Retido por Substituição)
        vICMSMonoRet_elem = item.find(".//ns:imposto/ns:ICMS//ns:vICMSMonoRet", ns)
        vICMSMonoRet = float(vICMSMonoRet_elem.text) if vICMSMonoRet_elem is not None else 0

        # Cálculo da Aliq Vigente (1.12 se CST for 61, senão 0)
        aliq_vigente = 1.12 if cst == "61" else 0

        # Cálculo do Valor Correto (qBCMonoRet * Aliq Vigente)
        valor_correto = qBCMonoRet * aliq_vigente

        chave_elem = root.find(".//ns:infNFe", ns)
        chave_nfe = chave_elem.attrib.get('Id', '').replace('NFe', '') if chave_elem is not None else ''


        produtos.append({
            "CNPJ Emissor": cnpj_emissor,
            "Emissor": emissor,
            "Número NF": numero_nota,
            "Produto": nome_produto,
            "Quantidade": quantidade,
            "Unidade de Medida": unidade_medida,
            "Valor Unitário": valor_unitario,
            "Valor Total": valor_total,
            "CST": cst,
            "Base de Cálculo ICMS": base_calculo_icms,
            "Alíquota ICMS (%)": aliquota_icms,
            "Valor ICMS": valor_icms,
            "qBCMonoRet": qBCMonoRet,
            "adRemICMSRet": adRemICMSRet,
            "vICMSMonoRet": vICMSMonoRet,
            "Aliq Vigente": aliq_vigente,  # Adicionando Aliq Vigente
            "Valor Correto": valor_correto,  # Adicionando Valor Correto
            "Chave":chave_nfe,
        })

    return produtos
def get_clientes():
    conn = psycopg2.connect(
    host = "localhost",
    dbname="ConfrontadorXML",
    user="postgres",
    password="0176"
)
    cursor = conn.cursor()
    query="""
    SELECT razao_social, cnpj FROM clientes ORDER BY razao_social
"""
    cursor.execute(query, )
    rows=cursor.fetchall()
    clientes =[]
    for row in rows:
        cnpj = row[1]
        nome = row[0]
        clientes.append([nome,cnpj])
    cursor.close()
    conn.close()
    return clientes
def formata_valor(valor):
    if valor is None or (hasattr(valor, "__float__") and pd.isna(valor)):
        return "R$ 0,00"

    try:
        quantia = Decimal(str(valor))
    except (InvalidOperation, ValueError, TypeError):
        return "R$ 0,00"

    sinal = "-" if quantia < 0 else ""
    quantia = abs(quantia)

    bruto = f"{quantia:,.2f}"
    bruto = bruto.replace(",", "_").replace(".", ",").replace("_", ".")

    return f"{sinal}R$ {bruto}"
def get_xml_ctes(cnpj, data_inicial, data_final):
    cont = 0
    resultados = []

    while True:
        url = f"https://api.sieg.com/BaixarXmls?api_key={api_key_sieg}"
        payload = {
            "XmlType": 2,
            "Take": 50,
            "Skip": (cont * 50),
            "DataEmissaoInicio": data_inicial.strftime("%Y-%m-%d"),
            "DataEmissaoFim": data_final.strftime("%Y-%m-%d"),
            "CnpjEmit": cnpj,
            "Downloadevent": False,
        }
        headers = {"Content-Type": "application/json"}

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
        except requests.RequestException as exc:
            print(f"Erro na requisição: {exc}")
            break
        try:
            dados = response.json()
        except ValueError:
            dados = response.text.strip()

        if isinstance(dados, dict):
            itens = dados.get("Xmls") or dados.get("xmls") or []
        elif isinstance(dados, list):
            itens = dados
        elif isinstance(dados, str):
            itens = [item for item in dados.split(",") if item]
        else:
            print(f"Formato não suportado: {type(dados).__name__}")
            break

        if not itens:
            break

        resultados.extend(itens)
        cont += 1

        if len(itens) < 50:
            break

    return resultados
def processa_ctes(ctes):
    cte=[]
    tree = ET.parse(ctes)
    root = tree.getroot()

    chave_cte = root.find("./ns_cte:protCTe/ns_cte:infProt/ns_cte:chCTe",ns_cte).text
    num_cte = root.find(".//ns_cte:ide/ns_cte:nCT",ns_cte).text

    dt_emis_elem = root.find(".//ns_cte:ide/ns_cte:dhEmi", ns_cte)
    raw = dt_emis_elem.text if dt_emis_elem is not None else None

    if raw:
        dt_emis = dt.datetime.fromisoformat(raw).strftime("%d/%m/%Y")
    else:
        dt_emis = "N/A"

    valor_cte_elem = root.find(".//ns_cte:vPrest/ns_cte:vTPrest",ns_cte)
    valor_cte = float(valor_cte_elem.text) if valor_cte_elem is not None else 0
    icms_cte_elem = root.find(".//ns_cte:imp/ns_cte:ICMS//ns_cte:vICMS",ns_cte)
    icms_cte = float(icms_cte_elem.text) if icms_cte_elem is not None else 0
    aliq_icms_elem = root.find(".//ns_cte:imp/ns_cte:ICMS//ns_cte:pICMS",ns_cte)
    aliq_icms = float(aliq_icms_elem.text) if aliq_icms_elem is not None else 0
    cte.append([chave_cte,dt_emis,num_cte,valor_cte,icms_cte,aliq_icms])
    return cte
def get_xml_ctes_eventos(cnpj, data_inicial, data_final):
    cont = 0
    resultados = []

    while True:
        url = f"https://api.sieg.com/BaixarXmls?api_key={api_key_sieg}"
        payload = {
            "XmlType": 2,
            "Take": 50,
            "Skip": (cont * 50),
            "DataEmissaoInicio": data_inicial.strftime("%Y-%m-%d"),
            "DataEmissaoFim": data_final.strftime("%Y-%m-%d"),
            "CnpjEmit": cnpj,
            "Downloadevent": True,
        }
        headers = {"Content-Type": "application/json"}

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
        except requests.RequestException as exc:
            print(f"Erro na requisição: {exc}")
            break
        try:
            dados = response.json()
        except ValueError:
            dados = response.text.strip()

        if isinstance(dados, dict):
            itens = dados.get("Xmls") or dados.get("xmls") or []
        elif isinstance(dados, list):
            itens = dados
        elif isinstance(dados, str):
            itens = [item for item in dados.split(",") if item]
        else:
            print(f"Formato não suportado: {type(dados).__name__}")
            break

        if not itens:
            break

        resultados.extend(itens)
        cont += 1

        if len(itens) < 50:
            break
    return resultados
def processa_evento_b64(xml_b64):
    xml_str = base64.b64decode(xml_b64).decode('utf-8')
    with BytesIO (xml_str.encode('utf-8')) as xml_file:
        tree = ET.parse(xml_file)
    root = tree.getroot()
    eventos=[]
    chave_cte_elem = root.find(".//ns_cte:infEvento/ns_cte:chCTe",ns_cte)
    chave_cte = chave_cte_elem.text if chave_cte_elem is not None else ""

    evento_elem = root.find(".//ns_cte:infEvento/ns_cte:detEvento//ns_cte:descEvento",ns_cte)
    evento = evento_elem.text if evento_elem is not None else ""
    return chave_cte,evento


