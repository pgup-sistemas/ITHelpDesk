import streamlit as st
import sys
import os
import pandas as pd
from datetime import datetime

# Add components directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'components'))

from components.auth import check_authentication, get_current_user, require_role
from components.database import get_chamados, assign_technician, get_tecnicos, update_chamado_status
from components.chat import display_chat

# Check authentication
if not check_authentication():
    st.error("❌ Acesso negado. Faça login primeiro.")
    st.stop()

current_user = get_current_user()

# Only allow technicians, admins, and directors
if current_user['role'] not in ['Técnico', 'Administrador', 'Diretoria']:
    st.error("❌ Acesso negado. Esta página é apenas para técnicos, administradores e diretoria.")
    st.stop()

st.set_page_config(page_title="Chamados Técnicos", page_icon="🎯", layout="wide")

st.title("🎯 Gestão de Chamados - Área Técnica")

# Get all tickets
all_tickets = get_chamados()

# Dashboard tabs
tab1, tab2, tab3 = st.tabs(["🎫 Todos os Chamados", "⏳ Pendentes", "🔧 Em Andamento"])

with tab1:
    st.markdown("### 📊 Visão Geral dos Chamados")
    
    # Quick stats
    col1, col2, col3, col4 = st.columns(4)
    
    total = len(all_tickets)
    pendentes = len([t for t in all_tickets if t[5] == 'Pendente'])
    em_andamento = len([t for t in all_tickets if t[5] == 'Em Andamento'])
    resolvidos = len([t for t in all_tickets if t[5] == 'Resolvido'])
    
    with col1:
        st.metric("Total", total)
    with col2:
        st.metric("Pendentes", pendentes, delta=f"{pendentes - em_andamento}")
    with col3:
        st.metric("Em Andamento", em_andamento)
    with col4:
        st.metric("Resolvidos", resolvidos)
    
    # Filters
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        status_filter = st.selectbox("📊 Status", ["Todos", "Pendente", "Em Andamento", "Resolvido", "Cancelado"])
    with col2:
        priority_filter = st.selectbox("⚡ Prioridade", ["Todas", "Alta", "Média", "Baixa"])
    with col3:
        sector_filter = st.selectbox("🏢 Setor", ["Todos", "Administrativo", "Financeiro", "RH", "Vendas", "Marketing", "Produção", "TI", "Diretoria"])
    with col4:
        # Get technicians for filter
        tecnicos = get_tecnicos()
        tecnico_names = ["Todos"] + [f"{t[2]}" for t in tecnicos]
        technician_filter = st.selectbox("👨‍💻 Técnico", tecnico_names)
    
    # Apply filters
    filtered_tickets = all_tickets
    if status_filter != "Todos":
        filtered_tickets = [t for t in filtered_tickets if t[5] == status_filter]
    if priority_filter != "Todas":
        filtered_tickets = [t for t in filtered_tickets if t[4] == priority_filter]
    if sector_filter != "Todos":
        filtered_tickets = [t for t in filtered_tickets if t[3] == sector_filter]
    if technician_filter != "Todos":
        filtered_tickets = [t for t in filtered_tickets if t[7] == technician_filter]
    
    # Display filtered tickets
    display_tickets_list(filtered_tickets, current_user, show_actions=True)

with tab2:
    st.markdown("### ⏳ Chamados Pendentes de Atribuição")
    
    pending_tickets = [t for t in all_tickets if t[5] == 'Pendente']
    
    if pending_tickets:
        st.info(f"📋 {len(pending_tickets)} chamado(s) aguardando atribuição de técnico.")
        
        # Sort by priority and date
        pending_tickets.sort(key=lambda x: (
            {'Alta': 0, 'Média': 1, 'Baixa': 2}.get(x[4], 3),  # Priority
            x[8]  # Date
        ))
        
        display_tickets_list(pending_tickets, current_user, show_actions=True, highlight_pending=True)
    else:
        st.success("🎉 Todos os chamados foram atribuídos!")

with tab3:
    st.markdown("### 🔧 Chamados Em Andamento")
    
    in_progress_tickets = [t for t in all_tickets if t[5] == 'Em Andamento']
    
    if in_progress_tickets:
        st.info(f"⚙️ {len(in_progress_tickets)} chamado(s) em atendimento.")
        display_tickets_list(in_progress_tickets, current_user, show_actions=True)
    else:
        st.info("📭 Nenhum chamado em andamento no momento.")

