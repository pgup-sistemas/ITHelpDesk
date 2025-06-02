
import streamlit as st
from datetime import datetime
from .database import save_feedback

def display_header():
    """Exibe o cabeçalho do sistema com informações do usuário e empresa"""
    
    # Dados dinâmicos da sessão
    user_info = st.session_state.get('user_info', {})
    usuario_logado = user_info.get('username', 'Usuário')
    versao_sistema = "v1.0.3"
    ano_atual = datetime.now().year

    # Cabeçalho principal
    st.markdown(f"""
    <div style="background-color:#f0f2f6;padding:10px 20px;border-radius:10px;margin-bottom:20px;">
      <strong>👤 Usuário logado:</strong> {usuario_logado} &nbsp;&nbsp;|&nbsp;&nbsp;
      <strong>🧾 Versão do sistema:</strong> {versao_sistema} &nbsp;&nbsp;|&nbsp;&nbsp;
      <strong>👨‍💻 Desenvolvedor:</strong> <a href="https://github.com/pgup-sistemas" target="_blank">PgUp Sistemas</a>
    </div>
    """, unsafe_allow_html=True)

    # Suporte técnico
    with st.expander("📞 Suporte Técnico - PgUp Sistemas"):
        st.markdown(f"""
        **PgUp Sistemas**  
        📧 [pageupsistemas@gmail.com](mailto:pageupsistemas@gmail.com)  
        📱 (69) 99388-2222  
        🌐 [GitHub - pgup-sistemas](https://github.com/pgup-sistemas)
        
        ---
        
        **Horário de atendimento:**  
        📅 Segunda a Sexta: 08:00 às 18:00  
        📅 Sábado: 08:00 às 12:00  
        
        *Para emergências, utilize o WhatsApp.*
        """)

    # Bloco de feedback opcional
    with st.expander("💬 Enviar feedback"):
        feedback = st.text_area("Digite aqui seu feedback ou sugestão:", key="feedback_text")
        
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("Enviar feedback", key="send_feedback"):
                if feedback.strip():
                    try:
                        # Salva o feedback no banco de dados
                        user_id = user_info.get('id', 0)
                        save_feedback(user_id, feedback.strip())
                        st.success("✅ Obrigado! Seu feedback foi enviado com sucesso.")
                        st.session_state.feedback_text = ""  # Limpa o campo
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Erro ao enviar feedback: {str(e)}")
                else:
                    st.warning("⚠️ Por favor, digite seu feedback antes de enviar.")
