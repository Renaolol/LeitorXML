# LeitorXML

Aplicacao Streamlit criada para apoiar equipes fiscais na leitura, conciliacao e analise de arquivos XML de NF-e, CT-e, NFSe e nos cruzamentos de ICMS monofasico com dados internos. O projeto centraliza diferentes rotinas em uma unica interface web leve, acessivel via navegador.

## Visao geral
- Interface principal em `App.py` (multi-page Streamlit) com paginas adicionais em `pages/`.
- Integracao com a API Sieg para baixar XMLs de NF-e de entrada e CT-e emitidos.
- Upload manual de XMLs de NFSe padrao nacional para consolidacao de tributos retidos.
- Consulta direta ao banco Dominio por meio de DSN ODBC para validar informacoes de ICMS monofasico.
- Camada de utilitarios em `dependencies.py` que encapsula chamadas de API, parsers de XML, formatacoes e acessos a banco de dados.

## Principais paginas do app
- **Leitor de Notas de Entrada (App.py)**: Seleciona cliente, intervalo de datas e baixa XMLs de NF-e via API Sieg. Mostra tabela editavel com produtos, valores tributarios e soma de indicadores chave.
- **Leitor de CT-e emitidos (`pages/Ctes.py`)**: Lista CT-es do periodo, consolida eventos associados e apresenta metricas de volume e ICMS.
- **Leitor de NFSe (`pages/Nfse.py`)**: Realiza upload de multiplos XMLs e resume valores retidos (ISS, PIS, COFINS, IR, INSS, etc.).
- **Consulta ICMS Monofasico (`pages/Mono.py`)**: Busca dados no banco Dominio via DSN `ContabilPBI` para avaliar configuracoes e valores de ICMS monofasico por empresa.

## Arquitetura e arquivos relevantes
- `App.py`: pagina inicial (NF-e) e orquestracao da aplicacao.
- `pages/`: paginas adicionais reconhecidas automaticamente pelo Streamlit.
- `dependencies.py`: funcoes de integracao (API Sieg, PostgreSQL, ODBC), parsing de XML e utilitarios de formatacao.
- `config_pag.py`: funcoes visuais (logo, icone e plano de fundo).
- `fundo.png`, `horizontal4.png`, `icone.ico`: recursos grafico-visuais carregados pelo app.
- `.env`: arquivo local (nao versionado publicamente) contendo credenciais sensiveis, como a API key Sieg.

## Requisitos de ambiente
### Software
- Python 3.10 ou superior.
- PostgreSQL acessivel com base `ConfrontadorXML` e usuario com permissao de leitura (ajuste credenciais em `dependencies.py` caso necessario).
- Fonte de dados Dominio acessivel via DSN ODBC chamado `SuaConexão` (Windows). Certifique-se de que o driver ODBC adequado esteja instalado e configurado.
- Chave valida para a API Sieg com permissao de download de XMLs.

### Bibliotecas Python
As principais dependencias sao:
`streamlit`, `pandas`, `python-dotenv`, `requests`, `psycopg2-binary`, `pyodbc`.

Instale-as (de preferencia dentro de um ambiente virtual) com:

```bash
pip install streamlit pandas python-dotenv requests psycopg2-binary pyodbc
```

## Preparando o projeto
1. Clone ou compacte o repositorio em sua maquina.
2. (Opcional, mas recomendado) Crie e ative um ambiente virtual:
   ```bash
   python -m venv .venv
   # Windows PowerShell
   .\.venv\Scripts\Activate.ps1
   ```
3. Instale as dependencias Python conforme listado acima.
4. Configure as integracoes externas (API, bancos de dados e DSN).

## Configuracao de variaveis de ambiente
O aplicativo carrega variaveis definidas no arquivo `.env` (via `python-dotenv`). Crie ou ajuste o arquivo com o formato:

```
api_key_sieg=SUACHAVEAQUI
```

Mantenha esse arquivo fora do controle de versao para proteger dados sensiveis.

## Executando a aplicacao
1. Certifique-se de que todas as dependencias estejam instaladas e que o `.env` esteja configurado.
2. Dentro da raiz do projeto, execute:
   ```bash
   streamlit run App.py
   ```
3. O Streamlit iniciara um servidor local (por padrao em `http://localhost:8501`). Abra o link indicado no terminal em seu navegador.

## Uso das funcionalidades
- **NF-e de entrada**: selecione cliente (nome + CNPJ obtidos do PostgreSQL), defina data inicial e final e clique em **Buscar**. O app baixa e processa os XMLs, exibe produtos e totais (valor das notas, ICMS, ICMS monofasico) e permite marcar itens conferidos.
- **CT-e emitidos**: com cliente e periodo definidos, baixa os XMLs e eventos via API Sieg, agrupa eventos por chave e mostra metricas agregadas.
- **NFSe padrao nacional**: utilize o uploader para adicionar um ou mais arquivos XML. O app converte os dados em tabela e calcula automaticamente o somatorio do ISS retido.
- **ICMS Monofasico**: informe o codigo da empresa e o periodo. A aplicacao consulta a base Dominiodominio (via DSN) e retorna colunas com status do cadastro e valores apurados.

## Resolucao de problemas
- Erros de conexao na API Sieg: confirme se a chave (`api_key_sieg`) e valida e se o servico esta acessivel a partir da rede local.
- Falha ao listar clientes: valide a conexao PostgreSQL definida em `dependencies.py` (host, base, usuario, senha).
- Erros com `pyodbc`: verifique se o DSN `SuaConexão` existe no Painel de Controle ODBC (64 bits) e se o driver correto esta instalado.
- Ausencia de imagens ou icone: confirme a presenca de `fundo.png`, `horizontal4.png` e `icone.ico` na raiz; o app exibe um aviso caso o plano de fundo nao seja encontrado.

## Contribuicao
Ajude mantendo credenciais fora do repositorio, escrevendo codigo legivel dentro do padrao existente e atualizando este README sempre que novas dependencias ou rotinas forem adicionadas.
