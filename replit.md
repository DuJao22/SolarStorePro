# Loja de Placas Solares - E-commerce Profissional

## Visão Geral
E-commerce completo e profissional para venda de placas solares com foco em conversão, credibilidade e experiência do usuário. Sistema desenvolvido com animações WOW, calculadora de ROI interativa e design responsivo otimizado para dispositivos móveis.

**Desenvolvido por:** João Layon - Desenvolvedor Full Stack

## Arquitetura do Projeto

### Tech Stack
- **Backend:** Python 3.11 + Flask
- **Database:** SQLite3 (preparado para migração futura para SQLiteCloud)
- **Frontend:** HTML5 responsivo + CSS3 + JavaScript vanilla
- **Animações:** AOS (Animate On Scroll) + CSS animations
- **Deployment:** Otimizado para Render

### Estrutura de Diretórios
```
/
├── app.py                 # Aplicação Flask principal
├── database.py            # Inicialização e gerenciamento do banco
├── requirements.txt       # Dependências Python
├── templates/            # Templates Jinja2
│   ├── base.html         # Template base
│   ├── index.html        # Home page
│   ├── produtos.html     # Catálogo
│   ├── produto.html      # Página individual
│   ├── calculadora.html  # ROI calculator
│   ├── sobre.html        # Sobre a empresa
│   ├── contato.html      # Contato/orçamento
│   └── checkout.html     # Checkout
└── static/
    ├── css/             # Estilos
    ├── js/              # Scripts
    └── images/          # Imagens e assets
```

## Funcionalidades Principais

### MVP (Versão Atual)
- ✅ Hero animado com CTAs persuasivos
- ✅ Catálogo de produtos com filtros (potência, preço, eficiência)
- ✅ Páginas de produto individuais com galeria e especificações
- ✅ Calculadora interativa de ROI
- ✅ Carrinho de compras persistente (localStorage)
- ✅ Checkout simplificado em 2 passos
- ✅ Seção de depoimentos e projetos
- ✅ Formulário de orçamento com envio de email
- ✅ Design responsivo mobile-first
- ✅ Animações on-scroll e microinterações
- ✅ Página Sobre com certificações

### Próximas Fases
- 🔄 Integração com gateway de pagamento (Stripe/MercadoPago)
- 🔄 Migração para SQLiteCloud
- 🔄 Painel administrativo completo
- 🔄 Blog otimizado para SEO
- 🔄 Sistema de agendamento
- 🔄 Animações avançadas com GSAP
- 🔄 Integração com CRM

## Design System

### Paleta de Cores
- **Verde Escuro:** #0B6A4A (primário)
- **Amarelo Ouro:** #FFC857 (secundário/CTAs)
- **Cinza Escuro:** #2D3436 (texto)
- **Branco:** #FFFFFF (background)

### Tipografia
- **Títulos:** Merriweather (serifada, elegante)
- **Corpo:** Inter (sans-serif, moderna)

### Componentes Visuais
- Cards com sombras suaves e bordas arredondadas
- Hover effects com scale 1.03
- Animações fade-in on scroll
- Progress indicators no checkout

## Database Schema

### Tabela: produtos
- id, nome, descricao, preco, potencia_watts, eficiencia, garantia, estoque, imagem, categoria

### Tabela: depoimentos
- id, nome, cargo, texto, foto, avaliacao, data

### Tabela: projetos
- id, titulo, descricao, local, economia_mensal, imagem_antes, imagem_depois

### Tabela: pedidos
- id, nome_cliente, email, telefone, endereco, produtos_json, total, status, data

### Tabela: contatos
- id, nome, email, telefone, mensagem, data

## SEO & Performance
- Meta tags únicas por página
- Schema.org markup (Product, Review, Organization)
- Lazy loading de imagens
- Minificação de CSS/JS
- Lighthouse target: Performance ≥ 80, Accessibility ≥ 90

## Deploy (Render)
Configurado com:
- Gunicorn como WSGI server
- Bind em 0.0.0.0:5000
- Variáveis de ambiente para produção
- SSL automático

## Mudanças Recentes
- 2025-11-25: Projeto inicial criado com estrutura completa
- Desenvolvido por João Layon - Desenvolvedor Full Stack

## Preferências do Usuário
- Stack: Python + Flask + SQLite3
- Deploy: Render
- Design: Animado, persuasivo, mobile-first
- Foco: Conversão e credibilidade
