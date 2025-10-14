import streamlit as st
import pyodbc
import pandas as pd
from dependencies import buscar_dados
from config_pag import get_logo, set_background
# Configurações da página
#------------------------
get_logo()
set_background()
#------------------------
st.title("Consulta ICMS Monofásico",help="Faz a busca no Banco de dados da Domínio")
st.divider()
col1,col2,col3 = st.columns(3)
with col1:
    codigo = st.text_input("Insira o código da empresa",width=300)
with col2:    
    data_inicial = st.date_input("Insira a data inicial",width=300,value="2025-09-01",format="DD/MM/YYYY")
with col3:    
    data_final = st.date_input("Insira a data final",width=300,value="2025-09-30",format="DD/MM/YYYY")
buscar = st.button("Buscar")
if buscar:
    monofasico= buscar_dados(codigo,data_inicial,data_final)
    monofasico_df = pd.DataFrame(monofasico,columns=(['Código da Empresa', 'Nome da Empresa', 'Número da Nota', 'Data de Emissão', 'Código de Acumulação', 'Base de Cálculo', 'Alíquota Fixa', 'Valor do ICMS Monofásico', 'Status do Cód. Ent.']))
    st.dataframe(monofasico_df)