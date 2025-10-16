import streamlit as st
import pandas as pd
from dependencies import processa_xml_nfse,formata_valor
from config_pag import set_background, get_ico, get_logo
set_background()
get_logo()
st.set_page_config("LEITOR XML NFSE",layout="wide",page_icon=get_ico())
st.title("Leitor de XML de NFSE padrão nacional")
xmls = st.file_uploader("Insira os XMLs",accept_multiple_files=True)
lista = []
for xml in xmls:
    lista.append(processa_xml_nfse(xml))
lista_df = pd.DataFrame(lista,columns=["Número","Chave","Valor Total","Desconto","IR","INSS","Contrib Social","RPS","PIS","COFINS","ISS RETIDO"])
iss_retido = lista_df["ISS RETIDO"].sum()
st.dataframe(lista_df) 
st.metric("Soma de ISS Retido",formata_valor(iss_retido))