import streamlit as st
import time
import base64
from io import BytesIO
import json
import pandas as pd
from dependencies import get_xml_ctes, processa_ctes, get_clientes,formata_valor,get_xml_ctes_eventos,processa_evento_b64
from config_pag import get_logo, set_background
# Configurações da página
#------------------------
get_logo()
set_background()
#------------------------
st.set_page_config("LEITOR XML CTES",layout="wide")
st.title("Leitor de ctes emitidos")
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
            ctes=[]
            xmls = get_xml_ctes(cnpj,data_inicial,data_final)
            
            if isinstance(xmls, str): xmls = json.loads(xmls)
            xmls_nfe = xmls if isinstance(xmls,list) else xmls.get("data", [])      
            for xml_b64 in xmls_nfe:
                valor = 0
                xml_str = base64.b64decode(xml_b64).decode('utf-8')
                with BytesIO (xml_str.encode('utf-8')) as xml_file:
                    xml_processado = processa_ctes(xml_file)
                    ctes.extend(xml_processado)        
            ctes_df = pd.DataFrame(ctes,columns=["Chave","Data Emissão","Numero","Valor","ICMS","Aliquota ICMS"])
            eventos_list = []
            eventos = get_xml_ctes_eventos(cnpj,data_inicial,data_final)
            for x in eventos:
                elemento = processa_evento_b64(x)
                eventos_list.append(elemento)
            eventos_df = pd.DataFrame(eventos_list, columns=["Chave", "Evento"])
            if not eventos_df.empty:
                eventos_df = (
                    eventos_df.groupby("Chave", as_index=False)
                    .agg({
                        "Evento": lambda eventos: ",".join(f'"{evt}"' for evt in eventos if evt)
                    })
                )  
            if ctes_df.empty:
                st.warning("Nenhum XML encontrado para o período.")
                st.stop()
        df_merged = pd.merge(ctes_df,eventos_df, how="left", on="Chave")
        st.dataframe(df_merged)
        resumo1,resumo2,resumo3,resumo4 = st.columns(4)
        contagem = ctes_df["Chave"].count()
        valor_total = ctes_df["Valor"].sum()
        valor_icms = ctes_df["ICMS"].sum()
        with resumo1:
            st.metric("Quantia Notas", contagem) 
        with resumo2:
            st.metric("Somatório dos ct-es",formata_valor(valor_total))    
        with resumo3:
            st.metric("Somatório do ICMS",formata_valor(valor_icms))  
    parar = st.form_submit_button("Limpar")
    if parar:
        st.stop()

