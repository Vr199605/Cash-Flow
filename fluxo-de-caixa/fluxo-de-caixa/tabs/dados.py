import streamlit as st


def render(df):
    st.dataframe(df, use_container_width=True, hide_index=True)
