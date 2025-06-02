import streamlit as st
import sys
import os
import sqlite3
import hashlib
import pandas as pd

# Add components directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'components'))

from components.auth import check_authentication, get_current_user, hash_password
from components.database import get_usuarios

# Check authentication
if not check_authentication():
    st.error("❌ Acesso negado. Faça login primeiro.")
    st.stop()

current_user = get_current_user()

# Only allow administrators
if current_user['role'] != 'Administrador':
    st.error("❌ Acesso negado. Esta página é apenas para administradores.")
    st.stop()

st.set_page_config(page_title="Administração de Usuários", page_icon="👥", layout="wide")

st.title("👥 Administração de Usuários")
st.markdown("Gerencie usuários, perfis e permissões do sistema")

# Tabs for different functions
tab1, tab2, tab3 = st.tabs(["👥 Listar Usuários", "➕ Adicionar Usuário", "📊 Estatísticas"])

with tab1:
    st.markdown("### 📋 Lista de Usuários")
    
    # Get all users
    users = get_usuarios()
    
    if users:
        # Convert to DataFrame for better display
        df = pd.DataFrame(users, columns=['ID', 'Username', 'Nome', 'Email', 'Perfil', 'Setor', 'Ativo'])
        
        # Filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            role_filter = st.selectbox("Filtrar por Perfil:", 
                                     ["Todos", "Colaborador", "Técnico", "Administrador", "Diretoria"])
        with col2:
            sector_filter = st.selectbox("Filtrar por Setor:", 
                                       ["Todos", "TI", "Administrativo", "Financeiro", "RH", "Vendas", "Marketing", "Produção", "Diretoria"])
        with col3:
            status_filter = st.selectbox("Filtrar por Status:", 
                                       ["Todos", "Ativo", "Inativo"])
        
        # Apply filters
        filtered_df = df.copy()
        if role_filter != "Todos":
            filtered_df = filtered_df[filtered_df['Perfil'] == role_filter]
        if sector_filter != "Todos":
            filtered_df = filtered_df[filtered_df['Setor'] == sector_filter]
        if status_filter != "Todos":
            active_status = 1 if status_filter == "Ativo" else 0
            filtered_df = filtered_df[filtered_df['Ativo'] == active_status]
        
        # Display statistics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total de Usuários", len(filtered_df))
        with col2:
            active_users = len(filtered_df[filtered_df['Ativo'] == 1])
            st.metric("Usuários Ativos", active_users)
        with col3:
            admins = len(filtered_df[filtered_df['Perfil'] == 'Administrador'])
            st.metric("Administradores", admins)
        with col4:
            technicians = len(filtered_df[filtered_df['Perfil'] == 'Técnico'])
            st.metric("Técnicos", technicians)
        
        st.markdown("---")
        
        # Display users with actions
        for _, user in filtered_df.iterrows():
            user_id, username, nome, email, perfil, setor, ativo = user
            
            # Status indicator
            status_icon = "🟢" if ativo else "🔴"
            status_text = "Ativo" if ativo else "Inativo"
            
            # Role color
            role_colors = {
                'Administrador': '🔴',
                'Técnico': '🔵',
                'Colaborador': '🟢',
                'Diretoria': '🟣'
            }
            role_icon = role_colors.get(perfil, '⚪')
            
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([2, 2, 1, 1, 2])
                
                with col1:
                    st.markdown(f"**{nome}**")
                    st.markdown(f"@{username}")
                
                with col2:
                    st.markdown(f"📧 {email or 'Não informado'}")
                    st.markdown(f"🏢 {setor}")
                
                with col3:
                    st.markdown(f"{role_icon} {perfil}")
                
                with col4:
                    st.markdown(f"{status_icon} {status_text}")
                
                with col5:
                    # Action buttons
                    if username != current_user['username']:  # Can't edit own user
                        if st.button(f"✏️ Editar", key=f"edit_{user_id}"):
                            st.session_state[f'editing_user_{user_id}'] = True
                            st.rerun()
                        
                        # Toggle active status
                        if ativo:
                            if st.button(f"🚫 Desativar", key=f"deactivate_{user_id}"):
                                update_user_status(user_id, False)
                                st.success(f"Usuário {username} desativado!")
                                st.rerun()
                        else:
                            if st.button(f"✅ Ativar", key=f"activate_{user_id}"):
                                update_user_status(user_id, True)
                                st.success(f"Usuário {username} ativado!")
                                st.rerun()
                    else:
                        st.markdown("*Usuário atual*")
                
                # Edit form
                if st.session_state.get(f'editing_user_{user_id}', False):
                    with st.form(f"edit_form_{user_id}"):
                        st.markdown(f"### ✏️ Editar Usuário: {username}")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            new_nome = st.text_input("Nome Completo:", value=nome)
                            new_email = st.text_input("Email:", value=email or "")
                            new_setor = st.selectbox("Setor:", 
                                                   ["TI", "Administrativo", "Financeiro", "RH", "Vendas", "Marketing", "Produção", "Diretoria"],
                                                   index=["TI", "Administrativo", "Financeiro", "RH", "Vendas", "Marketing", "Produção", "Diretoria"].index(setor) if setor in ["TI", "Administrativo", "Financeiro", "RH", "Vendas", "Marketing", "Produção", "Diretoria"] else 0)
                        
                        with col2:
                            new_perfil = st.selectbox("Perfil:", 
                                                    ["Colaborador", "Técnico", "Administrador", "Diretoria"],
                                                    index=["Colaborador", "Técnico", "Administrador", "Diretoria"].index(perfil))
                            new_password = st.text_input("Nova Senha (deixe vazio para manter):", type="password")
                            confirm_password = st.text_input("Confirmar Nova Senha:", type="password")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.form_submit_button("💾 Salvar Alterações"):
                                # Validate password if provided
                                if new_password:
                                    if new_password != confirm_password:
                                        st.error("❌ Senhas não coincidem!")
                                    elif len(new_password) < 6:
                                        st.error("❌ Senha deve ter pelo menos 6 caracteres!")
                                    else:
                                        update_user(user_id, new_nome, new_email, new_perfil, new_setor, new_password)
                                        st.success("✅ Usuário atualizado com sucesso!")
                                        del st.session_state[f'editing_user_{user_id}']
                                        st.rerun()
                                else:
                                    update_user(user_id, new_nome, new_email, new_perfil, new_setor)
                                    st.success("✅ Usuário atualizado com sucesso!")
                                    del st.session_state[f'editing_user_{user_id}']
                                    st.rerun()
                        
                        with col2:
                            if st.form_submit_button("❌ Cancelar"):
                                del st.session_state[f'editing_user_{user_id}']
                                st.rerun()
                
                st.markdown("---")
    else:
        st.info("📭 Nenhum usuário encontrado.")