def display_tickets_list(tickets, current_user, show_actions=False, highlight_pending=False):
    """Display a list of tickets with optional actions"""
    
    if not tickets:
        st.info("📭 Nenhum chamado encontrado.")
        return
    
    for ticket in tickets:
        ticket_id, titulo, descricao, setor, prioridade, status, solicitante, tecnico, data_abertura, data_resolucao, sla_prazo = ticket
        
        # Status and priority indicators
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
        
        # SLA calculation
        sla_status = ""
        sla_color = ""
        if sla_prazo and status != 'Resolvido':
            try:
                sla_deadline = datetime.strptime(sla_prazo, '%Y-%m-%d %H:%M:%S')
                now = datetime.now()
                time_diff = (sla_deadline - now).total_seconds()
                
                if time_diff < 0:
                    sla_status = "⚠️ SLA Vencido"
                    sla_color = "red"
                elif time_diff < 3600:  # Less than 1 hour
                    sla_status = "🚨 SLA Crítico"
                    sla_color = "orange"
                else:
                    hours_left = int(time_diff // 3600)
                    sla_status = f"⏰ {hours_left}h restantes"
                    sla_color = "green"
            except:
                sla_status = "⏰ SLA indefinido"
        
        # Ticket container
        container_style = "border-left: 4px solid #ff4444;" if highlight_pending and prioridade == 'Alta' else ""
        
        with st.container():
            if container_style:
                st.markdown(f'<div style="{container_style}">', unsafe_allow_html=True)
            
            # Ticket header
            col1, col2, col3, col4 = st.columns([1, 4, 1, 1])
            
            with col1:
                st.markdown(f"**#{ticket_id}**")
            with col2:
                st.markdown(f"**{titulo}**")
            with col3:
                st.markdown(f"{priority_colors.get(prioridade, '⚪')} {prioridade}")
            with col4:
                st.markdown(f"{status_colors.get(status, '⚪')} {status}")
            
            # Expandable details
            with st.expander(f"Ver detalhes do chamado #{ticket_id}"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"**📄 Descrição:**\n{descricao}")
                    st.markdown(f"**🏢 Setor:** {setor}")
                    st.markdown(f"**👤 Solicitante:** {solicitante}")
                    if tecnico:
                        st.markdown(f"**🔧 Técnico Responsável:** {tecnico}")
                
                with col2:
                    st.markdown(f"**📅 Data de Abertura:** {data_abertura}")
                    if data_resolucao:
                        st.markdown(f"**✅ Data de Resolução:** {data_resolucao}")
                    if sla_status:
                        st.markdown(f"**⏱️ SLA:** {sla_status}")
                
                # Actions for technicians and admins
                if show_actions and current_user['role'] in ['Técnico', 'Administrador']:
                    st.markdown("---")
                    
                    if status == 'Pendente':
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            if st.button(f"👋 Assumir Chamado", key=f"assume_{ticket_id}"):
                                assign_technician(ticket_id, current_user['id'], current_user['username'],
                                               current_user['id'], current_user['username'])
                                st.success("Chamado assumido com sucesso!")
                                st.rerun()
                        
                        # Admin can assign to other technicians
                        if current_user['role'] == 'Administrador':
                            with col2:
                                with st.form(f"assign_form_{ticket_id}"):
                                    tecnicos = get_tecnicos()
                                    tecnico_options = {f"{t[2]}": t[0] for t in tecnicos}
                                    selected_tech = st.selectbox("Atribuir para:", list(tecnico_options.keys()), key=f"tech_select_{ticket_id}")
                                    
                                    if st.form_submit_button("👥 Atribuir"):
                                        tech_id = tecnico_options[selected_tech]
                                        assign_technician(ticket_id, tech_id, selected_tech,
                                                       current_user['id'], current_user['username'])
                                        st.success(f"Chamado atribuído para {selected_tech}!")
                                        st.rerun()
                    
                    elif status == 'Em Andamento':
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            if st.button(f"✅ Resolver", key=f"resolve_{ticket_id}"):
                                st.session_state[f'resolving_{ticket_id}'] = True
                                st.rerun()
                        
                        with col2:
                            if st.button(f"📝 Atualizar", key=f"update_{ticket_id}"):
                                st.session_state[f'updating_{ticket_id}'] = True
                                st.rerun()
                        
                        # Admin can reassign
                        if current_user['role'] == 'Administrador':
                            with col3:
                                if st.button(f"🔄 Reatribuir", key=f"reassign_{ticket_id}"):
                                    st.session_state[f'reassigning_{ticket_id}'] = True
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
                                st.markdown("### 📝 Atualizar Chamado")
                                new_status = st.selectbox("Status:", ['Em Andamento', 'Pendente'])
                                update_notes = st.text_area("Observações:", height=80)
                                
                                col1, col2 = st.columns(2)
                                with col1:
                                    if st.form_submit_button("💾 Salvar"):
                                        update_chamado_status(ticket_id, new_status, current_user['id'],
                                                            current_user['username'], update_notes)
                                        st.success("Chamado atualizado!")
                                        del st.session_state[f'updating_{ticket_id}']
                                        st.rerun()
                                with col2:
                                    if st.form_submit_button("❌ Cancelar"):
                                        del st.session_state[f'updating_{ticket_id}']
                                        st.rerun()
                        
                        # Reassign form (admin only)
                        if st.session_state.get(f'reassigning_{ticket_id}', False):
                            with st.form(f"reassign_form_{ticket_id}"):
                                st.markdown("### 🔄 Reatribuir Chamado")
                                tecnicos = get_tecnicos()
                                tecnico_options = {f"{t[2]}": t[0] for t in tecnicos}
                                selected_tech = st.selectbox("Novo técnico:", list(tecnico_options.keys()))
                                reassign_reason = st.text_area("Motivo da reatribuição:", height=60)
                                
                                col1, col2 = st.columns(2)
                                with col1:
                                    if st.form_submit_button("🔄 Reatribuir"):
                                        tech_id = tecnico_options[selected_tech]
                                        assign_technician(ticket_id, tech_id, selected_tech,
                                                       current_user['id'], current_user['username'])
                                        st.success(f"Chamado reatribuído para {selected_tech}!")
                                        del st.session_state[f'reassigning_{ticket_id}']
                                        st.rerun()
                                with col2:
                                    if st.form_submit_button("❌ Cancelar"):
                                        del st.session_state[f'reassigning_{ticket_id}']
                                        st.rerun()
                
                # Chat section
                if current_user['role'] in ['Técnico', 'Administrador'] or (tecnico and current_user['username'] in tecnico):
                    st.markdown("---")
                    display_chat(ticket_id, current_user)
            
            st.markdown("---")

# Call the function to display tickets
if 'filtered_tickets' in locals():
    pass  # Already handled in tabs

# Sidebar with quick actions
with st.sidebar:
    st.markdown("### 🚀 Ações Rápidas")
    
    if current_user['role'] == 'Administrador':
        if st.button("👥 Gerenciar Usuários", use_container_width=True):
            st.switch_page("pages/5_admin_usuarios.py")
        
        if st.button("📊 Dashboard", use_container_width=True):
            st.switch_page("pages/4_dashboard_diretoria.py")
    
    if st.button("📋 Meus Chamados", use_container_width=True):
        st.switch_page("pages/2_meus_chamados.py")
    
    st.markdown("---")
    st.markdown("### 📈 Estatísticas Rápidas")
    
    # Quick stats for current user
    if current_user['role'] == 'Técnico':
        my_tickets = [t for t in all_tickets if t[7] == current_user['username']]
        st.metric("Meus Chamados", len(my_tickets))
        st.metric("Em Andamento", len([t for t in my_tickets if t[5] == 'Em Andamento']))
        st.metric("Resolvidos", len([t for t in my_tickets if t[5] == 'Resolvido']))
    
    # SLA alerts
    sla_critical = [t for t in all_tickets if t[5] != 'Resolvido' and t[10]]
    critical_count = 0
    for ticket in sla_critical:
        try:
            sla_deadline = datetime.strptime(ticket[10], '%Y-%m-%d %H:%M:%S')
            if datetime.now() > sla_deadline:
                critical_count += 1
        except:
            pass
    
    if critical_count > 0:
        st.error(f"🚨 {critical_count} chamado(s) com SLA vencido!")
