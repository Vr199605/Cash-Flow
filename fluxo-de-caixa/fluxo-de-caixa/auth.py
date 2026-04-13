import streamlit as st


def check_password() -> bool:
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if st.session_state["password_correct"]:
        return True

    st.markdown("""
        <style>
        .main { background-color: #0B0E14; }
        .stApp { display: flex; align-items: center; justify-content: center; }
        </style>
    """, unsafe_allow_html=True)

    with st.container():
        st.markdown(
            "<h1 style='text-align: center; color: #00D1FF;'>🔒 ACESSO RESTRITO</h1>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<p style='text-align: center; color: #94A3B8;'>Identifique-se para acessar os dados confidenciais</p>",
            unsafe_allow_html=True,
        )

        _, col, _ = st.columns([1, 2, 1])
        with col:
            user = st.text_input("Usuário", key="input_user")
            password = st.text_input("Senha", type="password", key="input_pass")
            if st.button("Entrar no Dashboard", use_container_width=True):
                if user == "admin" and password == "maldivas2026":
                    st.session_state["password_correct"] = True
                    st.rerun()
                else:
                    st.error("❌ Usuário ou senha incorretos")

    return False
