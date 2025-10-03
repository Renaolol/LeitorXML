import streamlit as st
import time
import base64
from io import BytesIO
import json
import pandas as pd

from dependencies import get_xml_sieg, processa_xml, get_clientes
st.set_page_config("LEITOR XML",layout="wide")
st.title("Leitor de Notas de Entrada")
st.divider()
col1,col2,col3,col4 = st.columns([1,2,1,1])
clientes = get_clientes()
with col1:
    pesquisa = st.text_input("Pesquisar: ")
with col2:
    clientes_select = st.selectbox("Selecione o cliente", clientes)
with col3:
    data_inicial = st.date_input("Selecione a data inicial",format="DD/MM/YYYY")
with col4:
    data_final = st.date_input("Selecione a data final",format="DD/MM/YYYY")
cnpj = clientes_select[1]
buscar = st.button("Buscar")
if buscar:
    with st.spinner("Aguarde",show_time=True):
        todos_produtos=[]
        xmls = get_xml_sieg(cnpj,data_inicial,data_final)
        if isinstance(xmls, str): xmls = json.loads(xmls)
        xmls_nfe = xmls if isinstance(xmls,list) else xmls.get("data", [])      
        for xml_b64 in xmls_nfe:
            valor = 0
            xml_str = base64.b64decode(xml_b64).decode('utf-8')
            with BytesIO (xml_str.encode('utf-8')) as xml_file:
                xml_processado = processa_xml(xml_file)
                todos_produtos.extend(xml_processado)
        todos_produtos_df = pd.DataFrame(todos_produtos)
        st.dataframe(todos_produtos_df)                
st.divider()
