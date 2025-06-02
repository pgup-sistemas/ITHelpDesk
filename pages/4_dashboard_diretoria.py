import streamlit as st
import sys
import os
from datetime import datetime, timedelta

# Add components directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'components'))

from components.auth import check_authentication, get_current_user
from components.database import get_analytics_data, get_quick_stats, get_chamados

# Check authentication
if not check_authentication():
    st.error("❌ Acesso negado. Faça login primeiro.")
    st.stop()

current_user = get_current_user()

# Only allow directors and admins
if current_user and current_user['role'] not in ['Diretoria', 'Administrador']:
    st.error("❌ Acesso negado. Esta página é apenas para diretoria e administradores.")
    st.stop()

st.set_page_config(page_title="Dashboard Diretoria", page_icon="📊", layout="wide")

st.title("📊 Dashboard Gerencial - Diretoria")
st.markdown("Análise completa do desempenho do sistema de chamados de TI")

# Get analytics data
analytics_data = get_analytics_data()
quick_stats = get_quick_stats()

# === KPI SECTION ===
st.markdown("## 📋 Indicadores Principais (KPIs)")

col1, col2, col3, col4, col5, col6 = st.columns(6)

with col1:
    st.metric("📊 Total de Chamados", quick_stats['total'])

with col2:
    st.metric("⏳ Pendentes", quick_stats['pendentes'], 
              delta=quick_stats['pendentes'] - quick_stats['em_andamento'])

with col3:
    st.metric("🔧 Em Andamento", quick_stats['em_andamento'])

with col4:
    st.metric("✅ Resolvidos", quick_stats['resolvidos'])

with col5:
    # Calculate resolution rate
    if quick_stats['total'] > 0:
        resolution_rate = round((quick_stats['resolvidos'] / quick_stats['total']) * 100, 1)
    else:
        resolution_rate = 0
    st.metric("📈 Taxa de Resolução", f"{resolution_rate}%")

with col6:
    # Calculate average resolution time
    all_tickets = get_chamados()
    resolved_tickets = [t for t in all_tickets if t[5] == 'Resolvido' and t[9]]
    
    if resolved_tickets:
        total_hours = 0
        count = 0
        for ticket in resolved_tickets:
            try:
                open_date = datetime.strptime(ticket[8], '%Y-%m-%d %H:%M:%S')
                resolve_date = datetime.strptime(ticket[9], '%Y-%m-%d %H:%M:%S')
                hours = (resolve_date - open_date).total_seconds() / 3600
                total_hours += hours
                count += 1
            except:
                continue
        avg_hours = round(total_hours / count, 1) if count > 0 else 0
    else:
        avg_hours = 0
    
    st.metric("⏱️ Tempo Médio (horas)", avg_hours)

st.markdown("---")

# === CHARTS SECTION ===
col1, col2 = st.columns(2)

# Chart 1: Tickets by Status
with col1:
    st.markdown("### 📊 Distribuição por Status")
    
    if analytics_data['by_status']:
        status_data = analytics_data['by_status']
        
        for status, count in status_data:
            status_icon = {
                'Pendente': '🟡',
                'Em Andamento': '🔵', 
                'Resolvido': '🟢',
                'Cancelado': '🔴'
            }.get(status, '⚪')
            
            st.markdown(f"{status_icon} **{status}:** {count} chamados")
    else:
        st.info("Nenhum dado disponível")

# Chart 2: Tickets by Priority
with col2:
    st.markdown("### ⚡ Distribuição por Prioridade")
    
    if analytics_data['by_priority']:
        priority_data = analytics_data['by_priority']
        
        for priority, count in priority_data:
            priority_icon = {
                'Alta': '🔴',
                'Média': '🟡',
                'Baixa': '🟢'
            }.get(priority, '⚪')
            
            st.markdown(f"{priority_icon} **{priority}:** {count} chamados")
    else:
        st.info("Nenhum dado disponível")

# Chart 3: Tickets by Sector
st.markdown("### 🏢 Chamados por Setor")

if analytics_data['by_sector']:
    sector_data = analytics_data['by_sector']
    sector_data.sort(key=lambda x: x[1], reverse=True)  # Sort by count
    
    for sector, count in sector_data:
        st.markdown(f"🏢 **{sector}:** {count} chamados")
