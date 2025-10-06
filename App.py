import streamlit as st
import time
import base64
from io import BytesIO
import json
import pandas as pd
from dependencies import get_xml_sieg, processa_xml, get_clientes,formata_valor
st.set_page_config("LEITOR XML",layout="wide")
st.title("Leitor de Notas de Entrada")
st.divider()
col1,col2,col3 = st.columns([2,0.5,0.5])
clientes = get_clientes()
with col1:
    clientes_select = st.selectbox("Selecione o cliente", clientes)
with col2:
    data_inicial = st.date_input("Selecione a data inicial",format="DD/MM/YYYY")
with col3:
    data_final = st.date_input("Selecione a data final",format="DD/MM/YYYY")
cnpj = clientes_select[1]

buscar = st.button("Buscar")
with st.form("Produtos"): 
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
            if todos_produtos_df.empty:
                st.warning("Nenhum XML encontrado para o período.")
                st.stop()
            if "Valor Correto" not in todos_produtos_df.columns:
                todos_produtos_df["Valor Correto"] = 0.0
        todos_produtos_df["Conferido"] = False
        todos_produtos_df["Valor Correto R$"]=todos_produtos_df["Valor Correto"].apply(formata_valor)
        #CheckBox para selecionar os que já foram conferidos
        st.data_editor(todos_produtos_df[["Número NF", "Produto", "Quantidade", "Valor Unitário", "Valor Total",
        "CST", "Base de Cálculo ICMS", "Alíquota ICMS (%)", "Valor ICMS",
        "qBCMonoRet", "adRemICMSRet", "vICMSMonoRet", "Aliq Vigente",
        "Valor Correto R$", "Conferido"]])
        quantia_notas = todos_produtos_df["Chave"].nunique()
        valor_notas = todos_produtos_df["Valor Total"].sum()
        valor_mono = todos_produtos_df["Valor Correto"].sum()
        valor_icms = todos_produtos_df["Valor ICMS"].sum()
        resumo1,resumo2,resumo3,resumo4 = st.columns(4)
        with resumo1:
            st.metric("Quantia Notas",quantia_notas) 
        with resumo2:
            st.metric("Somatório das Notas",formata_valor(valor_notas))    
        with resumo3:
            st.metric("Somatório do ICMS",formata_valor(valor_icms))
        with resumo4:
            st.metric("Somatório do ICMS Monofásico",formata_valor(valor_mono))     
    parar = st.form_submit_button("Parar")
    if parar:
        st.stop()
