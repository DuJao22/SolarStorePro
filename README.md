# SolarPro - E-commerce de Placas Solares

🌞 **Desenvolvido por João Layon - Desenvolvedor Full Stack**

## Descrição

E-commerce profissional e completo para venda de placas solares com foco em conversão, credibilidade e experiência do usuário. Sistema desenvolvido com animações WOW, calculadora de ROI interativa e design responsivo otimizado para dispositivos móveis.

## Tecnologias Utilizadas

- **Backend:** Python 3.11 + Flask
- **Database:** SQLite3 (preparado para migração para SQLiteCloud)
- **Frontend:** HTML5 + CSS3 + JavaScript Vanilla
- **Animações:** AOS (Animate On Scroll)
- **Deploy:** Otimizado para Render

## Funcionalidades

✅ Hero animado com CTAs persuasivos
✅ Catálogo de produtos com filtros (potência, preço, eficiência)
✅ Páginas de produto individuais com galeria e especificações técnicas
✅ Calculadora interativa de ROI
✅ Carrinho de compras persistente (localStorage)
✅ Checkout simplificado em 2 passos
✅ Seção de depoimentos e projetos realizados
✅ Formulário de orçamento com envio de email
✅ Design responsivo mobile-first
✅ Animações on-scroll e microinterações
✅ Otimizado para SEO

## Instalação Local

```bash
# Instalar dependências
pip install -r requirements.txt

# Inicializar banco de dados
python database.py

# Rodar aplicação
python app.py
```

Acesse: `http://localhost:5000`

## Deploy no Render

1. Conecte seu repositório ao Render
2. Configure as variáveis de ambiente:
   - `SESSION_SECRET`: Chave secreta para sessões
3. O deploy será automático!

## Estrutura do Projeto

```
/
├── app.py                 # Aplicação Flask principal
├── database.py            # Gerenciamento do banco de dados
├── requirements.txt       # Dependências Python
├── Procfile              # Configuração Render
├── templates/            # Templates Jinja2
│   ├── base.html
│   ├── index.html
│   ├── produtos.html
│   ├── produto.html
│   ├── calculadora.html
│   ├── sobre.html
│   ├── contato.html
│   ├── checkout.html
│   └── 404.html
└── static/
    ├── css/style.css     # Estilos
    ├── js/main.js        # Scripts
    └── images/           # Imagens e assets

## Paleta de Cores

- **Verde Escuro:** #0B6A4A (primário)
- **Amarelo Ouro:** #FFC857 (secundário/CTAs)
- **Cinza Escuro:** #2D3436 (texto)
- **Branco:** #FFFFFF (background)

## Database Schema

### Produtos
- Painéis solares com especificações técnicas completas
- Inversores e kits completos
- Sistema de estoque

### Depoimentos
- Avaliações de clientes com foto
- Rating de 1-5 estrelas

### Projetos
- Cases de sucesso com fotos antes/depois
- Economia mensal e potência instalada

### Pedidos
- Histórico completo de vendas
- Informações de cliente e endereço

### Contatos
- Formulários de orçamento
- Lead generation

## Próximas Implementações

- [ ] Integração com gateway de pagamento (Stripe/MercadoPago)
- [ ] Migração para SQLiteCloud
- [ ] Painel administrativo
- [ ] Blog otimizado para SEO
- [ ] Sistema de agendamento
- [ ] Animações avançadas com GSAP
- [ ] Integração com CRM

## Créditos

**Desenvolvido por:** João Layon - Desenvolvedor Full Stack

## Licença

Copyright © 2025 SolarPro. Todos os direitos reservados.
