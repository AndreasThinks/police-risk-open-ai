import streamlit as st
import pandas as pd
import os
from police_risk_open_ai.llm import *
from dotenv import load_dotenv
load_dotenv()

EMBEDDING_URL= os.getenv("EMBEDDING_URL")

st.title('Missing Risk Scanner')

@st.cache_data
def load_data():
    data = pd.read_parquet(EMBEDDING_URL)
    return data

# Create a text element and let the reader know the data is loading.
data_load_state = st.text('Loading data...')
# Load 10,000 rows of data into the dataframe.
data = load_data()
# Notify the reader that the data was successfully loaded.
data_load_state.text("Done! (using st.cache_data)")

risk_prompt = st.text_area("What do you know so far?")

if st.button("Evaluate"):
    risk_answer, risk_context = machine_risk_assessment(risk_prompt, data, debug=True)
    st.subheader(risk_answer)
    st.caption(risk_context)
else:
    st.write('Enter key details and click evaluate to begin.')