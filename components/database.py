import sqlite3
import os
from datetime import datetime, timedelta
import hashlib

def hash_password(password):
    """Hash a password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def init_database():
    """Initialize the SQLite database with all required tables"""
    # Create data directory if it doesn't exist
    os.makedirs('data', exist_ok=True)

    conn = sqlite3.connect('data/chamados.db')
    cursor = conn.cursor()

    # Create usuarios table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            nome_completo TEXT NOT NULL,
            email TEXT,
            role TEXT NOT NULL CHECK (role IN ('Colaborador', 'Técnico', 'Administrador', 'Diretoria')),
            setor TEXT NOT NULL,
            ativo BOOLEAN DEFAULT 1,
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create chamados table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chamados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            descricao TEXT NOT NULL,
            setor_origem TEXT NOT NULL,
            prioridade TEXT NOT NULL CHECK (prioridade IN ('Alta', 'Média', 'Baixa')),
            status TEXT NOT NULL DEFAULT 'Pendente' CHECK (status IN ('Pendente', 'Em Andamento', 'Resolvido', 'Cancelado')),
            solicitante_id INTEGER NOT NULL,
            solicitante_nome TEXT NOT NULL,
            tecnico_id INTEGER,
            tecnico_nome TEXT,
            observacoes TEXT,
            resolucao TEXT,
            data_abertura TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data_atribuicao TIMESTAMP,
            data_resolucao TIMESTAMP,
            sla_prazo TIMESTAMP,
            anexos TEXT,
            FOREIGN KEY (solicitante_id) REFERENCES usuarios (id),
            FOREIGN KEY (tecnico_id) REFERENCES usuarios (id)
        )
    """)

    # Create historico_chamados table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historico_chamados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chamado_id INTEGER NOT NULL,
            usuario_id INTEGER NOT NULL,
            usuario_nome TEXT NOT NULL,
            acao TEXT NOT NULL,
            detalhes TEXT,
            data_acao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (chamado_id) REFERENCES chamados (id),
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        )
    """)

    # Create chat_messages table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chamado_id INTEGER NOT NULL,
            usuario_id INTEGER NOT NULL,
            username TEXT NOT NULL,
            mensagem TEXT NOT NULL,
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (chamado_id) REFERENCES chamados (id),
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        )
    """)

    # Create default users if they don't exist
    default_users = [
        ('admin', 'admin123', 'Administrador Sistema', 'admin@empresa.com', 'Administrador', 'TI'),
        ('tecnico', 'tecnico123', 'Técnico TI', 'tecnico@empresa.com', 'Técnico', 'TI'),
        ('user', 'user123', 'Usuário Colaborador', 'user@empresa.com', 'Colaborador', 'Administrativo'),
        ('diretor', 'diretor123', 'Diretor Geral', 'diretor@empresa.com', 'Diretoria', 'Diretoria')
    ]

    for username, password, nome, email, role, setor in default_users:
        cursor.execute("SELECT id FROM usuarios WHERE username = ?", (username,))
        if not cursor.fetchone():
            password_hash = hash_password(password)
            cursor.execute("""
                INSERT INTO usuarios (username, password_hash, nome_completo, email, role, setor)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (username, password_hash, nome, email, role, setor))

    conn.commit()
    conn.close()

def calculate_sla_deadline(prioridade):
    """Calculate SLA deadline based on priority"""
    now = datetime.now()
    if prioridade == 'Alta':
        return now + timedelta(hours=4)  # 4 hours
    elif prioridade == 'Média':
        return now + timedelta(hours=24)  # 24 hours
    else:  # Baixa
        return now + timedelta(hours=72)  # 72 hours

def create_chamado(titulo, descricao, setor_origem, prioridade, solicitante_id, solicitante_nome, observacoes=None):
    """Create a new ticket"""
    conn = sqlite3.connect('data/chamados.db')
    cursor = conn.cursor()

    sla_prazo = calculate_sla_deadline(prioridade)

    cursor.execute("""
        INSERT INTO chamados (titulo, descricao, setor_origem, prioridade, solicitante_id, solicitante_nome, observacoes, sla_prazo)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (titulo, descricao, setor_origem, prioridade, solicitante_id, solicitante_nome, observacoes, sla_prazo))

    chamado_id = cursor.lastrowid

    # Add to history
    cursor.execute("""
        INSERT INTO historico_chamados (chamado_id, usuario_id, usuario_nome, acao, detalhes)
        VALUES (?, ?, ?, ?, ?)
    """, (chamado_id, solicitante_id, solicitante_nome, 'Criação', f'Chamado criado com prioridade {prioridade}'))

    conn.commit()
    conn.close()

    return chamado_id

