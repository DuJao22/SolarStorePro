
// Admin Dashboard Scripts

document.addEventListener('DOMContentLoaded', function() {
    // Mobile menu toggle
    const mobileMenuToggle = document.querySelector('.mobile-menu-toggle');
    const sidebar = document.querySelector('.admin-sidebar');
    const sidebarOverlay = document.querySelector('.sidebar-overlay');
    
    if (mobileMenuToggle && sidebar && sidebarOverlay) {
        mobileMenuToggle.addEventListener('click', function() {
            sidebar.classList.toggle('open');
            sidebarOverlay.classList.toggle('active');
        });
        
        sidebarOverlay.addEventListener('click', function() {
            sidebar.classList.remove('open');
            sidebarOverlay.classList.remove('active');
        });

        // Fechar menu ao clicar em um link (mobile)
        const navLinks = sidebar.querySelectorAll('.nav-link');
        navLinks.forEach(link => {
            link.addEventListener('click', function() {
                if (window.innerWidth <= 1024) {
                    sidebar.classList.remove('open');
                    sidebarOverlay.classList.remove('active');
                }
            });
        });
    }

    // Auto-hide flash messages
    setTimeout(() => {
        const flashMessages = document.querySelectorAll('.flash, .alert');
        flashMessages.forEach(msg => {
            msg.style.transition = 'opacity 0.5s';
            msg.style.opacity = '0';
            setTimeout(() => msg.remove(), 500);
        });
    }, 5000);

    // Search functionality
    const searchInput = document.querySelector('.search-input');
    if (searchInput) {
        searchInput.addEventListener('input', function(e) {
            const searchTerm = e.target.value.toLowerCase();
            const tableRows = document.querySelectorAll('.data-table tbody tr');
            
            tableRows.forEach(row => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(searchTerm) ? '' : 'none';
            });
        });
    }

    // Confirmação para ações perigosas
    const dangerButtons = document.querySelectorAll('[data-confirm]');
    dangerButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm(this.dataset.confirm)) {
                e.preventDefault();
            }
        });
    });

    // Preview de imagem
    const imageInputs = document.querySelectorAll('input[type="file"][accept*="image"]');
    imageInputs.forEach(input => {
        input.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    const preview = document.querySelector(`#preview-${input.id}`);
                    if (preview) {
                        preview.src = e.target.result;
                        preview.style.display = 'block';
                    }
                };
                reader.readAsDataURL(file);
            }
        });
    });

    // Animação dos cards de estatísticas
    const statCards = document.querySelectorAll('.stat-card');
    statCards.forEach((card, index) => {
        setTimeout(() => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(20px)';
            setTimeout(() => {
                card.style.transition = 'all 0.5s ease';
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }, 50);
        }, index * 100);
    });
});

// Função para upload de imagem
async function uploadImage(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch('/admin/upload-imagem', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.sucesso) {
            return data.filename;
        } else {
            alert('Erro ao fazer upload: ' + data.erro);
            return null;
        }
    } catch (error) {
        alert('Erro ao fazer upload da imagem');
        console.error(error);
        return null;
    }
}

// Assistente IA
async function enviarMensagemAssistente() {
    const input = document.getElementById('assistente-input');
    const chatBox = document.getElementById('assistente-chat');
    const mensagem = input.value.trim();
    
    if (!mensagem) return;
    
    // Adicionar mensagem do usuário
    const userMsg = document.createElement('div');
    userMsg.className = 'chat-message user-message';
    userMsg.textContent = mensagem;
    chatBox.appendChild(userMsg);
    
    input.value = '';
    chatBox.scrollTop = chatBox.scrollHeight;
    
    // Mostrar loading
    const loadingMsg = document.createElement('div');
    loadingMsg.className = 'chat-message assistant-message loading';
    loadingMsg.textContent = 'Pensando...';
    chatBox.appendChild(loadingMsg);
    chatBox.scrollTop = chatBox.scrollHeight;
    
    try {
        const response = await fetch('/admin/assistente/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ mensagem })
        });
        
        const data = await response.json();
        
        loadingMsg.remove();
        
        const assistantMsg = document.createElement('div');
        assistantMsg.className = 'chat-message assistant-message';
        assistantMsg.textContent = data.resposta || data.erro;
        chatBox.appendChild(assistantMsg);
        chatBox.scrollTop = chatBox.scrollHeight;
        
    } catch (error) {
        loadingMsg.remove();
        
        const errorMsg = document.createElement('div');
        errorMsg.className = 'chat-message assistant-message error';
        errorMsg.textContent = 'Erro ao conectar com o assistente.';
        chatBox.appendChild(errorMsg);
    }
}
