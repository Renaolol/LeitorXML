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

buscar = st.form("Buscar")
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
        
        colunas_visiveis = [
        "Número NF", "Produto", "Quantidade", "Valor Unitário", "Valor Total",
        "CST", "Base de Cálculo ICMS", "Alíquota ICMS (%)", "Valor ICMS",
        "qBCMonoRet", "adRemICMSRet", "vICMSMonoRet", "Aliq Vigente",
        "Valor Correto R$", "Conferido",
        ]
        #CheckBox para selecionar os que já foram conferidos
        if "Valor Correto R$" not in todos_produtos_df.columns:
            todos_produtos_df["Valor Correto R$"] = 0        
        todos_produtos_df["Valor Correto R$"] = todos_produtos_df["Valor Correto"].apply(formata_valor)
        if "produtos_cache" not in st.session_state:
            st.session_state["produtos_cache"] = todos_produtos_df.assign(Conferido=False)
        else:
            cache = todos_produtos_df.assign(Conferido=False)
            if "Conferido" in st.session_state["produtos_cache"]:
                cache["Conferido"] = st.session_state["produtos_cache"]["Conferido"].reindex(
                    cache.index, fill_value=False
                )
            st.session_state["produtos_cache"] = cache
        todos_produtos_df["Conferido"] = False


        editor_df = st.data_editor(
            st.session_state["produtos_cache"][colunas_visiveis],
            column_config={
                "Conferido": st.column_config.CheckboxColumn("Conferido", default=False)
            },
            disabled=[
                "Número NF", "Produto", "Quantidade", "Valor Unitário", "Valor Total",
                "CST", "Base de Cálculo ICMS", "Alíquota ICMS (%)", "Valor ICMS",
                "qBCMonoRet", "adRemICMSRet", "vICMSMonoRet", "Aliq Vigente", "Valor Correto R$"
            ],
            hide_index=True,
        )

        st.session_state["produtos_cache"]["Conferido"] = editor_df["Conferido"]
        todos_produtos_df["Conferido"] = editor_df["Conferido"]
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
    st.divider()
    st.form_submit_button("")
