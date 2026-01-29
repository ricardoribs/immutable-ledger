import streamlit as st
import requests
from datetime import datetime
import streamlit.components.v1 as components
from uuid import uuid4
import time
from fpdf import FPDF
import qrcode
from io import BytesIO
import os

# ======================================================
# CONFIG
# ======================================================
st.set_page_config(page_title="LuisBank | Digital", layout="wide", initial_sidebar_state="collapsed")

API_URL = "http://ledger_api:8000/ledger"

# ======================================================
# UTILS
# ======================================================
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.set_text_color(31, 111, 74)
        self.cell(0, 10, 'LuisBank Corporate', 0, 1, 'R'); self.ln(5)
    def footer(self):
        self.set_y(-15); self.set_font('Arial', 'I', 8); self.set_text_color(128)
        self.cell(0, 10, f'Pag {self.page_no()}', 0, 0, 'C')

def gerar_pdf(acc_data, txs):
    pdf = PDF(); pdf.add_page()
    pdf.set_font('Arial', 'B', 16); pdf.cell(0, 10, 'Extrato Oficial', 0, 1)
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 5, f"Cliente: {acc_data['name']}", 0, 1)
    pdf.cell(0, 5, f"CPF: {acc_data.get('cpf_masked', '***')}", 0, 1)
    pdf.cell(0, 5, f"Conta: {acc_data['id']}", 0, 1)
    pdf.ln(10)
    pdf.set_fill_color(31, 111, 74); pdf.set_text_color(255); pdf.set_font('Arial', 'B', 10)
    pdf.cell(40, 8, 'Data', 1, 0, 'C', 1); pdf.cell(40, 8, 'Tipo', 1, 0, 'C', 1); pdf.cell(60, 8, 'Descricao', 1, 0, 'C', 1); pdf.cell(50, 8, 'Valor', 1, 1, 'C', 1)
    pdf.set_text_color(0); pdf.set_font('Arial', '', 9); fill=False; pdf.set_fill_color(240,240,240)
    if not txs: pdf.cell(190, 8, 'Sem movimentacoes.', 1, 1, 'C', fill)
    for tx in txs:
        val = tx['amount']/100; c = (200,0,0) if tx['type']=='WITHDRAW' else (0,100,0); sinal = "-" if tx['type']=='WITHDRAW' else "+"
        pdf.set_text_color(0); pdf.cell(40, 8, tx['date'][:10], 1, 0, 'C', fill); pdf.cell(40, 8, tx['type'], 1, 0, 'C', fill); pdf.cell(60, 8, '...', 1, 0, 'C', fill)
        pdf.set_text_color(*c); pdf.cell(50, 8, f"{sinal} {val:.2f}", 1, 1, 'R', fill); fill=not fill
    
    return bytes(pdf.output(dest='S')) # Fix para fpdf novo

def gerar_qr_imagem(payload):
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(payload)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf)
    return buf.getvalue()