else:
    st.info("Nenhum dado disponível")

# Chart 4: Technician Performance
st.markdown("### 👨‍💻 Desempenho dos Técnicos")

if analytics_data['technician_performance']:
    tech_data = analytics_data['technician_performance']
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🎯 Chamados Resolvidos")
        for tech, resolved, avg_days in tech_data:
            st.markdown(f"👨‍💻 **{tech}:** {resolved} chamados resolvidos")
    
    with col2:
        st.markdown("#### ⏱️ Tempo Médio de Resolução")
        for tech, resolved, avg_days in tech_data:
            avg_hours = round(avg_days * 24, 1) if avg_days else 0
            st.markdown(f"⏱️ **{tech}:** {avg_hours} horas em média")
else:
    st.info("Nenhum dado de desempenho disponível")

st.markdown("---")

# === SLA ANALYSIS ===
st.markdown("## ⏰ Análise de SLA")

col1, col2, col3 = st.columns(3)

# Calculate SLA compliance
all_tickets = get_chamados()
sla_compliant = 0
sla_violated = 0
sla_critical = 0

for ticket in all_tickets:
    if ticket[5] == 'Resolvido' and ticket[9] and ticket[10]:  # Has resolution and SLA deadline
        try:
            resolve_date = datetime.strptime(ticket[9], '%Y-%m-%d %H:%M:%S')
            sla_deadline = datetime.strptime(ticket[10], '%Y-%m-%d %H:%M:%S')
            
            if resolve_date <= sla_deadline:
                sla_compliant += 1
            else:
                sla_violated += 1
        except:
            continue
    elif ticket[5] != 'Resolvido' and ticket[10]:  # Open ticket with SLA
        try:
            sla_deadline = datetime.strptime(ticket[10], '%Y-%m-%d %H:%M:%S')
            now = datetime.now()
            
            if now > sla_deadline:
                sla_violated += 1
            elif (sla_deadline - now).total_seconds() < 3600:  # Less than 1 hour
                sla_critical += 1
        except:
            continue

total_sla_tickets = sla_compliant + sla_violated
sla_compliance_rate = round((sla_compliant / total_sla_tickets) * 100, 1) if total_sla_tickets > 0 else 0

with col1:
    st.metric("✅ SLA Cumprido", f"{sla_compliance_rate}%", 
              delta=f"{sla_compliant} chamados")

with col2:
    st.metric("❌ SLA Violado", sla_violated, delta="chamados")

with col3:
    st.metric("🚨 SLA Crítico", sla_critical, delta="< 1 hora")

st.markdown("---")