def get_chamados(filters=None):
    """Get tickets with optional filters"""
    conn = sqlite3.connect('data/chamados.db')
    cursor = conn.cursor()

    query = """
        SELECT id, titulo, descricao, setor_origem, prioridade, status, 
               solicitante_nome, tecnico_nome, data_abertura, data_resolucao, sla_prazo
        FROM chamados
        WHERE 1=1
    """
    params = []

    if filters:
        if filters.get('status'):
            query += " AND status = ?"
            params.append(filters['status'])
        if filters.get('prioridade'):
            query += " AND prioridade = ?"
            params.append(filters['prioridade'])
        if filters.get('setor'):
            query += " AND setor_origem = ?"
            params.append(filters['setor'])
        if filters.get('solicitante_id'):
            query += " AND solicitante_id = ?"
            params.append(filters['solicitante_id'])
        if filters.get('tecnico_id'):
            query += " AND tecnico_id = ?"
            params.append(filters['tecnico_id'])

    query += " ORDER BY data_abertura DESC"

    cursor.execute(query, params)
    chamados = cursor.fetchall()
    conn.close()

    return chamados

def get_chamado_by_id(chamado_id):
    """Get a specific ticket by ID"""
    conn = sqlite3.connect('data/chamados.db')
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM chamados WHERE id = ?
    """, (chamado_id,))

    chamado = cursor.fetchone()
    conn.close()

    return chamado

def update_chamado_status(chamado_id, new_status, user_id, user_name, detalhes=None):
    """Update ticket status"""
    conn = sqlite3.connect('data/chamados.db')
    cursor = conn.cursor()

    update_fields = ["status = ?"]
    params = [new_status]

    if new_status == 'Resolvido':
        update_fields.append("data_resolucao = ?")
        params.append(datetime.now())

    params.append(chamado_id)

    cursor.execute(f"""
        UPDATE chamados 
        SET {', '.join(update_fields)}
        WHERE id = ?
    """, params)

    # Add to history
    cursor.execute("""
        INSERT INTO historico_chamados (chamado_id, usuario_id, usuario_nome, acao, detalhes)
        VALUES (?, ?, ?, ?, ?)
    """, (chamado_id, user_id, user_name, f'Status alterado para {new_status}', detalhes))

    conn.commit()
    conn.close()

def assign_technician(chamado_id, tecnico_id, tecnico_nome, user_id, user_name):
    """Assign a technician to a ticket"""
    conn = sqlite3.connect('data/chamados.db')
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE chamados 
        SET tecnico_id = ?, tecnico_nome = ?, data_atribuicao = ?, status = 'Em Andamento'
        WHERE id = ?
    """, (tecnico_id, tecnico_nome, datetime.now(), chamado_id))

    # Add to history
    cursor.execute("""
        INSERT INTO historico_chamados (chamado_id, usuario_id, usuario_nome, acao, detalhes)
        VALUES (?, ?, ?, ?, ?)
    """, (chamado_id, user_id, user_name, 'Atribuição', f'Chamado atribuído para {tecnico_nome}'))

    conn.commit()
    conn.close()

