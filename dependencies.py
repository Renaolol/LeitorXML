from dotenv import load_dotenv
import os
import requests
import json
import base64
from io import BytesIO
import xml.etree.ElementTree as ET
load_dotenv()
api_key_sieg = os.getenv("api_key_sieg")
ns = {'ns': 'http://www.portalfiscal.inf.br/nfe'}
def get_xml_sieg():
    try:
        url=f"https://api.sieg.com/BaixarXmls?api_key={api_key_sieg}"
        payload = {
        "XmlType": 1,
        "Take": 0,
        "Skip": 0,
        "DataEmissaoInicio": "2025-09-01",
        "DataEmissaoFim": "2025-09-01",
        "CnpjDest": "09271377000150",
        "Downloadevent": False
            }
        headers = {"Content-Type": "application/json"}
        response = requests.post(url, headers=headers, json = payload)
        if response.status_code == 200:
            return response.json()
        else:
            print("Erro na API: ", response.status_code, response.text)    
    except:
        print(f"Erro")
    return []    
def processa_xml(xml):
    tree = ET.parse(xml)
    root = tree.getroot()

    inf_nfe = root.find(".//ns:infNFe", ns)
    chave_nfe = inf_nfe.attrib.get("Id", "").replace("NFe", "") if inf_nfe is not None else ""

    numero_nota = root.find(".//ns:ide/ns:nNF", ns).text
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

    return produtos, total_icms_nota, total_notas_fiscais, total_quantidade_produtos

xmls = get_xml_sieg()
if isinstance(xmls, str): xmls = json.loads(xmls)
xmls_nfe = xmls if isinstance(xmls,list) else xmls.get("data", [])
      
for xml_b64 in xmls_nfe:
    valor = 0
    try:
        try:
            xml_str = base64.b64decode(xml_b64).decode('utf-8')
        except Exception as e:
           print(e)    
        with BytesIO (xml_str.encode('utf-8')) as xml_file:
            print("processando")
            processa_xml(xml_file)
    except:
        break