from langchain.agents import AgentType
from langchain_experimental.agents import create_pandas_dataframe_agent
from langchain.callbacks import StreamlitCallbackHandler
from langchain.chat_models import ChatOpenAI
import streamlit as st
import pandas as pd
import os
st.set_page_config(
    page_title="LangChain: SQL模型", page_icon="🦜"
)
st.title("🦜 LangChain: SQL模型")

file_formats = {
    "csv": pd.read_csv,
    "txt": pd.read_csv,
    "xls": pd.read_excel,
    "xlsx": pd.read_excel,
    "xlsm": pd.read_excel,
    "xlsb": pd.read_excel,
}

# List to hold datasets
if "datasets" not in st.session_state:
    datasets = {}
    # Preload datasets
    datasets["Movies"] = pd.read_csv("static/movies.csv")
    datasets["Housing"] = pd.read_csv("static/housing.csv")
    datasets["Cars"] = pd.read_csv("static/cars.csv")
    datasets["Colleges"] = pd.read_csv("static/colleges.csv")
    datasets["Customers & Products"] = pd.read_csv(
        "static/customers_and_products_contacts.csv")
    datasets["Department Store"] = pd.read_csv("static/department_store.csv")
    datasets["Energy Production"] = pd.read_csv("static/energy_production.csv")
    st.session_state["datasets"] = datasets
else:
    # use the list already loaded
    datasets = st.session_state["datasets"]


@st.cache_data(ttl="2h")
def load_data(uploaded_file):
    try:
        ext = os.path.splitext(uploaded_file.name)[1][1:].lower()
    except:
        ext = uploaded_file.split(".")[-1]
    if ext in file_formats:
        return file_formats[ext](uploaded_file)
    else:
        st.error(f"Unsupported file format: {ext}")
        return None


# Add facility to upload a dataset
try:
    uploaded_file = st.file_uploader(
        ":computer: Load a tabular file:", type=['csv', 'txt', 'xls', 'xlsx', 'xlsm', 'xlsb'])
    index_no = 0
    if uploaded_file:
        # Read in the data, add it to the list of available datasets. Give it a nice name.
        file_name = uploaded_file.name[:-4].capitalize()
        datasets[file_name] = load_data(uploaded_file)
        # We want to default the radio button to the newly added dataset
        index_no = len(datasets)-1
except Exception as e:
    st.error("File failed to load. Please select a valid CSV/TXT file.")
    print("File failed to load.\n" + str(e))

# load openai api key
with st.sidebar:
    openai_api_key = st.text_input("OpenAI API Key", type="password")
    if not openai_api_key:
        openai_api_key = st.secrets['OPENAI_API_KEY']
    chosen_dataset = st.selectbox(
        ":bar_chart: Data:", datasets.keys(), index=index_no)
    chosen_model = st.selectbox(
        ':brain: Model:',
        ['gpt-3.5-turbo', 'gpt-4'],
    )
    st.session_state["model"] = chosen_model


if "messages" not in st.session_state or st.sidebar.button("Clear history"):
    st.session_state["messages"] = [
        {"role": "assistant", "content": "How can I help you?"}]

# dispaly chat history
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input():
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    if not openai_api_key:
        st.info("please input your openai api token.")
        st.stop()

    llm = ChatOpenAI(
        temperature=0, model=chosen_model, openai_api_key=openai_api_key, streaming=True
    )

    pandas_df_agent = create_pandas_dataframe_agent(
        llm,
        datasets[chosen_dataset],
        verbose=True,
        agent_type=AgentType.OPENAI_FUNCTIONS,
        handle_parsing_errors=True,
    )

    with st.chat_message("assistant"):
        # st_cb = StreamlitCallbackHandler(
        #     st.container(), expand_new_thoughts=False)
        # response = pandas_df_agent.run(
        #     st.session_state.messages, callbacks=[st_cb])
        response = pandas_df_agent.run(
            st.session_state.messages)
        st.session_state.messages.append(
            {"role": "assistant", "content": response})
        st.write(response)

with st.expander('Data', expanded=False):
    tab_list = st.tabs(datasets.keys())
    # Load up each tab with a dataset
    for dataset_num, tab in enumerate(tab_list):
        with tab:
            # Can't get the name of the tab! Can't index key list. So convert to list and index
            dataset_name = list(datasets.keys())[dataset_num]
            st.subheader(dataset_name)
            st.dataframe(datasets[dataset_name], hide_index=True)