def get_auth_header():
    token = st.session_state.get("access_token")
    if token: return {"Authorization": f"Bearer {token}"}
    return {}

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap');
body { font-family: 'Roboto'; background-color: #f0f2f5; }
.auth-card { background: white; padding: 40px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); text-align: center; border-top: 5px solid #1f6f4a; margin-bottom: 20px; }
div[data-testid="stHorizontalBlock"] { gap: 0.15rem !important; }
div[data-testid="stHorizontalBlock"] button { width: 100%; height: 44px; border: 1px solid #d9d9d9; background: white; color: #555; font-weight: 500; transition: 0.2s; border-radius: 0; }
div[data-testid="stHorizontalBlock"] button:hover { background-color: #f1f8f5; color: #1f6f4a; border-color: #1f6f4a; z-index: 2; }
div[data-testid="stHorizontalBlock"] button:focus { background: #e9f5ee; color: #1f6f4a; border-bottom: 3px solid #1f6f4a !important; font-weight: bold; }
</style>""", unsafe_allow_html=True)

# ======================================================
# STATE
# ======================================================
for k in ["user", "view", "signup_mode", "created_id", "access_token", "refresh_token", "otp_uri", "backup_codes_view"]:
    if k not in st.session_state: st.session_state[k] = None
if st.session_state.view is None: st.session_state.view = "home"

# ======================================================
# AUTH
# ======================================================
def login():
    uid, pwd, otp = st.session_state.l_id, st.session_state.l_pass, st.session_state.l_otp
    if not uid or not pwd: st.error("Preencha ID e Senha."); return
    try:
        payload = {"username": uid, "password": pwd}
        params = {}
        if otp: params["otp"] = otp
        r = requests.post(f"{API_URL}/auth/login", data=payload, params=params)
        
        if r.status_code == 200:
            tokens = r.json()
            st.session_state.access_token = tokens["access_token"]
            st.session_state.refresh_token = tokens["refresh_token"]
            
            headers = {"Authorization": f"Bearer {tokens['access_token']}"}
            r_user = requests.get(f"{API_URL}/accounts/me", headers=headers)
            
            if r_user.status_code == 200:
                user_data = r_user.json()
                st.session_state.user = {
                    "id": user_data["id"], 
                    "name": user_data["name"], 
                    "cpf_masked": user_data.get("cpf_masked"),
                    "mfa_enabled": user_data.get("mfa_enabled", False)
                }
                st.session_state.view = "home"
            else: st.error(f"Falha ao recuperar dados: {r_user.status_code}")
        elif r.status_code == 401 and "MFA_REQUIRED" in r.text:
            st.warning("⚠️ 2FA Necessário. Digite o código do App ou Backup Code.")
        elif r.status_code == 429: st.error("Muitas tentativas. Aguarde.")
        else: st.error("Credenciais inválidas.")
    except Exception as e: st.error(f"Erro: {e}")

def signup():
    nome, cpf, email, pwd = st.session_state.s_name, st.session_state.s_cpf, st.session_state.s_email, st.session_state.s_pass
    if not nome or not pwd or not cpf or not email: st.warning("Preencha todos os campos."); return
    try:
        r = requests.post(f"{API_URL}/accounts", json={"name": nome, "cpf": cpf, "email": email, "password": pwd})
        if r.status_code == 201:
            st.session_state.created_id = r.json()["id"]
        else: st.error(f"Erro: {r.text}")
    except Exception as e: st.error(f"Erro: {e}")

def logout():
    if st.session_state.access_token:
        try: requests.post(f"{API_URL}/auth/logout", headers=get_auth_header())
        except: pass
    for key in list(st.session_state.keys()): del st.session_state[key]
    st.rerun()

# ======================================================
# APP
# ======================================================
if st.session_state.user is None:
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        if st.session_state.signup_mode:
            if st.session_state.created_id:
                st.markdown(f"""<div class="auth-card" style="border-top-color:#2e7d32;"><h1 style="color:#2e7d32; margin:0;">Sucesso!</h1><div style="background:#e8f5e9; padding:20px; border-radius:8px; border:1px solid #2e7d32; margin:20px 0;"><p style="margin:0; font-size:12px; color:#2e7d32;">SUA CONTA</p><h1 style="color:#2e7d32; margin:5px 0; font-size:48px;">{st.session_state.created_id}</h1><p>Use sua senha.</p></div></div>""", unsafe_allow_html=True)
                if st.button("Ir para Login", use_container_width=True):
                    st.session_state.created_id = None; st.session_state.signup_mode = False; st.rerun()
            else:
                st.markdown("""<div class="auth-card"><h1 style="color:#1f6f4a; margin:0;">Nova Conta</h1></div>""", unsafe_allow_html=True)
                with st.form("reg"):
                    st.text_input("Nome Completo", key="s_name")
                    st.text_input("CPF (Ex: 123.456.789-00)", key="s_cpf")
                    st.text_input("Email (Obrigatório)", key="s_email")
                    st.text_input("Senha", type="password", key="s_pass")
                    if st.form_submit_button("CRIAR", use_container_width=True): signup(); st.rerun()
                if st.button("Voltar"): st.session_state.signup_mode = False; st.rerun()
        else:
            st.markdown("""<div class="auth-card"><h1 style="color:#1f6f4a; margin:0;">LuisBank</h1><p style="color:#666;">Secure Login (HTTPS)</p></div>""", unsafe_allow_html=True)
            with st.form("log"):
                st.text_input("Conta (ID) ou Email", key="l_id") 
                st.text_input("Senha", type="password", key="l_pass")
                st.text_input("Código 2FA (se ativo)", key="l_otp", help="Use código do Google Authenticator ou Backup Code")
                if st.form_submit_button("ENTRAR", use_container_width=True): login(); st.rerun()
            if st.button("Abra sua conta"): st.session_state.signup_mode = True; st.rerun()
else:
    acc = st.session_state.user
    bal = 0.00
    try: 
        r = requests.get(f"{API_URL}/accounts/{acc['id']}/balance", headers=get_auth_header())
        if r.status_code==200: bal = r.json()["balance"]
        elif r.status_code==401: logout()
    except: pass
    
    mfa_badge = '<span style="background:#2e7d32; color:white; font-size:10px;">MFA ATIVO</span>' if acc.get('mfa_enabled') else '<span style="background:#c62828; color:white; font-size:10px;">MFA INATIVO</span>'
    components.html(f"""<!DOCTYPE html><div style="background: linear-gradient(90deg, #123326, #1f6f4a); color: white; padding: 10px 24px; display: flex; align-items: center; height: 40px; font-family: Roboto;"><div style="font-weight:700; font-size:18px;">LuisBank <span style="background:#f4d03f; color:#123326; font-size:10px; padding:2px 6px; border-radius:3px;">HTTPS SECURE</span></div><div style="margin-left:auto; font-size:12px;">{acc['name']} ({acc.get('cpf_masked')}) | {mfa_badge}</div></div>""", height=60)
    
    m1, m2, m3, m4, m5, m6 = st.columns(6)
    with m1: st.button("Saldos", on_click=lambda: setattr(st.session_state, 'view', 'home'))
    with m2: st.button("Pagamentos", on_click=lambda: setattr(st.session_state, 'view', 'pagamentos'))
    with m3: st.button("Transferir", on_click=lambda: setattr(st.session_state, 'view', 'transferencias'))
    with m4: st.button("Segurança 🛡️", on_click=lambda: setattr(st.session_state, 'view', 'mfa'))
    with m5: st.button("Pix 💠", on_click=lambda: setattr(st.session_state, 'view', 'pix'))
    with m6: 
        if st.button("Sair"): logout()

    if st.session_state.view == "home":
        st.markdown(f"### Visão Geral")
        c1, c2 = st.columns([1,2])
        with c1: st.metric("Saldo", f"R$ {bal:,.2f}")
        with c2: st.info("🔒 Conexão Criptografada (TLS/SSL). Ninguém pode interceptar seus dados.")
        st.write("---")
        txs=[]
        try: txs = requests.get(f"{API_URL}/accounts/{acc['id']}/statement", headers=get_auth_header()).json().get("transactions",[])
        except: pass
        
        st.download_button("📄 Baixar Extrato", data=gerar_pdf(acc, txs), file_name="extrato.pdf", mime="application/pdf")

    elif st.session_state.view == "mfa":
        st.markdown("### 🛡️ Configuração MFA")
        if acc.get('mfa_enabled'): st.success("✅ 2FA Ativo")
        else:
            try:
                if not st.session_state.otp_uri:
                     data = requests.get(f"{API_URL}/auth/mfa/setup", headers=get_auth_header()).json()
                     st.session_state.otp_uri = data["otp_uri"]

                st.info("1. Escaneie este QR Code no Google Authenticator")
                st.image(gerar_qr_imagem(st.session_state.otp_uri), width=200)
                
                with st.form("mfa"):
                    c = st.text_input("2. Digite o código que aparece no App")
                    if st.form_submit_button("Ativar"):
                        r = requests.post(f"{API_URL}/auth/mfa/enable", params={"code":c}, headers=get_auth_header())
                        
                        if r.status_code==200: 
                            resp = r.json()
                            st.session_state.backup_codes_view = resp.get("backup_codes", [])
                            st.rerun() # Recarrega para mostrar os códigos
                        else: st.error(f"Erro: {r.text}")
                
                # ✅ Exibe Backup Codes após ativação
                if st.session_state.backup_codes_view:
                     st.markdown("### ⚠️ Códigos de Recuperação")
                     st.warning("Salve estes códigos em um lugar seguro! Se perder o celular, eles são a única forma de recuperar a conta.")
                     st.code("\n".join(st.session_state.backup_codes_view))
                     if st.button("Já salvei, Sair"):
                         logout()

            except Exception as e: st.error(f"Erro setup: {e}")
            
    elif st.session_state.view == "pagamentos":
        st.markdown("### Caixa")
        with st.form("pg"):
            op = st.selectbox("Tipo", ["DEPOSIT", "WITHDRAW"])
            dest = st.text_input("Conta Destino (ID)", value=str(acc['id']))
            val = st.number_input("Valor", 0.01)
            otp_tx = st.text_input("Código 2FA (Obrigatório se > R$ 1.000)", type="password")
            
            if st.form_submit_button("Confirmar"):
                try:
                    params = {}
                    if otp_tx: params["otp"] = otp_tx
                    r=requests.post(f"{API_URL}/transactions", json={"idempotency_key":str(uuid4()), "amount":int(val*100), "type":op, "account_id":int(dest)}, params=params, headers=get_auth_header())
                    
                    if r.status_code==201: st.success("Feito!"); time.sleep(1); st.rerun()
                    elif r.status_code==401: st.error("⚠️ Autenticação Step-up necessária! Preencha o código 2FA.")
                    elif r.status_code==403: st.error(f"🚨 FRAUDE: {r.json()['detail']}")
                    else: st.error(f"Erro: {r.text}")
                except Exception as e: st.error(f"Erro: {e}")

    elif st.session_state.view == "transferencias":
        st.markdown("### Transferências")
        with st.form("tr"):
            dest = st.text_input("Conta Destino")
            val = st.number_input("Valor", 0.01)
            otp_tx = st.text_input("Código 2FA (Obrigatório se > R$ 1.000)", type="password")
            
            if st.form_submit_button("Confirmar"):
                try:
                    params = {}
                    if otp_tx: params["otp"] = otp_tx
                    r=requests.post(f"{API_URL}/transfers", json={"idempotency_key":str(uuid4()), "amount":int(val*100), "from_account_id":acc['id'], "to_account_id":int(dest)}, params=params, headers=get_auth_header())
                    
                    if r.status_code==201: st.success("Feito!"); time.sleep(1); st.rerun()
                    elif r.status_code==401: st.error("⚠️ Autenticação Step-up necessária! Preencha o código 2FA.")
                    elif r.status_code==403: st.error(f"🚨 FRAUDE: {r.json()['detail']}")
                    else: st.error(f"Erro: {r.text}")
                except Exception as e: st.error(f"Erro: {e}")

    elif st.session_state.view == "pix":
        t1, t2 = st.tabs(["Receber", "Pagar"])
        with t1:
            v = st.number_input("Valor", 0.0)
            if v>0: st.image(gerar_qr_imagem(f"PIX...{uuid4()}...{v}"), width=200)
        with t2:
            with st.form("px"):
                d = st.text_input("Chave"); va = st.number_input("Valor", 0.01)
                otp_tx = st.text_input("Código 2FA (Obrigatório se > R$ 1.000)", type="password")
                if st.form_submit_button("Pagar"):
                    params = {}
                    if otp_tx: params["otp"] = otp_tx
                    r = requests.post(f"{API_URL}/transfers", json={"idempotency_key":str(uuid4()), "amount":int(va*100), "from_account_id":acc['id'], "to_account_id":int(d)}, params=params, headers=get_auth_header())
                    if r.status_code==201: st.success("Enviado!"); st.session_state.view="home"; st.rerun()
                    elif r.status_code==401: st.error("⚠️ Autenticação Step-up necessária! Preencha o código 2FA.")
                    else: st.error("Erro no Pix")