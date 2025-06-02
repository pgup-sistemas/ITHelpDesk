import streamlit as st
from datetime import datetime, timedelta
import sqlite3
import pandas as pd

def format_datetime(dt_string, format_type="display"):
    """Format datetime string for display or calculations"""
    try:
        dt = datetime.strptime(dt_string, '%Y-%m-%d %H:%M:%S')
        if format_type == "display":
            return dt.strftime('%d/%m/%Y às %H:%M')
        elif format_type == "date_only":
            return dt.strftime('%d/%m/%Y')
        elif format_type == "time_only":
            return dt.strftime('%H:%M')
        else:
            return dt
    except:
        return dt_string

def calculate_time_difference(start_time, end_time):
    """Calculate time difference between two datetime strings"""
    try:
        start = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
        end = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')
        diff = end - start
        
        days = diff.days
        hours, remainder = divmod(diff.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        
        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"
    except:
        return "N/A"

def get_sla_status(sla_deadline, current_status):
    """Get SLA status based on deadline and current ticket status"""
    if not sla_deadline or current_status == 'Resolvido':
        return {"status": "N/A", "color": "gray", "icon": "⚪"}
    
    try:
        deadline = datetime.strptime(sla_deadline, '%Y-%m-%d %H:%M:%S')
        now = datetime.now()
        time_diff = (deadline - now).total_seconds()
        
        if time_diff < 0:
            return {"status": "SLA Vencido", "color": "red", "icon": "🔴"}
        elif time_diff < 3600:  # Less than 1 hour
            return {"status": "SLA Crítico", "color": "orange", "icon": "🟠"}
        elif time_diff < 7200:  # Less than 2 hours
            return {"status": "SLA Próximo", "color": "yellow", "icon": "🟡"}
        else:
            return {"status": "SLA OK", "color": "green", "icon": "🟢"}
    except:
        return {"status": "SLA Indefinido", "color": "gray", "icon": "⚪"}

def get_priority_info(priority):
    """Get priority information with colors and icons"""
    priority_map = {
        'Alta': {"color": "red", "icon": "🔴", "sla_hours": 4},
        'Média': {"color": "orange", "icon": "🟡", "sla_hours": 24},
        'Baixa': {"color": "green", "icon": "🟢", "sla_hours": 72}
    }
    return priority_map.get(priority, {"color": "gray", "icon": "⚪", "sla_hours": 24})

def get_status_info(status):
    """Get status information with colors and icons"""
    status_map = {
        'Pendente': {"color": "orange", "icon": "🟡", "description": "Aguardando atribuição"},
        'Em Andamento': {"color": "blue", "icon": "🔵", "description": "Sendo atendido"},
        'Resolvido': {"color": "green", "icon": "🟢", "description": "Concluído"},
        'Cancelado': {"color": "red", "icon": "🔴", "description": "Cancelado"}
    }
    return status_map.get(status, {"color": "gray", "icon": "⚪", "description": "Status desconhecido"})

def validate_user_permissions(user_role, required_roles):
    """Validate if user has required permissions"""
    return user_role in required_roles

def format_file_size(size_bytes):
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

def generate_ticket_summary(ticket_data):
    """Generate a summary for a ticket"""
    ticket_id, titulo, descricao, setor, prioridade, status, solicitante, tecnico, data_abertura, data_resolucao, sla_prazo = ticket_data
    
    summary = {
        'id': ticket_id,
        'title': titulo,
        'priority': get_priority_info(prioridade),
        'status': get_status_info(status),
        'sla': get_sla_status(sla_prazo, status),
        'duration': calculate_time_difference(data_abertura, data_resolucao) if data_resolucao else None,
        'open_duration': calculate_time_difference(data_abertura, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    }
    
    return summary

def export_to_csv(data, filename_prefix="export"):
    """Export data to CSV format"""
    if not data:
        return None
    
    df = pd.DataFrame(data)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{filename_prefix}_{timestamp}.csv"
    
    return df.to_csv(index=False), filename

def sanitize_input(input_text):
    """Sanitize user input to prevent basic security issues"""
    if not input_text:
        return ""
    
    # Remove potential script tags and other dangerous content
    dangerous_patterns = ['<script', '</script>', 'javascript:', 'on', 'eval(']
    
    sanitized = str(input_text)
    for pattern in dangerous_patterns:
        sanitized = sanitized.replace(pattern.lower(), '')
        sanitized = sanitized.replace(pattern.upper(), '')
    
    return sanitized.strip()

def create_notification(message, notification_type="info"):
    """Create a notification message"""
    notification_types = {
        'success': st.success,
        'error': st.error,
        'warning': st.warning,
        'info': st.info
    }
    
    notification_func = notification_types.get(notification_type, st.info)
    notification_func(message)

def get_business_hours_duration(start_time, end_time):
    """Calculate duration considering only business hours (8 AM to 6 PM, Mon-Fri)"""
    try:
        start = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
        end = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')
        
        # Simplified calculation - in production, you'd implement proper business hours logic
        total_hours = (end - start).total_seconds() / 3600
        
        # Rough estimation: assume 50% of time is during business hours
        business_hours = total_hours * 0.5
        
        return round(business_hours, 1)
    except:
        return 0

def generate_dashboard_metrics(tickets_data):
    """Generate metrics for dashboard display"""
    if not tickets_data:
        return {
            'total': 0,
            'pending': 0,
            'in_progress': 0,
            'resolved': 0,
            'avg_resolution_time': 0,
            'sla_compliance': 0
        }
    
    total = len(tickets_data)
    pending = len([t for t in tickets_data if t[5] == 'Pendente'])
    in_progress = len([t for t in tickets_data if t[5] == 'Em Andamento'])
    resolved = len([t for t in tickets_data if t[5] == 'Resolvido'])
    
    # Calculate average resolution time
    resolution_times = []
    sla_compliant = 0
    total_with_sla = 0
    
    for ticket in tickets_data:
        if ticket[5] == 'Resolvido' and ticket[8] and ticket[9]:  # Has open and resolution dates
            try:
                open_date = datetime.strptime(ticket[8], '%Y-%m-%d %H:%M:%S')
                resolve_date = datetime.strptime(ticket[9], '%Y-%m-%d %H:%M:%S')
                resolution_time = (resolve_date - open_date).total_seconds() / 3600  # hours
                resolution_times.append(resolution_time)
                
                # Check SLA compliance
                if ticket[10]:  # Has SLA deadline
                    sla_deadline = datetime.strptime(ticket[10], '%Y-%m-%d %H:%M:%S')
                    if resolve_date <= sla_deadline:
                        sla_compliant += 1
                    total_with_sla += 1
            except:
                continue
    
    avg_resolution_time = round(sum(resolution_times) / len(resolution_times), 1) if resolution_times else 0
    sla_compliance = round((sla_compliant / total_with_sla) * 100, 1) if total_with_sla > 0 else 0
    
    return {
        'total': total,
        'pending': pending,
        'in_progress': in_progress,
        'resolved': resolved,
        'avg_resolution_time': avg_resolution_time,
        'sla_compliance': sla_compliance
    }

def create_ticket_card(ticket_data, current_user, show_actions=False):
    """Create a standardized ticket card display"""
    summary = generate_ticket_summary(ticket_data)
    
    # Card container
    with st.container():
        # Header row
        col1, col2, col3, col4 = st.columns([1, 3, 1, 1])
        
        with col1:
            st.markdown(f"**#{summary['id']}**")
        
        with col2:
            st.markdown(f"**{summary['title']}**")
        
        with col3:
            st.markdown(f"{summary['priority']['icon']} {ticket_data[4]}")
        
        with col4:
            st.markdown(f"{summary['status']['icon']} {ticket_data[5]}")
        
        # Expandable details
        with st.expander(f"Detalhes do chamado #{summary['id']}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"**📄 Descrição:** {ticket_data[2]}")
                st.markdown(f"**🏢 Setor:** {ticket_data[3]}")
                st.markdown(f"**👤 Solicitante:** {ticket_data[6]}")
                if ticket_data[7]:
                    st.markdown(f"**🔧 Técnico:** {ticket_data[7]}")
            
            with col2:
                st.markdown(f"**📅 Abertura:** {format_datetime(ticket_data[8])}")
                if ticket_data[9]:
                    st.markdown(f"**✅ Resolução:** {format_datetime(ticket_data[9])}")
                st.markdown(f"**⏱️ SLA:** {summary['sla']['icon']} {summary['sla']['status']}")
            
            if show_actions:
                st.markdown("---")
                # Add action buttons here based on user permissions and ticket status
                pass

def log_user_action(user_id, action, details=None):
    """Log user actions for audit purposes"""
    conn = sqlite3.connect('data/chamados.db')
    cursor = conn.cursor()
    
    # Create audit log table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            details TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES usuarios (id)
        )
    """)
    
    cursor.execute("""
        INSERT INTO audit_log (user_id, action, details)
        VALUES (?, ?, ?)
    """, (user_id, action, details))
    
    conn.commit()
    conn.close()

def check_system_health():
    """Check system health and return status"""
    try:
        conn = sqlite3.connect('data/chamados.db')
        cursor = conn.cursor()
        
        # Check if main tables exist and have data
        cursor.execute("SELECT COUNT(*) FROM usuarios")
        users_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM chamados")
        tickets_count = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'status': 'healthy',
            'users': users_count,
            'tickets': tickets_count,
            'timestamp': datetime.now()
        }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now()
        }
