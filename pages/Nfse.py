import streamlit as st
import pandas as pd
from dependencies import processa_xml_nfse,formata_valor, cria_registro_1000, cria_registro_1020,cria_registro_1030
from config_pag import set_background, get_ico, get_logo
#Configurações da página
set_background()
get_logo()
st.set_page_config("LEITOR XML NFSE",layout="wide",page_icon=get_ico())
st.title("Leitor de XML de NFSE padrão nacional")

xmls = st.file_uploader("Insira os XMLs",accept_multiple_files=True)
#Criação da lista que será preenchida
lista = []
for xml in xmls:
    lista.append(processa_xml_nfse(xml))

#Criação do DataFrame a partir da lista   
lista_df = pd.DataFrame(lista,columns=["Número","Chave","Valor Total","Desconto","IR","INSS","Contrib Social","RPS","PIS",
                                       "COFINS","ISS RETIDO","DATA","CNPJ EMISSOR","ALIQUOTA","QUANTIDADE","VALOR UNITARIO"])
iss_retido = lista_df["ISS RETIDO"].sum()
st.dataframe(lista_df) 
st.metric("Soma de ISS Retido",formata_valor(iss_retido))

exportar = st.button("Exportar Domínio")
if exportar:
    registro=[]
    for x in lista:
        registro.append([cria_registro_1000(x[12],x[0],x[11],x[2],x[1]),cria_registro_1020(x[2],x[13],x[10]),
                         cria_registro_1030(x[14],x[15],x[12],x[13],x[10])])
    st.write (registro)       