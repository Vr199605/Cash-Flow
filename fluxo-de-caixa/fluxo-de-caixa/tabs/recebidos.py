import streamlit as st


def render(df_rec):
    st.dataframe(df_rec, use_container_width=True, hide_index=True)
