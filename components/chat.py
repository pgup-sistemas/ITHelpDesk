import streamlit as st
import sqlite3
from datetime import datetime

def init_chat_table():
    """Initialize chat messages table"""
    conn = sqlite3.connect('data/chamados.db')
    cursor = conn.cursor()
    
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
    
    conn.commit()
    conn.close()

def send_message(chamado_id, user_id, username, message):
    """Send a chat message"""
    if not message.strip():
        return False
    
    conn = sqlite3.connect('data/chamados.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO chat_messages (chamado_id, usuario_id, username, mensagem)
        VALUES (?, ?, ?, ?)
    """, (chamado_id, user_id, username, message.strip()))
    
    conn.commit()
    conn.close()
    return True

def get_chat_messages(chamado_id):
    """Get all chat messages for a ticket"""
    conn = sqlite3.connect('data/chamados.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT username, mensagem, data_criacao
        FROM chat_messages
        WHERE chamado_id = ?
        ORDER BY data_criacao ASC
    """, (chamado_id,))
    
    messages = cursor.fetchall()
    conn.close()
    return messages

def display_chat(chamado_id, current_user):
    """Display chat interface for a ticket"""
    st.markdown("### 💬 Chat Interno")
    
    # Initialize chat table if needed
    init_chat_table()
    
    # Display messages
    messages = get_chat_messages(chamado_id)
    
    if messages:
        chat_container = st.container()
        with chat_container:
            for username, message, timestamp in messages:
                # Parse timestamp
                try:
                    dt = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                    formatted_time = dt.strftime('%d/%m/%Y às %H:%M')
                except:
                    formatted_time = timestamp
                
                # Display message with different styling based on sender
                if username == current_user['username']:
                    st.markdown(f"""
                    <div style='text-align: right; margin: 10px 0;'>
                        <div style='background-color: #007bff; color: white; padding: 10px; border-radius: 10px; display: inline-block; max-width: 70%;'>
                            {message}
                        </div>
                        <div style='font-size: 0.8em; color: #666; margin-top: 5px;'>
                            Você • {formatted_time}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style='text-align: left; margin: 10px 0;'>
                        <div style='background-color: #f1f3f4; color: black; padding: 10px; border-radius: 10px; display: inline-block; max-width: 70%;'>
                            {message}
                        </div>
                        <div style='font-size: 0.8em; color: #666; margin-top: 5px;'>
                            {username} • {formatted_time}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
    else:
        st.info("Nenhuma mensagem ainda. Seja o primeiro a enviar!")
    
    # Message input form
    with st.form(f"chat_form_{chamado_id}", clear_on_submit=True):
        message_input = st.text_area("Digite sua mensagem:", height=80, placeholder="Escreva sua mensagem aqui...")
        col1, col2 = st.columns([3, 1])
        
        with col2:
            submit_button = st.form_submit_button("📤 Enviar", use_container_width=True)
        
        if submit_button and message_input:
            if send_message(chamado_id, current_user['id'], current_user['username'], message_input):
                st.success("Mensagem enviada!")
                st.rerun()
            else:
                st.error("Erro ao enviar mensagem.")

def get_unread_messages_count(chamado_id, user_id):
    """Get count of unread messages for a user in a ticket"""
    # This is a simplified version - in a real app you'd track read status
    return 0

def mark_messages_as_read(chamado_id, user_id):
    """Mark messages as read for a user"""
    # Implementation for marking messages as read
    pass
