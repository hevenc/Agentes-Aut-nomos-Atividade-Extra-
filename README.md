DataPilot CSV: Agente Autônomo para Análise de Dados

Este projeto apresenta um aplicativo web construído com Streamlit que utiliza um Agente de IA Autônomo (LangChain + Google Gemini) para realizar Análise Exploratória de Dados (EDA) de forma conversacional. O Agente é capaz de processar arquivos CSV, executar código Python em tempo real, gerar gráficos e fornecer conclusões estruturadas sobre os dados.

✨ Funcionalidades Principais
Agente ReAct Inteligente: Utiliza a arquitetura ReAct para raciocinar, planejar as ações e executar código Python de forma autônoma.

EDA Conversacional: Faça perguntas em linguagem natural sobre o seu CSV (ex: Quais são as medidas de tendência central (média, mediana)? ").

Visualização Dinâmica: Geração e exibição de gráficos interativos (Plotly) e estáticos (Matplotlib) diretamente no Streamlit.

Conclusões Estruturadas: Cada resposta do agente inclui uma seção clara de CONCLUSÕES, resumindo os achados e implicações da análise.

Memória: O agente mantém o histórico da conversa, permitindo análises encadeadas e refino de perguntas.

⚙️ Tecnologias Utilizadas
Componente

Tecnologia

Função

Interface

Streamlit

Criação rápida e responsiva da aplicação web.

Agente / LLM

Google Gemini (via langchain-google-genai)

Fornece a inteligência e o raciocínio central do agente.

Framework de Agentes

LangChain

Construção do Agente ReAct, ferramentas e memória conversacional.

Análise

Pandas, NumPy

Manipulação, limpeza e análise de DataFrames.

Visualização

Plotly, Matplotlib, Seaborn (indireto)

Geração de gráficos complexos para exibição.

Segurança

python-dotenv

Gerenciamento seguro da chave de API em ambiente local.

Dependência Pandas

tabulate

Necessário para o método df.to_markdown() (visualização da tabela).

🛠️ Configuração e Execução Local
1. Pré-requisitos
Certifique-se de ter o Python (3.9+) e o Git instalados em seu sistema.

2. Clonagem do Repositório
Clone o projeto para sua máquina local:

git clone [https://docs.github.com/pt/repositories/creating-and-managing-repositories/quickstart-for-repositories](https://docs.github.com/pt/repositories/creating-and-managing-repositories/quickstart-for-repositories)
cd DataPilot-CSV

3. Instalação de Dependências
Recomendamos sempre criar um ambiente virtual (venv) antes de instalar os pacotes:

# Cria o ambiente virtual
python -m venv venv

# Ativa o ambiente virtual (Linux/macOS)
source venv/bin/activate 

# Ativa o ambiente virtual (Windows)
.\venv\Scripts\activate 

# Instala as dependências listadas no requirements.txt
pip install -r requirements.txt

4. Configuração da Chave de API (Passo Crítico de Segurança)

Obtenha sua Chave: Crie sua chave de API no Google AI Studio.

Crie o arquivo .env: Na raiz do seu projeto (a mesma pasta onde está o main.py), crie um arquivo chamado .env.

Insira a Chave: Adicione sua chave neste arquivo no seguinte formato:

# Conteúdo do arquivo .env
GOOGLE_API_KEY="SUA_CHAVE_SECRETA_COMPLETA_AQUI"

🔔 O arquivo .gitignore deste projeto garante que o .env nunca seja enviado ao repositório público.

5. Execução do Aplicativo
Com o ambiente ativado e a chave configurada, execute a aplicação Streamlit:

streamlit run main.py

O aplicativo será aberto automaticamente no seu navegador, geralmente em http://localhost:8501/.

☁️ Deploy no Streamlit Cloud
Para implantar este aplicativo na nuvem:

Use o painel de Deploy do Streamlit Cloud (ou similar).

O sistema de deploy lerá o requirements.txt e instalará as dependências.

CONFIGURAÇÃO DE SECRETO: Você deve configurar a chave de API na seção "Secrets" da plataforma. Adicione a variável no formato TOML:

GOOGLE_API_KEY="SUA_CHAVE_SECRETA_AQUI"
