import streamlit as st
import sys
import os
import pandas as pd
from datetime import datetime

# Add components directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'components'))

from components.auth import check_authentication, get_current_user
from components.database import get_chamados, get_chamado_by_id, update_chamado_status
from components.chat import display_chat

# Check authentication
if not check_authentication():
    st.error("❌ Acesso negado. Faça login primeiro.")
    st.stop()

current_user = get_current_user()

st.set_page_config(page_title="Meus Chamados", page_icon="📋", layout="wide")

st.title("📋 Meus Chamados")

# Get user's tickets
if current_user['role'] in ['Técnico', 'Administrador']:
    # Technicians can see tickets assigned to them or all tickets (for admin)
    if current_user['role'] == 'Administrador':
        user_tickets = get_chamados()  # Admin sees all tickets
        st.info("👨‍💼 Como administrador, você pode ver todos os chamados do sistema.")
    else:
        user_tickets = get_chamados({'tecnico_id': current_user['id']})
        st.info("🔧 Visualizando chamados atribuídos a você.")
else:
    # Regular users see only their own tickets
    user_tickets = get_chamados({'solicitante_id': current_user['id']})
    st.info("👤 Visualizando seus chamados abertos.")

# Filters
col1, col2, col3 = st.columns(3)

with col1:
    status_filter = st.selectbox("📊 Filtrar por Status", 
                                ["Todos", "Pendente", "Em Andamento", "Resolvido", "Cancelado"])

with col2:
    priority_filter = st.selectbox("⚡ Filtrar por Prioridade", 
                                  ["Todas", "Alta", "Média", "Baixa"])

with col3:
    sector_filter = st.selectbox("🏢 Filtrar por Setor", 
                                ["Todos", "Administrativo", "Financeiro", "RH", "Vendas", "Marketing", "Produção", "TI", "Diretoria"])

# Apply filters
filtered_tickets = user_tickets
if status_filter != "Todos":
    filtered_tickets = [t for t in filtered_tickets if t[5] == status_filter]  # status is index 5
if priority_filter != "Todas":
    filtered_tickets = [t for t in filtered_tickets if t[4] == priority_filter]  # priority is index 4
if sector_filter != "Todos":
    filtered_tickets = [t for t in filtered_tickets if t[3] == sector_filter]  # sector is index 3

# Statistics
if filtered_tickets:
    col1, col2, col3, col4 = st.columns(4)
    
    total = len(filtered_tickets)
    pendentes = len([t for t in filtered_tickets if t[5] == 'Pendente'])
    em_andamento = len([t for t in filtered_tickets if t[5] == 'Em Andamento'])
    resolvidos = len([t for t in filtered_tickets if t[5] == 'Resolvido'])
    
    with col1:
        st.metric("Total", total)
    with col2:
        st.metric("Pendentes", pendentes)
    with col3:
        st.metric("Em Andamento", em_andamento)
    with col4:
        st.metric("Resolvidos", resolvidos)

st.markdown("---")

