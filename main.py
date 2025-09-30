# --- Importar as bibliotecas --- #
import numpy as np
import pandas as pd
import altair as alt
import streamlit as st
import plotly.express as px
import matplotlib.pyplot as plt
import os
import io
from dotenv import load_dotenv

# --- Importações da LangChain e Google/Groq --- #
from langchain_groq import ChatGroq
from langchain.agents import Tool, AgentExecutor, create_react_agent
from langchain.globals import set_debug
from langchain_core.prompts import PromptTemplate
from langchain_experimental.tools import PythonAstREPLTool
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.memory import ConversationBufferMemory
from typing import Type

set_debug(False)  # Desativado para não poluir o output no Streamlit

# Carrega as variáveis de ambiente do arquivo .env (arquivo com a chave de API)
load_dotenv()

# --- Configurações iniciais --- #
st.set_page_config(
    page_title="DataPilot CSV",
    layout="wide",
    # Adicionando a configuração de tema aqui:
    initial_sidebar_state="auto",
    menu_items=None,
    # Configurando o tema
    page_icon="🤖"
)

# --- Estilização do Título  --- #
st.markdown(
    """
    <style>
    /* 1. Centraliza o Título e o subtítulo (H1, H2) em toda a aplicação */
    div.stApp > header {
        text-align: center;
    }

    /* 2. Estiliza a cor e o tamanho do H1 (o título principal) */
    h1 {
        color: #9933FF; /* Roxo Profundo */
        font-size: 2.5em; 
        text-align: center; /* Centraliza o texto dentro do H1 */
    }

    /* 3. Centraliza a div que contém o título  */
    [data-testid="stAppViewContainer"] > div > section > div {
        display: flex;
        flex-direction: column;
        align-items: center;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title('DataPilot CSV')


# --- Funções Auxiliares para Gráficos --- #

# Esta função permite que o agente Python gere código de plotagem e a captura (e exibição) no Streamlit.
# O código gerado pelo agente DEVE usar `st_plot_capture()`
def st_plot_capture(plot_type, code_to_exec):
    """Executa o código de plotagem e exibe o gráfico no Streamlit."""
    try:
        # Cria um buffer para capturar a saída padrão
        buffer = io.StringIO()

        # Executa o código Python
        exec(code_to_exec, {'df': st.session_state.df_upload,
                            'px': px,
                            'plt': plt,
                            'st': st,
                            'st_plot_capture': st_plot_capture,
                            'np': np,
                            'pd': pd},
             {'output_buffer': buffer})

        # Captura o gráfico, se for Matplotlib (plt)
        if plot_type == 'matplotlib':
            fig = plt.gcf()
            st.pyplot(fig)
            plt.close(fig)

        # Captura o gráfico, se for Plotly (px)
        elif plot_type == 'plotly':
            # O código Plotly deve criar uma variável `fig` e usar `st.plotly_chart(fig)`
            # ou simplesmente ser um código Plotly que o LLM sabe renderizar.
            pass  # A execução direta no `exec` já deve ter chamado st.plotly_chart()

        return f"Gráfico do tipo {plot_type} gerado e exibido com sucesso."

    except Exception as e:
        return f"Erro ao gerar o gráfico: {e}. Verifique se o código gerado está correto."


# --- Classe do Agente --- #
class AgenteDataFrame:
    def __init__(self, llm: Type[BaseChatModel], df: pd.DataFrame, memory: ConversationBufferMemory) -> None:
        self.__df = df
        self.__llm = llm
        self.__memory = memory  # Adicionando memória (obrigatória na atividade)

    @property
    def ferramentas(self):
        # A ferramenta Python agora tem acesso às bibliotecas de plotagem e à função de captura
        python_globals = {
            "df": self.__df,
            "px": px,
            "plt": plt,
            "np": np,
            "pd": pd,
            "st": st,  # Dando acesso ao Streamlit para exibir gráficos Plotly/Matplotlib
        }

        # Ferramenta para execução de código Python com acesso ao DataFrame (df)
        python_tool = PythonAstREPLTool(
            locals=python_globals,
            name="Códigos Python para Análise e Gráficos",
            description="""
            Utilize esta ferramenta sempre que o usuário solicitar cálculos, consultas, transformações ou GERAÇÃO DE GRÁFICOS
            (histogramas, boxplots, dispersão, barras, etc.).
            Use Plotly Express (px) para gráficos interativos. Ex: `fig = px.histogram(df, x='coluna'); st.plotly_chart(fig)`.
            Use Matplotlib (plt) para gráficos estáticos. Ex: `plt.figure(figsize=(10,5)); plt.hist(df['coluna']); st.pyplot()`.
            Retorne SEMPRE a resposta final em português após a análise.
            """
        )

        return [python_tool]

    @property
    def react_prompt(self):
        # Cria um buffer para capturar a saída de df.info()
        info_buffer = io.StringIO()

        # Chama df.info() e direciona sua saída para o buffer
        # df.info() retorna None, mas preenche info_buffer
        self.__df.info(buf=info_buffer)

        # Concatena o head formatado com o conteúdo capturado do buffer
        df_info = self.__df.head().to_markdown() + "\n\n" + info_buffer.getvalue()

        return PromptTemplate(
            input_variables=["input", "agent_scratchpad", "tools", "tool_names", "history"],
            partial_variables={"df_info": df_info},
            template="""
            Você é um assistente de Análise Exploratória de Dados (EDA) que responde SEMPRE em português.

            Você tem acesso a um DataFrame pandas chamado `df`.
            Aqui estão as primeiras linhas e a descrição dos tipos de dados do DataFrame:
            {df_info}

            Seu objetivo principal é responder perguntas do usuário, gerar gráficos (usando Plotly/Matplotlib e funções st.plotly_chart/st.pyplot) 
            e, CRITICAMENTE, fornecer uma seção de **CONCLUSÕES** após a análise.
            As conclusões devem resumir os achados e implicações do que foi analisado, utilizando seu histórico de conversas.

            Histórico da Conversa:
            {history}

            Ferramentas disponíveis:
            {tools}

            Use o seguinte formato de raciocínio ReAct:

            Question: pergunta do usuário
            Thought: raciocínio do que fazer (sempre em português)
            Action: nome da ferramenta, uma das [{tool_names}]
            Action Input: entrada para a ação (código Python)
            Observation: resultado da ação
            ...(repita Thought/Action/... quantas vezes quiser)
            Thought: Agora eu sei a resposta final e as conclusões a tirar
            Final Answer: Resposta completa, incluindo gráficos gerados, resultados e, o mais importante, uma seção clara de **CONCLUSÕES:**

            Comece!

            Question: {input}
            Thought: {agent_scratchpad}
            """
        )

    def executar(self, pergunta: str) -> str:
        agente = create_react_agent(llm=self.__llm, tools=self.ferramentas, prompt=self.react_prompt)
        # O executor agora recebe a memória
        executor = AgentExecutor(
            agent=agente,
            tools=self.ferramentas,
            handle_parsing_errors=True,
            memory=self.__memory,
            verbose=True,  # Para ver o ReAct completo
            max_iterations=100,
            max_execution_time=300.0
        )
        # A memória é passada como parte do invoke, e o executor a gerencia
        resposta = executor.invoke({"input": pergunta})
        return resposta["output"]


# --- Layout Streamlit --- #
col1, col2 = st.columns([1, 4])

with col1:
    upload = st.file_uploader("", type="csv")

    # Inicializa ou carrega o DataFrame e o Histórico de Chat
    if 'df_upload' not in st.session_state:
        st.session_state.df_upload = None
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'memory' not in st.session_state:
        st.session_state.memory = ConversationBufferMemory(memory_key="history", return_messages=False)

    if upload is not None and st.session_state.df_upload is None or (
            upload is not None and upload.name != st.session_state.upload_name):
        try:
            df_upload = pd.read_csv(upload)
            st.session_state.df_upload = df_upload
            st.session_state.upload_name = upload.name

            # Resetar o histórico e a memória ao carregar um novo arquivo
            st.session_state.chat_history = []
            st.session_state.memory = ConversationBufferMemory(memory_key="history", return_messages=False)

            st.success(f"Arquivo **{upload.name}** carregado com sucesso!")
        except Exception as e:
            st.error(f"Erro ao carregar o CSV: {e}")
            st.session_state.df_upload = None

    if st.session_state.df_upload is not None:
        st.write(f"🧾 Primeiras linhas do arquivo: **{st.session_state.upload_name}**")
        st.dataframe(st.session_state.df_upload.head())

with col2:
    st.subheader("🤖 Converse com a IA")

    # Exibe histórico do chat (Com Destaque para Conclusões)
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            conteudo = msg["content"]
            # Verifica se há a seção de conclusões (o agente usa negrito **)
            if "**CONCLUSÕES:**" in conteudo:
                # Separa o conteúdo principal das conclusões
                partes = conteudo.split("**CONCLUSÕES:**", 1)
                st.markdown(partes[0])  # Conteúdo principal e raciocínio

                # Exibe as Conclusões em um bloco de destaque (st.info)
                st.info(f"**CONCLUSÕES:**{partes[1]}")
            else:
                st.markdown(conteudo)

    user_input = st.chat_input("Digite sua pergunta...")

    # Tenta pegar a chave da variável de ambiente
    google_api_key = os.getenv("GOOGLE_API_KEY", "")

    if not google_api_key:
        st.warning("⚠️ Chave de API do Gemini não encontrada. Por favor, defina a variável de ambiente GOOGLE_API_KEY.")

    # Instancia LLM Gemini (somente se a chave existir)
    if google_api_key:
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-preview-05-20",
            google_api_key=google_api_key
        )
    else:
        llm = None

    if user_input and st.session_state.df_upload is not None and llm is not None:
        # Salva pergunta no histórico
        st.session_state.chat_history.append({"role": "user", "content": user_input})

        # Exibe a pergunta na interface
        with st.chat_message("user"):
            st.markdown(user_input)

        # Cria o agente com df e memória
        agente = AgenteDataFrame(llm=llm, df=st.session_state.df_upload, memory=st.session_state.memory)

        with st.spinner("Pensando e analisando..."):
            # O executor gerencia a memória internamente
            resposta = agente.executar(user_input)

            # Salva resposta no histórico
            st.session_state.chat_history.append({"role": "assistant", "content": resposta})

            # Exibe resposta (Com Destaque para Conclusões)
            with st.chat_message("assistant"):
                # Aplica o mesmo destaque de CONCLUSÕES
                if "**CONCLUSÕES:**" in resposta:
                    partes = resposta.split("**CONCLUSÕES:**", 1)
                    st.markdown(partes[0])
                    st.info(f"**CONCLUSÕES:**{partes[1]}")
                else:
                    st.markdown(resposta)

    elif user_input and st.session_state.df_upload is None:
        st.warning("⚠️ Por favor, envie um CSV em **Browse files**, antes de fazer perguntas.")








