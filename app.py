import streamlit as st
import sys
import os
import locale

# Configurar locale brasileiro
try:
    locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_TIME, 'Portuguese_Brazil.1252')
    except:
        pass  # Mantém o padrão se não conseguir configurar

# Add components directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'components'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))

from components.auth import check_authentication, login_page
from components.database import init_database
from components.header import display_header

# Configure page
st.set_page_config(
    page_title="Sistema de Chamados de TI",
    page_icon="📟",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database and ensure data directory exists
os.makedirs('data', exist_ok=True)
init_database()

def main():
    # Check if user is authenticated
    if not check_authentication():
        login_page()
        return
    
    # Get user info from session
    user_info = st.session_state.get('user_info', {})
    user_role = user_info.get('role', '')
    username = user_info.get('username', '')
    
    # Display header
    display_header()
    
    # Main page content
    st.title("📟 Sistema de Chamados de TI")
    st.markdown(f"**Bem-vindo, {username}!** | Perfil: {user_role}")
    
    # Role-based welcome message and navigation
    if user_role == 'Colaborador':
        st.info("🎫 Você pode abrir chamados e acompanhar o status dos seus pedidos.")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📝 Abrir Novo Chamado", use_container_width=True):
                st.switch_page("pages/1_abrir_chamado.py")
        with col2:
            if st.button("📋 Meus Chamados", use_container_width=True):
                st.switch_page("pages/2_meus_chamados.py")
    
    elif user_role == 'Técnico':
        st.info("🔧 Gerencie chamados atribuídos e disponíveis para atendimento.")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🎯 Chamados para Técnicos", use_container_width=True):
                st.switch_page("pages/3_chamados_tecnicos.py")
        with col2:
            if st.button("📋 Meus Chamados", use_container_width=True):
                st.switch_page("pages/2_meus_chamados.py")
    
    elif user_role == 'Administrador':
        st.info("⚙️ Acesso completo ao sistema: gerencie usuários e todos os chamados.")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("👥 Gerenciar Usuários", use_container_width=True):
                st.switch_page("pages/5_admin_usuarios.py")
        with col2:
            if st.button("🎯 Todos os Chamados", use_container_width=True):
                st.switch_page("pages/3_chamados_tecnicos.py")
        with col3:
            if st.button("📊 Dashboard", use_container_width=True):
                st.switch_page("pages/4_dashboard_diretoria.py")
    
    elif user_role == 'Diretoria':
        st.info("📊 Acesse relatórios gerenciais e dashboards analíticos.")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📊 Dashboard Gerencial", use_container_width=True):
                st.switch_page("pages/4_dashboard_diretoria.py")
        with col2:
            if st.button("👀 Visualizar Chamados", use_container_width=True):
                st.switch_page("pages/3_chamados_tecnicos.py")
    
    # Quick stats section
    with st.container():
        st.markdown("---")
        from components.database import get_quick_stats
        stats = get_quick_stats()
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total de Chamados", stats['total'])
        with col2:
            st.metric("Pendentes", stats['pendentes'])
        with col3:
            st.metric("Em Andamento", stats['em_andamento'])
        with col4:
            st.metric("Resolvidos", stats['resolvidos'])
    
    # Logout button in sidebar
    with st.sidebar:
        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        
        # Informações básicas no final do sidebar
        st.markdown("---")
        st.markdown("""
        <div style="font-size: 10px; color: #888; text-align: center;">
        <p>v1.0.3</p>
        <p><a href="https://github.com/pgup-sistemas" target="_blank" style="color: #888;">PgUp Sistemas</a></p>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