# === EXPORT SECTION ===
st.markdown("## 📁 Exportação de Relatórios")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📊 Exportar Dados Gerais", use_container_width=True):
        # Prepare general data for export
        all_tickets = get_chamados()
        if all_tickets:
            import pandas as pd
            df = pd.DataFrame(all_tickets, columns=[
                'ID', 'Título', 'Descrição', 'Setor', 'Prioridade', 'Status',
                'Solicitante', 'Técnico', 'Data_Abertura', 'Data_Resolução', 'SLA_Prazo'
            ])
            
            csv = df.to_csv(index=False)
            st.download_button(
                label="⬇️ Baixar CSV",
                data=csv,
                file_name=f"chamados_geral_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )

with col2:
    if st.button("⏰ Exportar Análise SLA", use_container_width=True):
        # Prepare SLA analysis for export
        sla_analysis = []
        for ticket in all_tickets:
            if ticket[10]:  # Has SLA deadline
                sla_status = "Indefinido"
                try:
                    sla_deadline = datetime.strptime(ticket[10], '%Y-%m-%d %H:%M:%S')
                    if ticket[5] == 'Resolvido' and ticket[9]:
                        resolve_date = datetime.strptime(ticket[9], '%Y-%m-%d %H:%M:%S')
                        sla_status = "Cumprido" if resolve_date <= sla_deadline else "Violado"
                    elif ticket[5] != 'Resolvido':
                        now = datetime.now()
                        sla_status = "Violado" if now > sla_deadline else "Em Andamento"
                except:
                    pass
                
                sla_analysis.append([
                    ticket[0], ticket[1], ticket[4], ticket[5], 
                    ticket[8], ticket[9], ticket[10], sla_status
                ])
        
        if sla_analysis:
            import pandas as pd
            sla_df = pd.DataFrame(sla_analysis, columns=[
                'ID', 'Título', 'Prioridade', 'Status', 
                'Data_Abertura', 'Data_Resolução', 'SLA_Prazo', 'SLA_Status'
            ])
            
            csv = sla_df.to_csv(index=False)
            st.download_button(
                label="⬇️ Baixar Análise SLA",
                data=csv,
                file_name=f"analise_sla_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )

with col3:
    if st.button("👨‍💻 Exportar Desempenho Técnicos", use_container_width=True):
        # Prepare technician performance for export
        if analytics_data['technician_performance']:
            import pandas as pd
            tech_df = pd.DataFrame(analytics_data['technician_performance'], 
                                  columns=['Técnico', 'Chamados_Resolvidos', 'Tempo_Médio_Dias'])
            
            csv = tech_df.to_csv(index=False)
            st.download_button(
                label="⬇️ Baixar Desempenho",
                data=csv,
                file_name=f"desempenho_tecnicos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )

# === REAL-TIME MONITORING ===
st.markdown("## 🔄 Monitoramento em Tempo Real")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 🚨 Alertas Ativos")
    
    # Check for overdue tickets
    overdue_count = 0
    for ticket in all_tickets:
        if ticket[5] != 'Resolvido' and ticket[10]:
            try:
                sla_deadline = datetime.strptime(ticket[10], '%Y-%m-%d %H:%M:%S')
                if datetime.now() > sla_deadline:
                    overdue_count += 1
            except:
                continue
    
    if overdue_count > 0:
        st.error(f"🚨 {overdue_count} chamado(s) com SLA vencido")
    
    # Check for high priority pending tickets
    high_priority_pending = len([t for t in all_tickets if t[4] == 'Alta' and t[5] == 'Pendente'])
    if high_priority_pending > 0:
        st.warning(f"⚡ {high_priority_pending} chamado(s) de alta prioridade pendente(s)")
    
    # Check for unassigned tickets older than 2 hours
    unassigned_old = 0
    for ticket in all_tickets:
        if ticket[5] == 'Pendente' and not ticket[7]:  # No technician assigned
            try:
                open_date = datetime.strptime(ticket[8], '%Y-%m-%d %H:%M:%S')
                hours_open = (datetime.now() - open_date).total_seconds() / 3600
                if hours_open > 2:
                    unassigned_old += 1
            except:
                continue
    
    if unassigned_old > 0:
        st.warning(f"⏰ {unassigned_old} chamado(s) não atribuído(s) há mais de 2 horas")
    
    if overdue_count == 0 and high_priority_pending == 0 and unassigned_old == 0:
        st.success("✅ Nenhum alerta ativo no momento")

with col2:
    st.markdown("### 📊 Estatísticas da Última Hora")
    
    # Calculate statistics for last hour
    one_hour_ago = datetime.now() - timedelta(hours=1)
    recent_tickets = []
    
    for ticket in all_tickets:
        try:
            open_date = datetime.strptime(ticket[8], '%Y-%m-%d %H:%M:%S')
            if open_date >= one_hour_ago:
                recent_tickets.append(ticket)
        except:
            continue
    
    st.metric("🆕 Novos Chamados", len(recent_tickets))
    
    # Recent resolutions
    recent_resolutions = []
    for ticket in all_tickets:
        if ticket[9]:  # Has resolution date
            try:
                resolve_date = datetime.strptime(ticket[9], '%Y-%m-%d %H:%M:%S')
                if resolve_date >= one_hour_ago:
                    recent_resolutions.append(ticket)
            except:
                continue
    
    st.metric("✅ Resoluções", len(recent_resolutions))
    
    # Average response time for new tickets
    if recent_tickets:
        assigned_count = len([t for t in recent_tickets if t[7]])  # Has technician
        response_rate = round((assigned_count / len(recent_tickets)) * 100, 1)
        st.metric("⚡ Taxa de Resposta", f"{response_rate}%")

# Auto-refresh option
st.markdown("---")
if st.button("🔄 Atualizar Dashboard", use_container_width=False):
    st.rerun()

# Footer with last update time
st.markdown(f"*Última atualização: {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}*")