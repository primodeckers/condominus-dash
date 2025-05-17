import streamlit as st
import hashlib
import yaml
import os
from pathlib import Path

def carregar_credenciais():
    """Carrega as credenciais do arquivo de configuração."""
    config_path = Path('config.yaml')
    if not config_path.exists():
        return None
    
    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)
        return config.get('credenciais')

def verificar_autenticacao():
    """Verifica se o usuário está autenticado."""
    if 'autenticado' not in st.session_state:
        st.session_state.autenticado = False
        st.session_state.usuario_atual = None
    
    if not st.session_state.autenticado:
        return mostrar_tela_login()
    
    return True

def aplicar_estilo_login():
    """Aplica estilos CSS personalizados para a tela de login."""
    st.markdown("""
        <style>
        .stForm {
            background-color: #ffffff;
            padding: 1.5rem;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            width: 600px;
            margin: 0 auto;
        }
        .stTextInput > div > div > input {
            border-radius: 5px;
            border: 1px solid #e0e0e0;
            padding: 0.5rem;
        }
        .stButton > button {
            width: 100%;
            background-color: #1E88E5;
            color: white;
            border: none;
            padding: 0.5rem;
            border-radius: 5px;
            font-weight: bold;
        }
        .stButton > button:hover {
            background-color: #1565C0;
        }
        h1 {
            text-align: center;
            color: #1E88E5;
            margin-bottom: 1.5rem;
        }
        div[data-testid="stForm"] {
            width: 300px !important;
            margin: 0 auto !important;
        }
        div[data-testid="stForm"] > div {
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        div[data-testid="InputInstructions"] > span:nth-child(1) {
            visibility: hidden;
        }
        </style>
    """, unsafe_allow_html=True)

def mostrar_tela_login():
    """Mostra a tela de login e processa a autenticação."""
    aplicar_estilo_login()
    
    st.title("🔐 Login")
    
    with st.form("login_form"):
        usuario = st.text_input("Usuário", placeholder="Digite seu usuário")
        senha = st.text_input("Senha", type="password", placeholder="Digite sua senha")
        submit = st.form_submit_button("Entrar")
        
        if submit:
            if autenticar_usuario(usuario, senha):
                st.session_state.autenticado = True
                st.session_state.usuario_atual = usuario
                st.rerun()
            else:
                st.error("Usuário ou senha inválidos!")
    
    return False

def autenticar_usuario(usuario, senha):
    """Autentica o usuário usando as credenciais fornecidas."""
    credenciais = carregar_credenciais()
    if not credenciais:
        return False
    
    # Hash da senha fornecida
    senha_hash = hashlib.sha256(senha.encode()).hexdigest()
    
    # Verifica se o usuário existe e se a senha está correta
    return (
        usuario in credenciais and 
        credenciais[usuario]['senha_hash'] == senha_hash
    )

def logout():
    """Realiza o logout do usuário."""
    st.session_state.autenticado = False
    st.session_state.usuario_atual = None
    st.rerun()

def obter_nome_usuario():
    """Retorna o nome do usuário atual."""
    if not st.session_state.usuario_atual:
        return None
    
    credenciais = carregar_credenciais()
    if not credenciais or st.session_state.usuario_atual not in credenciais:
        return None
    
    return credenciais[st.session_state.usuario_atual]['nome']

aplicar_estilo_login()  # Sempre aplica o CSS

if not verificar_autenticacao():
    st.stop()
