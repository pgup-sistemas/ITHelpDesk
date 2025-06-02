import streamlit as st
import sqlite3
import hashlib
from datetime import datetime

def hash_password(password):
    """Hash a password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, hashed):
    """Verify a password against its hash"""
    return hash_password(password) == hashed

def authenticate_user(username, password):
    """Authenticate user credentials"""
    conn = sqlite3.connect('data/chamados.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, username, password_hash, role, setor, ativo
        FROM usuarios 
        WHERE username = ? AND ativo = 1
    """, (username,))
    
    user = cursor.fetchone()
    conn.close()
    
    if user and verify_password(password, user[2]):
        return {
            'id': user[0],
            'username': user[1],
            'role': user[3],
            'setor': user[4]
        }
    return None

def check_authentication():
    """Check if user is authenticated"""
    return 'authenticated' in st.session_state and st.session_state.authenticated

def login_page():
    """Display login page"""
    st.title("🔐 Login - Sistema de Chamados de TI")
    
    with st.form("login_form"):
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown("### Acesso ao Sistema")
            username = st.text_input("👤 Usuário")
            password = st.text_input("🔒 Senha", type="password")
            
            submit_button = st.form_submit_button("Entrar", use_container_width=True)
            
            if submit_button:
                if username and password:
                    user_info = authenticate_user(username, password)
                    if user_info:
                        st.session_state.authenticated = True
                        st.session_state.user_info = user_info
                        st.success("Login realizado com sucesso!")
                        st.rerun()
                    else:
                        st.error("❌ Usuário ou senha incorretos!")
                else:
                    st.error("❌ Preencha todos os campos!")
    
    # Information about default users (for demo purposes)
    with st.expander("ℹ️ Informações de Acesso"):
        st.markdown("""
        **Usuários padrão do sistema:**
        
        - **Administrador:** admin / admin123
        - **Técnico:** tecnico / tecnico123  
        - **Colaborador:** user / user123
        - **Diretoria:** diretor / diretor123
        
        *O administrador pode criar novos usuários através do painel administrativo.*
        """)

def logout():
    """Logout user"""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

def require_role(required_roles):
    """Decorator to require specific roles"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not check_authentication():
                st.error("❌ Acesso negado. Faça login primeiro.")
                st.stop()
            
            user_role = st.session_state.user_info.get('role')
            if user_role not in required_roles:
                st.error(f"❌ Acesso negado. Perfil necessário: {', '.join(required_roles)}")
                st.stop()
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

def get_current_user():
    """Get current logged in user info"""
    if check_authentication():
        return st.session_state.user_info
    return None
