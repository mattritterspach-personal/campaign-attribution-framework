import streamlit as st
from attribution import generate_sample_journeys, attribute, compare_models
st.title("Campaign Attribution Framework")
df = generate_sample_journeys()
st.write(df.head())