# Display tickets
if filtered_tickets:
    for ticket in filtered_tickets:
        ticket_id, titulo, descricao, setor, prioridade, status, solicitante, tecnico, data_abertura, data_resolucao, sla_prazo = ticket
        
        # Status and priority colors
        status_colors = {
            'Pendente': '🟡',
            'Em Andamento': '🔵',
            'Resolvido': '🟢',
            'Cancelado': '🔴'
        }
        
        priority_colors = {
            'Alta': '🔴',
            'Média': '🟡',
            'Baixa': '🟢'
        }
        
        # Calculate SLA status
        sla_status = "⏰ Dentro do Prazo"
        if sla_prazo:
            try:
                sla_deadline = datetime.strptime(sla_prazo, '%Y-%m-%d %H:%M:%S')
                now = datetime.now()
                if now > sla_deadline and status != 'Resolvido':
                    sla_status = "⚠️ SLA Vencido"
                elif (sla_deadline - now).total_seconds() < 3600 and status != 'Resolvido':  # Less than 1 hour
                    sla_status = "🚨 SLA Próximo do Vencimento"
            except:
                pass
        
        # Ticket card
        with st.expander(f"🎫 #{ticket_id} - {titulo} | {status_colors.get(status, '⚪')} {status} | {priority_colors.get(prioridade, '⚪')} {prioridade}"):
            
            # Ticket details
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"**📄 Descrição:** {descricao}")
                st.markdown(f"**🏢 Setor:** {setor}")
                st.markdown(f"**👤 Solicitante:** {solicitante}")
                if tecnico:
                    st.markdown(f"**🔧 Técnico:** {tecnico}")
                else:
                    st.markdown("**🔧 Técnico:** Não atribuído")
            
            with col2:
                st.markdown(f"**📅 Abertura:** {data_abertura}")
                if data_resolucao:
                    st.markdown(f"**✅ Resolução:** {data_resolucao}")
                st.markdown(f"**⏱️ SLA:** {sla_status}")
            
            # Action buttons for technicians and admins
            if current_user['role'] in ['Técnico', 'Administrador'] and status != 'Resolvido':
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if status == 'Pendente' and st.button(f"👋 Assumir Chamado #{ticket_id}", key=f"assume_{ticket_id}"):
                        from components.database import assign_technician
                        assign_technician(ticket_id, current_user['id'], current_user['username'], 
                                        current_user['id'], current_user['username'])
                        st.success("Chamado assumido com sucesso!")
                        st.rerun()
                
                with col2:
                    if status == 'Em Andamento' and st.button(f"✅ Resolver #{ticket_id}", key=f"resolve_{ticket_id}"):
                        st.session_state[f'resolving_{ticket_id}'] = True
                        st.rerun()
                
                with col3:
                    if st.button(f"📝 Atualizar #{ticket_id}", key=f"update_{ticket_id}"):
                        st.session_state[f'updating_{ticket_id}'] = True
                        st.rerun()
                
                # Resolution form
                if st.session_state.get(f'resolving_{ticket_id}', False):
                    with st.form(f"resolve_form_{ticket_id}"):
                        st.markdown("### ✅ Resolver Chamado")
                        resolution = st.text_area("Descreva a solução aplicada:", height=100)
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.form_submit_button("✅ Confirmar Resolução"):
                                update_chamado_status(ticket_id, 'Resolvido', current_user['id'], 
                                                    current_user['username'], resolution)
                                st.success("Chamado resolvido com sucesso!")
                                del st.session_state[f'resolving_{ticket_id}']
                                st.rerun()
                        with col2:
                            if st.form_submit_button("❌ Cancelar"):
                                del st.session_state[f'resolving_{ticket_id}']
                                st.rerun()
                
                # Update form
                if st.session_state.get(f'updating_{ticket_id}', False):
                    with st.form(f"update_form_{ticket_id}"):
                        st.markdown("### 📝 Atualizar Status")
                        new_status = st.selectbox("Novo Status:", ['Em Andamento', 'Pendente'])
                        update_notes = st.text_area("Observações:", height=80)
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.form_submit_button("💾 Salvar Atualização"):
                                update_chamado_status(ticket_id, new_status, current_user['id'], 
                                                    current_user['username'], update_notes)
                                st.success("Status atualizado com sucesso!")
                                del st.session_state[f'updating_{ticket_id}']
                                st.rerun()
                        with col2:
                            if st.form_submit_button("❌ Cancelar"):
                                del st.session_state[f'updating_{ticket_id}']
                                st.rerun()
            
            # Chat section
            st.markdown("---")
            display_chat(ticket_id, current_user)

else:
    st.info("📭 Nenhum chamado encontrado com os filtros aplicados.")
    
    if current_user['role'] in ['Colaborador']:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📝 Abrir Primeiro Chamado", use_container_width=True):
                st.switch_page("pages/1_abrir_chamado.py")

# Quick navigation
with st.sidebar:
    st.markdown("### 🧭 Navegação Rápida")
    
    if current_user['role'] in ['Colaborador', 'Técnico', 'Administrador']:
        if st.button("📝 Abrir Novo Chamado", use_container_width=True):
            st.switch_page("pages/1_abrir_chamado.py")
    
    if current_user['role'] in ['Técnico', 'Administrador']:
        if st.button("🎯 Chamados Técnicos", use_container_width=True):
            st.switch_page("pages/3_chamados_tecnicos.py")
    
    if current_user['role'] in ['Administrador']:
        if st.button("👥 Gerenciar Usuários", use_container_width=True):
            st.switch_page("pages/5_admin_usuarios.py")
    
    if current_user['role'] in ['Diretoria', 'Administrador']:
        if st.button("📊 Dashboard", use_container_width=True):
            st.switch_page("pages/4_dashboard_diretoria.py")
    
    st.markdown("---")
    st.markdown("### 📊 Resumo Rápido")
    quick_stats = {
        'Total': len(user_tickets),
        'Pendentes': len([t for t in user_tickets if t[5] == 'Pendente']),
        'Em Andamento': len([t for t in user_tickets if t[5] == 'Em Andamento']),
        'Resolvidos': len([t for t in user_tickets if t[5] == 'Resolvido'])
    }
    
    for label, value in quick_stats.items():
        st.metric(label, value)
