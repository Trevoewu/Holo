from openai import OpenAI
import streamlit as st
import pandas as pd
import openai

from classes import get_primer, format_question, run_request
st.set_page_config(page_title='可视化模型', page_icon='🧠')
st.title("🧠可视化模型")
# List to hold datasets
if "datasets" not in st.session_state:
    datasets = {}
    # Preload datasets
    datasets["Week1"] = pd.read_csv(
        "static/1000taxidata/odddata/week1/oddata_20140803_train.txt")
    datasets["Week2"] = pd.read_csv(
        "static/1000taxidata/odddata/week2/oddata_20140810_train.txt")
    datasets["Week3"] = pd.read_csv(
        "static/1000taxidata/odddata/week3/oddata_20140818_train.txt")
    datasets["Week4"] = pd.read_csv(
        "static/1000taxidata/odddata/week4/oddata_20140824_train.txt")
    st.session_state["datasets"] = datasets
else:
    # use the list already loaded
    datasets = st.session_state["datasets"]
# api key
openai_key = st.secrets['OPENAI_API_KEY']
hf_key = st.secrets['HF_API_KEY']


if "model" not in st.session_state:
    st.session_state["model"] = "CodeLlama-34b-Instruct-hf"

# if "messages" not in st.session_state:
#     st.session_state.messages = []

if "messages" not in st.session_state or st.sidebar.button("清空对话记录"):
    st.session_state["messages"] = [
        {"role": "assistant", "content": "What would you like to visualise?"}]


# Add facility to upload a dataset
try:
    uploaded_file = st.file_uploader(
        ":computer: Load a CSV/TXT file:", type=['csv', 'txt'])
    index_no = 0
    if uploaded_file:
        # Read in the data, add it to the list of available datasets. Give it a nice name.
        file_name = uploaded_file.name[:-4].capitalize()
        datasets[file_name] = pd.read_csv(uploaded_file)
        # We want to default the radio button to the newly added dataset
        index_no = len(datasets)-1
except Exception as e:
    st.error("File failed to load. Please select a valid CSV/TXT file.")
    print("File failed to load.\n" + str(e))

with st.sidebar:
    chosen_dataset = st.selectbox(
        ":bar_chart: Data:", datasets.keys(), index=index_no)
    chosen_model = st.selectbox(
        ':brain: Model:',
        ['gpt-4', 'gpt-3.5-turbo', 'gpt-4o', 'CodeLlama-34b-Instruct-hf'],
    )
    st.session_state["model"] = chosen_model

# display history messages
for message in st.session_state.messages:
    if message['role'] == 'user':
        with st.chat_message('user'):
            st.markdown(message["content"])
    else:
        with st.chat_message('assistant'):
            plot_area = st.empty()
            try:
                plot_area.pyplot(exec(message['content']))
            except Exception as e:
                print('Not executable code')
                st.markdown(message['content'])
#
if prompt := st.chat_input(''):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        primer_desc, pimer_code = get_primer(
            datasets[chosen_dataset], 'datasets["' + chosen_dataset + '"]')
        # Format the question
        question_to_ask = format_question(
            primer_desc, pimer_code, prompt, st.session_state.model)
        # Run the question
        answer = ""
        answer = run_request(
            question_to_ask, st.session_state.model, key=openai_key, alt_key=hf_key)
        # the answer is the completed Python script so add to the beginning of the script to it.
        answer = pimer_code + answer
        plot_area = st.empty()
        try:
            plot_area.pyplot(exec(answer))
        except Exception as e:
            st.warning(e)
            # st.write(answer)
        st.expander('Code', expanded=False).code(answer)
        st.session_state.messages.append(
            {"role": "assistant", "content": answer})


with st.expander('Data', expanded=False):
    tab_list = st.tabs(datasets.keys())
    # Load up each tab with a dataset
    for dataset_num, tab in enumerate(tab_list):
        with tab:
            # Can't get the name of the tab! Can't index key list. So convert to list and index
            dataset_name = list(datasets.keys())[dataset_num]
            st.subheader(dataset_name)
            st.dataframe(datasets[dataset_name], hide_index=True)
