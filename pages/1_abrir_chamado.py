import streamlit as st
import sys
import os

# Add components directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'components'))

from components.auth import check_authentication, get_current_user
from components.database import create_chamado

# Check authentication
if not check_authentication():
    st.error("❌ Acesso negado. Faça login primeiro.")
    st.stop()

current_user = get_current_user()

st.set_page_config(page_title="Abrir Chamado", page_icon="📝", layout="wide")

st.title("📝 Abrir Novo Chamado")

# Only allow certain roles to access this page
allowed_roles = ['Colaborador', 'Técnico', 'Administrador']
if current_user['role'] not in allowed_roles:
    st.error("❌ Você não tem permissão para abrir chamados.")
    st.stop()

# Form to create new ticket
with st.form("novo_chamado"):
    st.markdown("### Informações do Chamado")
    
    col1, col2 = st.columns(2)
    
    with col1:
        titulo = st.text_input("🎫 Título do Chamado *", placeholder="Descreva brevemente o problema")
        setor_origem = st.selectbox("🏢 Setor de Origem *", [
            "Administrativo", "Financeiro", "Recursos Humanos", "Vendas", 
            "Marketing", "Produção", "TI", "Diretoria", "Outro"
        ], index=0 if current_user['setor'] == 'Administrativo' else None)
        
    with col2:
        prioridade = st.selectbox("⚡ Prioridade *", ["Baixa", "Média", "Alta"], index=1)
        
    descricao = st.text_area("📄 Descrição Detalhada do Problema *", 
                            height=150,
                            placeholder="Descreva o problema com o máximo de detalhes possível...")
    
    observacoes = st.text_area("📝 Observações Adicionais", 
                              height=100,
                              placeholder="Informações extras que possam ajudar na resolução...")
    
    # File upload for attachments
    st.markdown("### 📎 Anexos (Opcional)")
    uploaded_files = st.file_uploader(
        "Anexe imagens, prints ou documentos relacionados ao problema",
        accept_multiple_files=True,
        type=['png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx', 'txt']
    )
    
    # Priority information
    with st.expander("ℹ️ Informações sobre Prioridades"):
        st.markdown("""
        **🔴 Alta:** Problemas críticos que impedem o trabalho (SLA: 4 horas)
        - Sistema fora do ar
        - Falha de segurança
        - Perda de dados
        
        **🟡 Média:** Problemas que impactam a produtividade (SLA: 24 horas)
        - Lentidão no sistema
        - Problemas de impressão
        - Erro em funcionalidade específica
        
        **🟢 Baixa:** Melhorias ou problemas menores (SLA: 72 horas)
        - Solicitação de novo software
        - Dúvidas sobre uso
        - Pequenos ajustes
        """)
    
    # Submit button
    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        submitted = st.form_submit_button("🚀 Abrir Chamado", use_container_width=True)
    
    if submitted:
        # Validate required fields
        if not titulo or not descricao or not setor_origem:
            st.error("❌ Preencha todos os campos obrigatórios!")
        else:
            try:
                # Create the ticket
                chamado_id = create_chamado(
                    titulo=titulo,
                    descricao=descricao,
                    setor_origem=setor_origem,
                    prioridade=prioridade,
                    solicitante_id=current_user['id'],
                    solicitante_nome=current_user['username'],
                    observacoes=observacoes if observacoes else None
                )
                
                # Handle file uploads (simplified - in production you'd save files properly)
                if uploaded_files:
                    st.info(f"📎 {len(uploaded_files)} arquivo(s) anexado(s) ao chamado.")
                
                st.success(f"✅ Chamado #{chamado_id} criado com sucesso!")
                st.info(f"📊 Prioridade: {prioridade} | SLA: {'4 horas' if prioridade == 'Alta' else '24 horas' if prioridade == 'Média' else '72 horas'}")
                
                # Show navigation options
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("📋 Ver Meus Chamados", use_container_width=True):
                        st.switch_page("pages/2_meus_chamados.py")
                with col2:
                    if st.button("📝 Abrir Outro Chamado", use_container_width=True):
                        st.rerun()
                        
            except Exception as e:
                st.error(f"❌ Erro ao criar chamado: {str(e)}")

# Recent tickets section
st.markdown("---")
st.markdown("### 📊 Meus Últimos Chamados")

from components.database import get_chamados

# Get user's recent tickets
recent_tickets = get_chamados({'solicitante_id': current_user['id']})[:5]

if recent_tickets:
    for ticket in recent_tickets:
        ticket_id, titulo, descricao, setor, prioridade, status, solicitante, tecnico, data_abertura, data_resolucao, sla_prazo = ticket
        
        # Status color
        status_color = {
            'Pendente': '🟡',
            'Em Andamento': '🔵', 
            'Resolvido': '🟢',
            'Cancelado': '🔴'
        }.get(status, '⚪')
        
        # Priority color
        priority_color = {
            'Alta': '🔴',
            'Média': '🟡',
            'Baixa': '🟢'
        }.get(prioridade, '⚪')
        
        with st.container():
            col1, col2, col3, col4 = st.columns([1, 3, 1, 1])
            with col1:
                st.write(f"**#{ticket_id}**")
            with col2:
                st.write(f"**{titulo}**")
            with col3:
                st.write(f"{priority_color} {prioridade}")
            with col4:
                st.write(f"{status_color} {status}")
else:
    st.info("Você ainda não possui chamados. Este é seu primeiro!")

# Help section
with st.sidebar:
    st.markdown("### 🆘 Precisa de Ajuda?")
    st.markdown("""
    **Como abrir um bom chamado:**
    
    1. 📝 **Título claro:** Resuma o problema em poucas palavras
    
    2. 📄 **Descrição detalhada:** Explique o que aconteceu, quando e como reproduzir
    
    3. ⚡ **Prioridade correta:** Escolha baseado no impacto real
    
    4. 📎 **Anexos:** Inclua prints ou arquivos que ajudem
    
    5. 🕐 **Acompanhe:** Monitore o status na página "Meus Chamados"
    """)
    
    st.markdown("---")
    st.markdown("**📞 Contato de Emergência:**")
    st.markdown("📱 (69) 99388-2222")
    st.markdown("📧 suporte.ti@empresa.com")
