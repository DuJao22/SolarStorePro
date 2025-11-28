import sqlite3
import json
from datetime import datetime
from werkzeug.security import generate_password_hash

def init_db():
    conn = sqlite3.connect('solarpro.db')
    c = conn.cursor()

    # Tabela de usuários (clientes e admins)
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        senha_hash TEXT NOT NULL,
        telefone TEXT,
        cpf TEXT,
        endereco TEXT,
        cidade TEXT,
        estado TEXT,
        cep TEXT,
        tipo TEXT DEFAULT 'cliente',
        ativo INTEGER DEFAULT 1,
        data_cadastro TEXT,
        ultimo_acesso TEXT
    )''')

    # Tabela de produtos
    c.execute('''CREATE TABLE IF NOT EXISTS produtos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        descricao TEXT,
        preco REAL NOT NULL,
        preco_promocional REAL,
        potencia_watts INTEGER NOT NULL,
        eficiencia REAL NOT NULL,
        garantia INTEGER NOT NULL,
        estoque INTEGER DEFAULT 0,
        estoque_minimo INTEGER DEFAULT 5,
        imagem TEXT,
        categoria TEXT,
        especificacoes TEXT,
        ativo INTEGER DEFAULT 1,
        destaque INTEGER DEFAULT 0,
        vendas INTEGER DEFAULT 0,
        data_cadastro TEXT
    )''')

    # Tabela de depoimentos
    c.execute('''CREATE TABLE IF NOT EXISTS depoimentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        cargo TEXT,
        texto TEXT NOT NULL,
        foto TEXT,
        avaliacao INTEGER DEFAULT 5,
        data TEXT
    )''')

    # Tabela de projetos
    c.execute('''CREATE TABLE IF NOT EXISTS projetos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        titulo TEXT NOT NULL,
        descricao TEXT,
        local TEXT,
        economia_mensal REAL,
        potencia_instalada INTEGER,
        imagem_antes TEXT,
        imagem_depois TEXT,
        data TEXT
    )''')

    # Carrinho persistente (para rastrear abandonados)
    c.execute('''CREATE TABLE IF NOT EXISTS carrinhos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER,
        session_id TEXT,
        produtos_json TEXT NOT NULL,
        total REAL DEFAULT 0,
        status TEXT DEFAULT 'ativo',
        data_criacao TEXT,
        data_atualizacao TEXT,
        data_abandono TEXT,
        notificado INTEGER DEFAULT 0,
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
    )''')

    # Tabela de pedidos
    c.execute('''CREATE TABLE IF NOT EXISTS pedidos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER,
        nome_cliente TEXT NOT NULL,
        email TEXT NOT NULL,
        telefone TEXT,
        cpf TEXT,
        endereco TEXT,
        cidade TEXT,
        estado TEXT,
        cep TEXT,
        produtos_json TEXT NOT NULL,
        subtotal REAL NOT NULL,
        desconto REAL DEFAULT 0,
        frete REAL DEFAULT 0,
        total REAL NOT NULL,
        cupom_usado TEXT,
        metodo_pagamento TEXT,
        status_pagamento TEXT DEFAULT 'pendente',
        status_pedido TEXT DEFAULT 'aguardando_pagamento',
        mercadopago_id TEXT,
        mercadopago_status TEXT,
        observacoes TEXT,
        data TEXT,
        data_pagamento TEXT,
        data_envio TEXT,
        data_entrega TEXT,
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
    )''')

    # Tabela de contatos
    c.execute('''CREATE TABLE IF NOT EXISTS contatos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        email TEXT NOT NULL,
        telefone TEXT,
        assunto TEXT,
        mensagem TEXT NOT NULL,
        respondido INTEGER DEFAULT 0,
        data TEXT
    )''')

    # Configurações do sistema (chaves do Mercado Pago, etc)
    c.execute('''CREATE TABLE IF NOT EXISTS configuracoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chave TEXT UNIQUE NOT NULL,
        valor TEXT,
        descricao TEXT,
        tipo TEXT DEFAULT 'texto',
        data_atualizacao TEXT
    )''')

    # Lista de desejos
    c.execute('''CREATE TABLE IF NOT EXISTS lista_desejos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER NOT NULL,
        produto_id INTEGER NOT NULL,
        data TEXT,
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
        FOREIGN KEY (produto_id) REFERENCES produtos(id),
        UNIQUE(usuario_id, produto_id)
    )''')

    # Cupons de desconto
    c.execute('''CREATE TABLE IF NOT EXISTS cupons (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo TEXT UNIQUE NOT NULL,
        descricao TEXT,
        tipo TEXT DEFAULT 'percentual',
        valor REAL NOT NULL,
        valor_minimo REAL DEFAULT 0,
        quantidade_total INTEGER,
        quantidade_usada INTEGER DEFAULT 0,
        ativo INTEGER DEFAULT 1,
        data_inicio TEXT,
        data_fim TEXT
    )''')

    # Logs de atividades do admin
    c.execute('''CREATE TABLE IF NOT EXISTS logs_admin (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER,
        acao TEXT NOT NULL,
        detalhes TEXT,
        ip TEXT,
        data TEXT,
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
    )''')

    # Avaliações de produtos
    c.execute('''CREATE TABLE IF NOT EXISTS avaliacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER NOT NULL,
        produto_id INTEGER NOT NULL,
        pedido_id INTEGER,
        nota INTEGER NOT NULL,
        comentario TEXT,
        aprovado INTEGER DEFAULT 0,
        data TEXT,
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
        FOREIGN KEY (produto_id) REFERENCES produtos(id)
    )''')

    # Criar admin padrão se não existir
    c.execute('SELECT COUNT(*) FROM usuarios WHERE tipo = "admin"')
    if c.fetchone()[0] == 0:
        senha_hash = generate_password_hash('admin123')
        c.execute('''INSERT INTO usuarios (nome, email, senha_hash, tipo, ativo, data_cadastro)
                     VALUES (?, ?, ?, ?, ?, ?)''',
                  ('Administrador', 'admin@solarpro.com', senha_hash, 'admin', 1, 
                   datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

    # Inserir configurações padrão
    configs_padrao = [
        ('mercadopago_access_token', '', 'Access Token do Mercado Pago', 'senha'),
        ('mercadopago_public_key', '', 'Public Key do Mercado Pago', 'texto'),
        ('mercadopago_sandbox', '1', 'Modo Sandbox (1=ativo, 0=produção)', 'boolean'),
        ('loja_nome', 'SolarPro', 'Nome da loja', 'texto'),
        ('loja_razao_social', 'SolarPro Energia Solar Ltda', 'Razão Social da empresa', 'texto'),
        ('loja_cnpj', '', 'CNPJ da empresa', 'texto'),
        ('loja_email', 'contato@solarpro.com', 'Email da loja', 'texto'),
        ('loja_telefone', '(11) 99999-9999', 'Telefone da loja', 'texto'),
        ('loja_whatsapp', '5511999999999', 'WhatsApp com código do país', 'texto'),
        ('loja_endereco', 'Av. Paulista, 1000 - Bela Vista', 'Endereço completo', 'texto'),
        ('loja_cidade', 'São Paulo', 'Cidade', 'texto'),
        ('loja_estado', 'SP', 'Estado (UF)', 'texto'),
        ('loja_horario', 'Seg-Sex: 8h às 18h | Sáb: 8h às 12h', 'Horário de atendimento', 'texto'),
        ('frete_gratis_acima', '5000', 'Frete grátis acima de (R$)', 'numero'),
        ('estoque_alerta', '5', 'Alertar quando estoque abaixo de', 'numero'),
        ('carrinho_abandono_horas', '24', 'Marcar carrinho como abandonado após (horas)', 'numero'),
        ('openai_api_key', '', 'Chave API do OpenAI para assistente IA', 'senha'),
    ]
    
    for config in configs_padrao:
        c.execute('''INSERT OR IGNORE INTO configuracoes (chave, valor, descricao, tipo, data_atualizacao)
                     VALUES (?, ?, ?, ?, ?)''',
                  (config[0], config[1], config[2], config[3], datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

    # Inserir produtos de exemplo se não existirem
    c.execute('SELECT COUNT(*) FROM produtos')
    if c.fetchone()[0] == 0:
        produtos_exemplo = [
            ('Painel Solar 550W Monocristalino', 'Placa solar de alta eficiência com células monocristalinas de última geração. Ideal para residências e pequenos comércios.', 1299.00, None, 550, 21.5, 25, 50, 5, 'painel-550w.jpg', 'Residencial', json.dumps({
                'dimensoes': '2278 x 1134 x 35 mm',
                'peso': '28.5 kg',
                'tipo_celula': 'Monocristalino PERC',
                'tensao_maxima': '49.5V',
                'corrente_maxima': '11.11A',
                'certificacoes': 'INMETRO, IEC 61215, IEC 61730'
            }), 1, 1, 0, datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
            ('Painel Solar 450W Policristalino', 'Excelente custo-benefício com tecnologia policristalina comprovada. Perfeito para projetos de médio porte.', 989.00, 899.00, 450, 18.2, 25, 75, 5, 'painel-450w.jpg', 'Residencial', json.dumps({
                'dimensoes': '2094 x 1038 x 35 mm',
                'peso': '24.8 kg',
                'tipo_celula': 'Policristalino',
                'tensao_maxima': '48.3V',
                'corrente_maxima': '9.32A',
                'certificacoes': 'INMETRO, IEC 61215'
            }), 1, 0, 0, datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
            ('Kit Solar Residencial 5kWp', 'Sistema completo com 10 painéis de 550W, inversor, estruturas e cabos. Instalação inclusa.', 24990.00, None, 5500, 21.5, 25, 15, 3, 'kit-5kwp.jpg', 'Kit Completo', json.dumps({
                'componentes': '10x Painel 550W + Inversor 5kW + Estruturas + Cabos',
                'area_necessaria': '30m²',
                'geracao_mensal': '650 kWh/mês',
                'instalacao': 'Inclusa',
                'garantia_inversor': '10 anos',
                'monitoramento': 'App mobile incluído'
            }), 1, 1, 0, datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
            ('Painel Solar 600W Half-Cell', 'Tecnologia Half-Cell para maior eficiência e menor perda por sombreamento. Top de linha.', 1599.00, None, 600, 22.8, 25, 30, 5, 'painel-600w.jpg', 'Comercial', json.dumps({
                'dimensoes': '2384 x 1303 x 35 mm',
                'peso': '32.5 kg',
                'tipo_celula': 'Monocristalino Half-Cell',
                'tensao_maxima': '45.8V',
                'corrente_maxima': '13.1A',
                'certificacoes': 'INMETRO, IEC 61215, IEC 61730, TUV'
            }), 1, 1, 0, datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
            ('Kit Solar Comercial 10kWp', 'Sistema industrial com 18 painéis de 550W. Ideal para comércios e pequenas indústrias.', 47990.00, 44990.00, 10000, 21.5, 25, 8, 2, 'kit-10kwp.jpg', 'Kit Completo', json.dumps({
                'componentes': '18x Painel 550W + Inversor 10kW Trifásico + Estruturas + Cabos',
                'area_necessaria': '55m²',
                'geracao_mensal': '1.300 kWh/mês',
                'instalacao': 'Inclusa',
                'garantia_inversor': '10 anos',
                'monitoramento': 'Sistema web completo'
            }), 1, 0, 0, datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
            ('Painel Solar 400W Bifacial', 'Tecnologia bifacial com captação de luz em ambos os lados. Até 30% mais eficiente.', 1399.00, None, 400, 20.5, 30, 40, 5, 'painel-400w-bifacial.jpg', 'Comercial', json.dumps({
                'dimensoes': '2008 x 1002 x 40 mm',
                'peso': '25.2 kg',
                'tipo_celula': 'Monocristalino Bifacial',
                'tensao_maxima': '48.2V',
                'corrente_maxima': '8.30A',
                'certificacoes': 'INMETRO, IEC 61215, IEC 61730, ISO 9001'
            }), 1, 0, 0, datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
            ('Inversor Solar 3kW String', 'Inversor string de alta qualidade com eficiência de 97.6%. Ideal para sistemas residenciais.', 2890.00, None, 3000, 97.6, 10, 25, 5, 'inversor-3kw.jpg', 'Inversor', json.dumps({
                'tipo': 'String Inverter',
                'potencia_nominal': '3000W',
                'tensao_entrada': '150-550V',
                'eficiencia_maxima': '97.6%',
                'protecoes': 'Sobretensão, Sobrecorrente, Ilhamento',
                'monitoramento': 'WiFi integrado'
            }), 1, 0, 0, datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
            ('Inversor Solar 5kW Híbrido', 'Inversor híbrido com backup de bateria. Autonomia mesmo sem rede elétrica.', 8990.00, 7990.00, 5000, 96.5, 10, 12, 3, 'inversor-5kw-hibrido.jpg', 'Inversor', json.dumps({
                'tipo': 'Inversor Híbrido',
                'potencia_nominal': '5000W',
                'tensao_bateria': '48V',
                'backup': 'Até 8 horas (com baterias)',
                'eficiencia_maxima': '96.5%',
                'monitoramento': 'WiFi + App mobile'
            }), 1, 1, 0, datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
            ('Kit Solar Off-Grid 3kWp', 'Sistema completo para locais sem rede elétrica. Inclui painéis, inversor e banco de baterias.', 32990.00, None, 3000, 21.0, 25, 5, 2, 'kit-offgrid-3kwp.jpg', 'Kit Completo', json.dumps({
                'componentes': '6x Painel 550W + Inversor 3kW + 4x Baterias 200Ah + Controlador',
                'autonomia': '2-3 dias sem sol',
                'area_necessaria': '18m²',
                'aplicacao': 'Casas de campo, sítios, áreas remotas',
                'instalacao': 'Inclusa'
            }), 1, 0, 0, datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
            ('Microinversor 600W', 'Microinversor para sistemas modulares. Máxima flexibilidade e monitoramento individual por painel.', 1290.00, None, 600, 96.8, 12, 35, 5, 'microinversor-600w.jpg', 'Inversor', json.dumps({
                'tipo': 'Microinversor',
                'potencia_nominal': '600W',
                'paineis_suportados': '1-2 painéis',
                'eficiencia_maxima': '96.8%',
                'vantagens': 'Sem ponto único de falha, expansível',
                'monitoramento': 'Painel a painel via app'
            }), 1, 0, 0, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        ]

        c.executemany('''INSERT INTO produtos 
            (nome, descricao, preco, preco_promocional, potencia_watts, eficiencia, garantia, estoque, estoque_minimo, imagem, categoria, especificacoes, ativo, destaque, vendas, data_cadastro)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', produtos_exemplo)

        # Depoimentos de exemplo
        depoimentos_exemplo = [
            ('Maria Silva', 'Empresária', 'Instalamos o sistema de 5kWp há 6 meses e a economia na conta de luz já pagou 30% do investimento! Equipe profissional e suporte excelente.', 'cliente1.jpg', 5, '2024-09-15'),
            ('Carlos Mendes', 'Engenheiro', 'Qualidade dos painéis surpreendente. Sistema funcionando perfeitamente, gerando até mais energia do que previsto. Recomendo!', 'cliente2.jpg', 5, '2024-10-20'),
            ('Ana Oliveira', 'Comerciante', 'Minha loja reduziu 85% da conta de energia. O investimento se pagará em menos de 3 anos. Melhor decisão que tomei para o negócio!', 'cliente3.jpg', 5, '2024-11-05'),
            ('Roberto Santos', 'Fazendeiro', 'Sistema off-grid perfeito para a fazenda. Finalmente temos energia confiável longe da cidade. Excelente custo-benefício!', 'cliente4.jpg', 5, '2024-08-10')
        ]

        c.executemany('''INSERT INTO depoimentos 
            (nome, cargo, texto, foto, avaliacao, data)
            VALUES (?, ?, ?, ?, ?, ?)''', depoimentos_exemplo)

        # Projetos de exemplo
        projetos_exemplo = [
            ('Residência Familiar - São Paulo/SP', 'Sistema de 8kWp instalado em residência de 250m². Redução de 92% na conta de energia.', 'Jardim Paulista, São Paulo/SP', 980.00, 8000, 'projeto1-antes.jpg', 'projeto1-depois.jpg', '2024-07-15'),
            ('Supermercado Regional - Campinas/SP', 'Sistema comercial de 50kWp em telhado metálico. Economia mensal de R$ 5.800.', 'Campinas/SP', 5800.00, 50000, 'projeto2-antes.jpg', 'projeto2-depois.jpg', '2024-09-20'),
            ('Fazenda Santa Clara - Interior/SP', 'Sistema off-grid de 15kWp para propriedade rural sem rede elétrica.', 'Interior de São Paulo', 1200.00, 15000, 'projeto3-antes.jpg', 'projeto3-depois.jpg', '2024-06-30'),
            ('Condomínio Residencial - Ribeirão Preto/SP', 'Sistema de 25kWp para áreas comuns. Redução de 88% nos custos condominiais.', 'Ribeirão Preto/SP', 2800.00, 25000, 'projeto4-antes.jpg', 'projeto4-depois.jpg', '2024-10-12')
        ]

        c.executemany('''INSERT INTO projetos 
            (titulo, descricao, local, economia_mensal, potencia_instalada, imagem_antes, imagem_depois, data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', projetos_exemplo)

        # Cupom de exemplo
        c.execute('''INSERT OR IGNORE INTO cupons (codigo, descricao, tipo, valor, valor_minimo, quantidade_total, ativo, data_inicio, data_fim)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                  ('BEMVINDO10', 'Desconto de 10% para novos clientes', 'percentual', 10, 500, 100, 1, 
                   datetime.now().strftime('%Y-%m-%d'), '2025-12-31'))

    conn.commit()
    conn.close()
    print("Banco de dados inicializado com sucesso!")

def migrate_db():
    """Atualiza estrutura do banco existente sem perder dados"""
    conn = sqlite3.connect('solarpro.db')
    c = conn.cursor()
    
    # Adicionar colunas novas se não existirem
    try:
        c.execute('ALTER TABLE produtos ADD COLUMN preco_promocional REAL')
    except: pass
    try:
        c.execute('ALTER TABLE produtos ADD COLUMN estoque_minimo INTEGER DEFAULT 5')
    except: pass
    try:
        c.execute('ALTER TABLE produtos ADD COLUMN ativo INTEGER DEFAULT 1')
    except: pass
    try:
        c.execute('ALTER TABLE produtos ADD COLUMN destaque INTEGER DEFAULT 0')
    except: pass
    try:
        c.execute('ALTER TABLE produtos ADD COLUMN vendas INTEGER DEFAULT 0')
    except: pass
    try:
        c.execute('ALTER TABLE produtos ADD COLUMN data_cadastro TEXT')
    except: pass
    try:
        c.execute('ALTER TABLE produtos ADD COLUMN imagens TEXT')
    except: pass
    try:
        c.execute('ALTER TABLE produtos ADD COLUMN custo REAL DEFAULT 0')
    except: pass
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