with tab2:
    st.markdown("### ➕ Adicionar Novo Usuário")
    
    with st.form("add_user_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            username = st.text_input("👤 Nome de Usuário: *", help="Será usado para login")
            nome = st.text_input("📝 Nome Completo: *")
            email = st.text_input("📧 Email:")
            setor = st.selectbox("🏢 Setor: *", 
                               ["TI", "Administrativo", "Financeiro", "RH", "Vendas", "Marketing", "Produção", "Diretoria"])
        
        with col2:
            perfil = st.selectbox("👨‍💼 Perfil: *", 
                                ["Colaborador", "Técnico", "Administrador", "Diretoria"])
            password = st.text_input("🔒 Senha: *", type="password", help="Mínimo 6 caracteres")
            confirm_password = st.text_input("🔒 Confirmar Senha: *", type="password")
        
        # Profile descriptions
        with st.expander("ℹ️ Descrição dos Perfis"):
            st.markdown("""
            **👤 Colaborador:** Pode abrir e acompanhar seus próprios chamados
            
            **🔧 Técnico:** Pode gerenciar chamados disponíveis ou atribuídos, responder chats
            
            **⚙️ Administrador:** Acesso completo - cria usuários, visualiza todos os chamados, atribui técnicos
            
            **📊 Diretoria:** Acessa dashboards gerenciais e relatórios, visualização de chamados
            """)
        
        submitted = st.form_submit_button("➕ Criar Usuário", use_container_width=True)
        
        if submitted:
            # Validate required fields
            if not username or not nome or not password or not setor or not perfil:
                st.error("❌ Preencha todos os campos obrigatórios!")
            elif len(password) < 6:
                st.error("❌ A senha deve ter pelo menos 6 caracteres!")
            elif password != confirm_password:
                st.error("❌ As senhas não coincidem!")
            else:
                # Check if username already exists
                if check_username_exists(username):
                    st.error("❌ Nome de usuário já existe!")
                else:
                    try:
                        create_user(username, password, nome, email, perfil, setor)
                        st.success(f"✅ Usuário '{username}' criado com sucesso!")
                        st.info(f"📋 Perfil: {perfil} | Setor: {setor}")
                        
                        # Clear form by rerunning (optional)
                        if st.button("🔄 Limpar Formulário"):
                            st.rerun()
                    except Exception as e:
                        st.error(f"❌ Erro ao criar usuário: {str(e)}")

with tab3:
    st.markdown("### 📊 Estatísticas de Usuários")
    
    users = get_usuarios()
    if users:
        df = pd.DataFrame(users, columns=['ID', 'Username', 'Nome', 'Email', 'Perfil', 'Setor', 'Ativo'])
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Users by role
            st.markdown("#### 👨‍💼 Usuários por Perfil")
            role_counts = df['Perfil'].value_counts()
            
            # Create a pie chart
            import plotly.express as px
            fig = px.pie(values=role_counts.values, names=role_counts.index,
                        title="Distribuição de Usuários por Perfil")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Users by sector
            st.markdown("#### 🏢 Usuários por Setor")
            sector_counts = df['Setor'].value_counts()
            
            fig = px.bar(x=sector_counts.values, y=sector_counts.index, orientation='h',
                        title="Usuários por Setor")
            st.plotly_chart(fig, use_container_width=True)
        
        # Active vs Inactive
        col1, col2, col3, col4 = st.columns(4)
        
        active_count = len(df[df['Ativo'] == 1])
        inactive_count = len(df[df['Ativo'] == 0])
        
        with col1:
            st.metric("🟢 Usuários Ativos", active_count)
        with col2:
            st.metric("🔴 Usuários Inativos", inactive_count)
        with col3:
            st.metric("📊 Total", len(df))
        with col4:
            activity_rate = round((active_count / len(df)) * 100, 1) if len(df) > 0 else 0
            st.metric("📈 Taxa de Atividade", f"{activity_rate}%")

# Helper functions
def check_username_exists(username):
    """Check if username already exists"""
    conn = sqlite3.connect('data/chamados.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM usuarios WHERE username = ?", (username,))
    exists = cursor.fetchone() is not None
    
    conn.close()
    return exists

def create_user(username, password, nome, email, perfil, setor):
    """Create a new user"""
    conn = sqlite3.connect('data/chamados.db')
    cursor = conn.cursor()
    
    password_hash = hash_password(password)
    
    cursor.execute("""
        INSERT INTO usuarios (username, password_hash, nome_completo, email, role, setor)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (username, password_hash, nome, email, perfil, setor))
    
    conn.commit()
    conn.close()

def update_user(user_id, nome, email, perfil, setor, password=None):
    """Update an existing user"""
    conn = sqlite3.connect('data/chamados.db')
    cursor = conn.cursor()
    
    if password:
        password_hash = hash_password(password)
        cursor.execute("""
            UPDATE usuarios 
            SET nome_completo = ?, email = ?, role = ?, setor = ?, password_hash = ?
            WHERE id = ?
        """, (nome, email, perfil, setor, password_hash, user_id))
    else:
        cursor.execute("""
            UPDATE usuarios 
            SET nome_completo = ?, email = ?, role = ?, setor = ?
            WHERE id = ?
        """, (nome, email, perfil, setor, user_id))
    
    conn.commit()
    conn.close()

def update_user_status(user_id, active):
    """Update user active status"""
    conn = sqlite3.connect('data/chamados.db')
    cursor = conn.cursor()
    
    cursor.execute("UPDATE usuarios SET ativo = ? WHERE id = ?", (active, user_id))
    
    conn.commit()
    conn.close()

# Sidebar with quick actions
with st.sidebar:
    st.markdown("### 🚀 Ações Rápidas")
    
    if st.button("🎯 Chamados Técnicos", use_container_width=True):
        st.switch_page("pages/3_chamados_tecnicos.py")
    
    if st.button("📊 Dashboard", use_container_width=True):
        st.switch_page("pages/4_dashboard_diretoria.py")
    
    if st.button("📋 Meus Chamados", use_container_width=True):
        st.switch_page("pages/2_meus_chamados.py")
    
    st.markdown("---")
    st.markdown("### 📊 Resumo")
    
    users = get_usuarios()
    if users:
        total_users = len(users)
        active_users = len([u for u in users if u[6] == 1])  # Ativo column
        
        st.metric("Total Usuários", total_users)
        st.metric("Usuários Ativos", active_users)
        
        # Role distribution
        roles = {}
        for user in users:
            role = user[4]  # Role column
            roles[role] = roles.get(role, 0) + 1
        
        for role, count in roles.items():
            st.metric(role, count)

    st.markdown("---")
    st.markdown("### ⚠️ Dicas de Segurança")
    st.markdown("""
    - 🔒 Use senhas fortes (min. 6 caracteres)
    - 👥 Atribua perfis adequados
    - 🚫 Desative usuários inativos
    - 📧 Mantenha emails atualizados
    """)