def get_quick_stats():
    """Get quick statistics for dashboard"""
    conn = sqlite3.connect('data/chamados.db')
    cursor = conn.cursor()

    # Total tickets
    cursor.execute("SELECT COUNT(*) FROM chamados")
    total = cursor.fetchone()[0]

    # Pending tickets
    cursor.execute("SELECT COUNT(*) FROM chamados WHERE status = 'Pendente'")
    pendentes = cursor.fetchone()[0]

    # In progress tickets
    cursor.execute("SELECT COUNT(*) FROM chamados WHERE status = 'Em Andamento'")
    em_andamento = cursor.fetchone()[0]

    # Resolved tickets
    cursor.execute("SELECT COUNT(*) FROM chamados WHERE status = 'Resolvido'")
    resolvidos = cursor.fetchone()[0]

    conn.close()

    return {
        'total': total,
        'pendentes': pendentes,
        'em_andamento': em_andamento,
        'resolvidos': resolvidos
    }

def get_analytics_data():
    """Get data for analytics dashboard"""
    conn = sqlite3.connect('data/chamados.db')
    cursor = conn.cursor()

    # Tickets by priority
    cursor.execute("""
        SELECT prioridade, COUNT(*) as count
        FROM chamados
        GROUP BY prioridade
    """)
    tickets_by_priority = cursor.fetchall()

    # Tickets by status
    cursor.execute("""
        SELECT status, COUNT(*) as count
        FROM chamados
        GROUP BY status
    """)
    tickets_by_status = cursor.fetchall()

    # Tickets by sector
    cursor.execute("""
        SELECT setor_origem, COUNT(*) as count
        FROM chamados
        GROUP BY setor_origem
        ORDER BY count DESC
    """)
    tickets_by_sector = cursor.fetchall()

    # Technician performance
    cursor.execute("""
        SELECT tecnico_nome, COUNT(*) as total_chamados,
               AVG(julianday(data_resolucao) - julianday(data_abertura)) as avg_resolution_days
        FROM chamados
        WHERE tecnico_nome IS NOT NULL AND status = 'Resolvido'
        GROUP BY tecnico_nome
        ORDER BY total_chamados DESC
    """)
    technician_performance = cursor.fetchall()

    # Tickets over time (last 30 days)
    cursor.execute("""
        SELECT DATE(data_abertura) as date, COUNT(*) as count
        FROM chamados
        WHERE data_abertura >= date('now', '-30 days')
        GROUP BY DATE(data_abertura)
        ORDER BY date
    """)
    tickets_over_time = cursor.fetchall()

    conn.close()

    return {
        'by_priority': tickets_by_priority,
        'by_status': tickets_by_status,
        'by_sector': tickets_by_sector,
        'technician_performance': technician_performance,
        'over_time': tickets_over_time
    }

def get_usuarios():
    """Get all users"""
    conn = sqlite3.connect('data/chamados.db')
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, username, nome_completo, email, role, setor, ativo
        FROM usuarios
        ORDER BY nome_completo
    """)

    users = cursor.fetchall()
    conn.close()
    return users

def get_tecnicos():
    """Get all technicians"""
    conn = sqlite3.connect('data/chamados.db')
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, username, nome_completo
        FROM usuarios
        WHERE role IN ('Técnico', 'Administrador') AND ativo = 1
        ORDER BY nome_completo
    """)

    technicians = cursor.fetchall()
    conn.close()
    return technicians

def save_feedback(user_id, feedback_text):
    """Save user feedback to database"""
    conn = sqlite3.connect('data/chamados.db')
    cursor = conn.cursor()

    # Create feedback table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            feedback_text TEXT NOT NULL,
            data_envio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES usuarios (id)
        )
    """)

    # Insert feedback
    cursor.execute("""
        INSERT INTO feedback (user_id, feedback_text)
        VALUES (?, ?)
    """, (user_id, feedback_text))

    conn.commit()
    conn.close()