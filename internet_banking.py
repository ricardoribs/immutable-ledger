import streamlit as st
import requests
from uuid import uuid4
import time

# ================= CONFIG =================
st.set_page_config(
    page_title="LuisBank | Internet Banking",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

API_URL = "http://localhost:8000/ledger"

# ================= CSS (LUISBANK MODE) =================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Arial:wght@400;600;700&display=swap');

html, body, [class*="css"] {
    font-family: Arial, sans-serif;
    background-color: #f4f6f8;
}

header[data-testid="stHeader"] {
    background-color: #0b4f2e;
}

#MainMenu, footer { visibility: hidden; }

/* HEADER */
.top-bar {
    background-color: #0f6b3e;
    padding: 10px 20px;
    color: white;
    font-weight: bold;
}

/* SIDEBAR */
.sidebar-box {
    background-color: #ffffff;
    padding: 15px;
    border: 1px solid #dcdcdc;
    font-size: 14px;
}

/* CONTENT BOX */
.content-box {
    background-color: white;
    border: 1px solid #dcdcdc;
    padding: 20px;
    margin-bottom: 15px;
}

.section-title {
    font-weight: bold;
    border-bottom: 2px solid #0f6b3e;
    padding-bottom: 5px;
    margin-bottom: 10px;
}

/* BUTTONS */
button {
    background-color: #0f6b3e !important;
    color: white !important;
    border-radius: 3px !important;
    font-weight: bold !important;
}

button:hover {
    background-color: #0b4f2e !important;
}
</style>
""", unsafe_allow_html=True)

# ================= SESSION =================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "account" not in st.session_state:
    st.session_state.account = None

# ================= LOGIN =================
if not st.session_state.logged_in:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,1,1])

    with col2:
        st.markdown("## 🏦 **LuisBank**")
        st.caption("Acesso ao Internet Banking")

        acc_id = st.text_input("Conta")
        
        if st.button("Entrar"):
            if acc_id:
                try:
                    # AJUSTE TÉCNICO:
                    # Como não temos uma rota de "Buscar Dados da Conta", 
                    # vamos usar a rota de "Saldo" para validar se a conta existe.
                    url_validacao = f"{API_URL}/accounts/{acc_id}/balance"
                    
                    # DEBUG: Mostra na tela onde ele está tentando conectar (pode remover depois)
                    # st.write(f"Conectando em: {url_validacao}")
                    
                    r = requests.get(url_validacao)

                    if r.status_code == 200:
                        # Se deu 200, a conta existe!
                        dados_saldo = r.json()
                        
                        # Montamos um objeto de conta "fake" pois a API de saldo não retorna nome
                        # Num sistema real, fariamos uma rota GET /accounts/{id}
                        st.session_state.account = {
                            "id": dados_saldo["account_id"],
                            "name": "Ricardo Ribeiro", # Nome fixo ou genérico
                            "document": "123.456.789-00",
                            "agency": "0001"
                        }
                        
                        st.session_state.logged_in = True
                        st.rerun()
                    else:
                        st.error(f"Conta inválida ou inexistente (Erro {r.status_code})")
                        # st.json(r.json()) # Mostra o detalhe do erro se houver
                
                except Exception as e:
                    st.error(f"Erro de Conexão: {e}")
                    st.warning("Verifique se o Docker está rodando.")
            else:
                st.warning("Digite o número da conta.")

# ================= DASHBOARD =================
else:
    acc = st.session_state.account

    # HEADER
    st.markdown(
        f"<div class='top-bar'>LuisBank Internet Banking &nbsp;&nbsp; | &nbsp;&nbsp; Usuário: {acc.get('name','Cliente')}</div>",
        unsafe_allow_html=True
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # LAYOUT
    sidebar, main = st.columns([1, 3])

    # ===== SIDEBAR =====
    with sidebar:
        st.markdown("<div class='sidebar-box'>", unsafe_allow_html=True)
        st.markdown("**Empresa**")
        st.markdown(f"CNPJ: {acc.get('document','00.000.000/0001-00')}")
        st.markdown(f"Agência: {acc.get('agency','0001')}")
        st.markdown(f"Conta: {acc['id']}")
        st.markdown("---")
        if st.button("Sair"):
            st.session_state.clear()
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # ===== MAIN =====
    with main:
        # SALDO
        try:
            r = requests.get(f"{API_URL}/accounts/{acc['id']}/balance")
            saldo = r.json()["balance"] / 100
        except:
            saldo = 0

        st.markdown("<div class='content-box'>", unsafe_allow_html=True)
        st.markdown("<div class='section-title'>Saldo (R$)</div>", unsafe_allow_html=True)
        st.markdown(f"**Total Disponível:** R$ {saldo:,.2f}")
        st.markdown("</div>", unsafe_allow_html=True)

        # LANÇAMENTOS FUTUROS
        st.markdown("<div class='content-box'>", unsafe_allow_html=True)
        st.markdown("<div class='section-title'>Lançamentos Futuros</div>", unsafe_allow_html=True)
        st.warning("Não há lançamentos futuros.")
        st.markdown("</div>", unsafe_allow_html=True)

        # OPERAÇÕES
        st.markdown("<div class='content-box'>", unsafe_allow_html=True)
        st.markdown("<div class='section-title'>Movimentações</div>", unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:
            val = st.number_input("Depósito", min_value=1.0)
            if st.button("Depositar"):
                payload = {
                    "idempotency_key": str(uuid4()),
                    "amount": int(val * 100),
                    "type": "DEPOSIT",
                    "account_id": acc["id"]
                }
                requests.post(f"{API_URL}/transactions", json=payload)
                st.rerun()

        with col2:
            val = st.number_input("Saque", min_value=1.0, key="s")
            if st.button("Sacar"):
                payload = {
                    "idempotency_key": str(uuid4()),
                    "amount": int(val * 100),
                    "type": "WITHDRAW",
                    "account_id": acc["id"]
                }
                r = requests.post(f"{API_URL}/transactions", json=payload)
                if r.status_code == 422:
                    st.error("Saldo insuficiente")
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<center style='color:#888'>LuisBank © 2026</center>", unsafe_allow_html=True)
