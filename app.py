from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3
import json
from datetime import datetime, timedelta
from functools import wraps
import os
import uuid
from gemini_service import gemini_service
from database import init_db

# Inicializar banco de dados ao importar o app (necessário para Gunicorn/Render)
init_db()

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/images/products'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
app.secret_key = os.environ.get('SESSION_SECRET', 'dev-secret-key-change-in-production')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Faça login para continuar.'
login_manager.login_message_category = 'info'

class User(UserMixin):
    def __init__(self, id, nome, email, tipo, telefone=None, cpf=None, endereco=None, cidade=None, estado=None, cep=None):
        self.id = id
        self.nome = nome
        self.email = email
        self.tipo = tipo
        self.telefone = telefone
        self.cpf = cpf
        self.endereco = endereco
        self.cidade = cidade
        self.estado = estado
        self.cep = cep
    
    def is_admin(self):
        return self.tipo == 'admin'

@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM usuarios WHERE id = ? AND ativo = 1', (user_id,)).fetchone()
    conn.close()
    if user:
        return User(user['id'], user['nome'], user['email'], user['tipo'],
                   user['telefone'], user['cpf'], user['endereco'], user['cidade'], user['estado'], user['cep'])
    return None

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('Acesso restrito a administradores.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.template_filter('format_price')
def format_price_filter(value):
    try:
        value = float(value)
        return f"R$ {value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    except (ValueError, TypeError):
        return "R$ 0,00"

@app.template_filter('from_json')
def from_json_filter(value):
    try:
        if value:
            return json.loads(value)
        return {}
    except (json.JSONDecodeError, TypeError):
        return {}

@app.template_filter('format_date')
def format_date_filter(value):
    try:
        if value:
            dt = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
            return dt.strftime('%d/%m/%Y às %H:%M')
    except:
        pass
    return value

def get_db_connection():
    conn = sqlite3.connect('solarpro.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_config(chave, default=''):
    conn = get_db_connection()
    config = conn.execute('SELECT valor FROM configuracoes WHERE chave = ?', (chave,)).fetchone()
    conn.close()
    return config['valor'] if config else default

def set_config(chave, valor):
    conn = get_db_connection()
    conn.execute('''INSERT OR REPLACE INTO configuracoes (chave, valor, data_atualizacao)
                    VALUES (?, ?, ?)''', (chave, valor, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    conn.close()

def log_admin_action(usuario_id, acao, detalhes=''):
    conn = get_db_connection()
    conn.execute('''INSERT INTO logs_admin (usuario_id, acao, detalhes, ip, data)
                    VALUES (?, ?, ?, ?, ?)''',
                (usuario_id, acao, detalhes, request.remote_addr, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    conn.close()

@app.context_processor
def utility_processor():
    def product_image_url(image_name):
        return url_for('static', filename=f'images/products/{image_name}')
    
    def get_cart_count():
        if current_user.is_authenticated:
            conn = get_db_connection()
            carrinho = conn.execute('SELECT produtos_json FROM carrinhos WHERE usuario_id = ? AND status = "ativo"', 
                                   (current_user.id,)).fetchone()
            conn.close()
            if carrinho and carrinho['produtos_json']:
                produtos = json.loads(carrinho['produtos_json'])
                return sum(p.get('quantidade', 0) for p in produtos)
        return 0
    
    return dict(product_image_url=product_image_url, get_cart_count=get_cart_count)

# ============== ROTAS PÚBLICAS ==============

@app.route('/')
def index():
    conn = get_db_connection()
    produtos_destaque = conn.execute('SELECT * FROM produtos WHERE ativo = 1 AND destaque = 1 ORDER BY RANDOM() LIMIT 6').fetchall()
    if len(produtos_destaque) < 6:
        produtos_destaque = conn.execute('SELECT * FROM produtos WHERE ativo = 1 ORDER BY RANDOM() LIMIT 6').fetchall()
    depoimentos = conn.execute('SELECT * FROM depoimentos ORDER BY data DESC LIMIT 4').fetchall()
    projetos = conn.execute('SELECT * FROM projetos ORDER BY data DESC LIMIT 4').fetchall()
    conn.close()
    return render_template('index.html', 
                         produtos=produtos_destaque, 
                         depoimentos=depoimentos,
                         projetos=projetos)

@app.route('/produtos')
def produtos():
    conn = get_db_connection()
    categoria = request.args.get('categoria', '')
    ordem = request.args.get('ordem', 'nome')
    busca = request.args.get('busca', '')
    
    query = 'SELECT * FROM produtos WHERE ativo = 1'
    params = []
    
    if categoria:
        query += ' AND categoria = ?'
        params.append(categoria)
    
    if busca:
        query += ' AND (nome LIKE ? OR descricao LIKE ?)'
        params.extend([f'%{busca}%', f'%{busca}%'])
    
    if ordem == 'preco_asc':
        query += ' ORDER BY preco ASC'
    elif ordem == 'preco_desc':
        query += ' ORDER BY preco DESC'
    elif ordem == 'potencia_desc':
        query += ' ORDER BY potencia_watts DESC'
    elif ordem == 'vendas':
        query += ' ORDER BY vendas DESC'
    else:
        query += ' ORDER BY nome ASC'
    
    produtos_lista = conn.execute(query, params).fetchall()
    categorias = conn.execute('SELECT DISTINCT categoria FROM produtos WHERE ativo = 1').fetchall()
    conn.close()
    
    return render_template('produtos.html', 
                         produtos=produtos_lista, 
                         categorias=categorias,
                         categoria_atual=categoria,
                         ordem_atual=ordem,
                         busca=busca)

@app.route('/produto/<int:id>')
def produto(id):
    conn = get_db_connection()
    produto = conn.execute('SELECT * FROM produtos WHERE id = ? AND ativo = 1', (id,)).fetchone()
    
    if not produto:
        conn.close()
        return redirect(url_for('produtos'))
    
    produtos_relacionados = conn.execute(
        'SELECT * FROM produtos WHERE categoria = ? AND id != ? AND ativo = 1 LIMIT 4', 
        (produto['categoria'], id)
    ).fetchall()
    
    avaliacoes = conn.execute('''
        SELECT a.*, u.nome as usuario_nome FROM avaliacoes a 
        JOIN usuarios u ON a.usuario_id = u.id 
        WHERE a.produto_id = ? AND a.aprovado = 1 ORDER BY a.data DESC
    ''', (id,)).fetchall()
    
    na_lista_desejos = False
    if current_user.is_authenticated:
        desejo = conn.execute('SELECT id FROM lista_desejos WHERE usuario_id = ? AND produto_id = ?',
                             (current_user.id, id)).fetchone()
        na_lista_desejos = desejo is not None
    
    conn.close()
    
    return render_template('produto.html', 
                         produto=produto, 
                         relacionados=produtos_relacionados,
                         avaliacoes=avaliacoes,
                         na_lista_desejos=na_lista_desejos)

@app.route('/calculadora')
def calculadora():
    return render_template('calculadora.html')

@app.route('/calcular-roi', methods=['POST'])
def calcular_roi():
    try:
        data = request.get_json()
        consumo_mensal = float(data.get('consumo', 0))
        tarifa = float(data.get('tarifa', 0.85))
        
        if consumo_mensal <= 0:
            return jsonify({'erro': 'Consumo deve ser maior que zero'}), 400
    except (ValueError, TypeError):
        return jsonify({'erro': 'Dados inválidos'}), 400
    
    consumo_diario = consumo_mensal / 30
    potencia_necessaria = (consumo_diario / 5) * 1000
    
    paineis_550w = round(potencia_necessaria / 550)
    if paineis_550w < 4:
        paineis_550w = 4
    
    potencia_total = paineis_550w * 550
    geracao_mensal_estimada = (potencia_total / 1000) * 5 * 30
    economia_mensal = geracao_mensal_estimada * tarifa
    economia_anual = economia_mensal * 12
    
    custo_painel = 1299.00
    custo_inversor = 2890.00 if paineis_550w <= 6 else 8990.00
    custo_instalacao = paineis_550w * 500
    custo_total = (paineis_550w * custo_painel) + custo_inversor + custo_instalacao
    
    payback_anos = round(custo_total / economia_anual, 1)
    economia_25_anos = (economia_anual * 25) - custo_total
    
    resultado = {
        'paineis_necessarios': paineis_550w,
        'potencia_total': potencia_total,
        'geracao_mensal': round(geracao_mensal_estimada, 2),
        'economia_mensal': round(economia_mensal, 2),
        'economia_anual': round(economia_anual, 2),
        'custo_total': round(custo_total, 2),
        'payback_anos': payback_anos,
        'economia_25_anos': round(economia_25_anos, 2)
    }
    
    return jsonify(resultado)

@app.route('/sobre')
def sobre():
    return render_template('sobre.html')

@app.route('/solucao-empresas')
def landing_saas():
    return render_template('landing.html')

@app.route('/contato', methods=['GET', 'POST'])
def contato():
    if request.method == 'POST':
        conn = get_db_connection()
        conn.execute('''INSERT INTO contatos (nome, email, telefone, assunto, mensagem, data)
                       VALUES (?, ?, ?, ?, ?, ?)''',
                    (request.form['nome'],
                     request.form['email'],
                     request.form.get('telefone', ''),
                     request.form.get('assunto', 'Geral'),
                     request.form['mensagem'],
                     datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()
        conn.close()
        flash('Mensagem enviada com sucesso! Entraremos em contato em breve.', 'success')
        return redirect(url_for('contato'))
    
    return render_template('contato.html')

# ============== AUTENTICAÇÃO ==============

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.is_admin():
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('minha_conta'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        senha = request.form.get('senha', '')
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM usuarios WHERE email = ? AND ativo = 1', (email,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['senha_hash'], senha):
            user_obj = User(user['id'], user['nome'], user['email'], user['tipo'],
                           user['telefone'], user['cpf'], user['endereco'], user['cidade'], user['estado'], user['cep'])
            login_user(user_obj, remember=True)
            
            conn = get_db_connection()
            conn.execute('UPDATE usuarios SET ultimo_acesso = ? WHERE id = ?',
                        (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), user['id']))
            conn.commit()
            conn.close()
            
            flash(f'Bem-vindo(a), {user["nome"]}!', 'success')
            
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            
            if user['tipo'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('index'))
        else:
            flash('Email ou senha incorretos.', 'error')
    
    return render_template('auth/login.html')

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if current_user.is_authenticated:
        return redirect(url_for('minha_conta'))
    
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        email = request.form.get('email', '').strip().lower()
        telefone = request.form.get('telefone', '').strip()
        senha = request.form.get('senha', '')
        confirmar_senha = request.form.get('confirmar_senha', '')
        
        if not nome or not email or not senha:
            flash('Preencha todos os campos obrigatórios.', 'error')
            return render_template('auth/cadastro.html')
        
        if senha != confirmar_senha:
            flash('As senhas não conferem.', 'error')
            return render_template('auth/cadastro.html')
        
        if len(senha) < 6:
            flash('A senha deve ter pelo menos 6 caracteres.', 'error')
            return render_template('auth/cadastro.html')
        
        conn = get_db_connection()
        existing = conn.execute('SELECT id FROM usuarios WHERE email = ?', (email,)).fetchone()
        
        if existing:
            conn.close()
            flash('Este email já está cadastrado.', 'error')
            return render_template('auth/cadastro.html')
        
        senha_hash = generate_password_hash(senha)
        conn.execute('''INSERT INTO usuarios (nome, email, telefone, senha_hash, tipo, data_cadastro)
                       VALUES (?, ?, ?, ?, ?, ?)''',
                    (nome, email, telefone, senha_hash, 'cliente', datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()
        
        user = conn.execute('SELECT * FROM usuarios WHERE email = ?', (email,)).fetchone()
        conn.close()
        
        user_obj = User(user['id'], user['nome'], user['email'], user['tipo'])
        login_user(user_obj, remember=True)
        
        flash('Cadastro realizado com sucesso! Bem-vindo(a)!', 'success')
        return redirect(url_for('index'))
    
    return render_template('auth/cadastro.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você saiu da sua conta.', 'info')
    return redirect(url_for('index'))

# ============== ÁREA DO CLIENTE ==============

@app.route('/minha-conta')
@login_required
def minha_conta():
    conn = get_db_connection()
    pedidos = conn.execute('''SELECT * FROM pedidos WHERE usuario_id = ? ORDER BY data DESC LIMIT 5''',
                          (current_user.id,)).fetchall()
    lista_desejos = conn.execute('''
        SELECT p.* FROM lista_desejos ld
        JOIN produtos p ON ld.produto_id = p.id
        WHERE ld.usuario_id = ? AND p.ativo = 1
    ''', (current_user.id,)).fetchall()
    conn.close()
    return render_template('cliente/minha_conta.html', pedidos=pedidos, lista_desejos=lista_desejos)

@app.route('/meus-pedidos')
@login_required
def meus_pedidos():
    conn = get_db_connection()
    pedidos = conn.execute('SELECT * FROM pedidos WHERE usuario_id = ? ORDER BY data DESC',
                          (current_user.id,)).fetchall()
    conn.close()
    return render_template('cliente/meus_pedidos.html', pedidos=pedidos)

@app.route('/pedido/<int:id>')
@login_required
def ver_pedido(id):
    conn = get_db_connection()
    pedido = conn.execute('SELECT * FROM pedidos WHERE id = ? AND usuario_id = ?',
                         (id, current_user.id)).fetchone()
    conn.close()
    if not pedido:
        flash('Pedido não encontrado.', 'error')
        return redirect(url_for('meus_pedidos'))
    return render_template('cliente/ver_pedido.html', pedido=pedido)

@app.route('/atualizar-perfil', methods=['POST'])
@login_required
def atualizar_perfil():
    conn = get_db_connection()
    conn.execute('''UPDATE usuarios SET nome = ?, telefone = ?, cpf = ?, endereco = ?, cidade = ?, estado = ?, cep = ?
                    WHERE id = ?''',
                (request.form.get('nome'),
                 request.form.get('telefone'),
                 request.form.get('cpf'),
                 request.form.get('endereco'),
                 request.form.get('cidade'),
                 request.form.get('estado'),
                 request.form.get('cep'),
                 current_user.id))
    conn.commit()
    conn.close()
    flash('Perfil atualizado com sucesso!', 'success')
    return redirect(url_for('minha_conta'))

@app.route('/lista-desejos/adicionar/<int:produto_id>', methods=['POST'])
@login_required
def adicionar_lista_desejos(produto_id):
    conn = get_db_connection()
    try:
        conn.execute('''INSERT INTO lista_desejos (usuario_id, produto_id, data) VALUES (?, ?, ?)''',
                    (current_user.id, produto_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()
        flash('Produto adicionado à lista de desejos!', 'success')
    except:
        flash('Produto já está na lista de desejos.', 'info')
    conn.close()
    return redirect(request.referrer or url_for('produtos'))

@app.route('/lista-desejos/remover/<int:produto_id>', methods=['POST'])
@login_required
def remover_lista_desejos(produto_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM lista_desejos WHERE usuario_id = ? AND produto_id = ?',
                (current_user.id, produto_id))
    conn.commit()
    conn.close()
    flash('Produto removido da lista de desejos.', 'info')
    return redirect(request.referrer or url_for('minha_conta'))

# ============== CARRINHO ==============

@app.route('/carrinho')
def carrinho():
    return render_template('carrinho.html')

@app.route('/api/carrinho', methods=['GET'])
def api_get_carrinho():
    if current_user.is_authenticated:
        conn = get_db_connection()
        carrinho = conn.execute('SELECT produtos_json FROM carrinhos WHERE usuario_id = ? AND status = "ativo"',
                               (current_user.id,)).fetchone()
        conn.close()
        if carrinho and carrinho['produtos_json']:
            return jsonify(json.loads(carrinho['produtos_json']))
    return jsonify([])

@app.route('/api/carrinho', methods=['POST'])
def api_salvar_carrinho():
    data = request.get_json()
    produtos = data.get('produtos', [])
    
    if current_user.is_authenticated:
        conn = get_db_connection()
        total = sum(p.get('preco', 0) * p.get('quantidade', 0) for p in produtos)
        
        existing = conn.execute('SELECT id FROM carrinhos WHERE usuario_id = ? AND status = "ativo"',
                               (current_user.id,)).fetchone()
        
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if existing:
            conn.execute('''UPDATE carrinhos SET produtos_json = ?, total = ?, data_atualizacao = ?
                           WHERE id = ?''', (json.dumps(produtos), total, now, existing['id']))
        else:
            conn.execute('''INSERT INTO carrinhos (usuario_id, produtos_json, total, status, data_criacao, data_atualizacao)
                           VALUES (?, ?, ?, ?, ?, ?)''',
                        (current_user.id, json.dumps(produtos), total, 'ativo', now, now))
        
        conn.commit()
        conn.close()
    
    return jsonify({'success': True})

# ============== CHECKOUT ==============

@app.route('/checkout')
@login_required
def checkout():
    public_key = get_config('mercadopago_public_key', '')
    return render_template('checkout.html', mercadopago_public_key=public_key)

@app.route('/processar-pedido', methods=['POST'])
@login_required
def processar_pedido():
    try:
        data = request.get_json()
        
        if not data or not isinstance(data, dict):
            return jsonify({'sucesso': False, 'erro': 'Dados inválidos'}), 400
        
        produtos_cliente = data.get('produtos', [])
        if not produtos_cliente:
            return jsonify({'sucesso': False, 'erro': 'Carrinho vazio'}), 400
        
        required_fields = ['endereco', 'cidade', 'estado', 'cep']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'sucesso': False, 'erro': f'Campo obrigatório: {field}'}), 400
        
        conn = get_db_connection()
        
        total_servidor = 0
        produtos_validados = []
        
        for item in produtos_cliente:
            produto_id = int(item.get('id', 0))
            quantidade = int(item.get('quantidade', 0))
            
            produto_db = conn.execute('SELECT * FROM produtos WHERE id = ? AND ativo = 1', (produto_id,)).fetchone()
            
            if not produto_db:
                conn.close()
                return jsonify({'sucesso': False, 'erro': f'Produto não encontrado'}), 400
            
            if produto_db['estoque'] < quantidade:
                conn.close()
                return jsonify({'sucesso': False, 'erro': f'Estoque insuficiente para {produto_db["nome"]}'}), 400
            
            preco = produto_db['preco_promocional'] if produto_db['preco_promocional'] else produto_db['preco']
            subtotal = float(preco) * quantidade
            total_servidor += subtotal
            
            produtos_validados.append({
                'id': produto_id,
                'nome': produto_db['nome'],
                'quantidade': quantidade,
                'preco_unitario': float(preco),
                'subtotal': subtotal
            })
        
        # Aplicar cupom se existir
        desconto = 0
        cupom_codigo = data.get('cupom', '').strip().upper()
        if cupom_codigo:
            cupom = conn.execute('''SELECT * FROM cupons WHERE codigo = ? AND ativo = 1 
                                   AND (data_inicio IS NULL OR date(data_inicio) <= date('now'))
                                   AND (data_fim IS NULL OR date(data_fim) >= date('now'))
                                   AND (quantidade_total IS NULL OR quantidade_usada < quantidade_total)''',
                               (cupom_codigo,)).fetchone()
            if cupom and total_servidor >= cupom['valor_minimo']:
                if cupom['tipo'] == 'percentual':
                    desconto = total_servidor * (cupom['valor'] / 100)
                else:
                    desconto = cupom['valor']
                
                conn.execute('UPDATE cupons SET quantidade_usada = quantidade_usada + 1 WHERE id = ?', (cupom['id'],))
        
        total_final = total_servidor - desconto
        
        # Criar pedido
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        conn.execute('''INSERT INTO pedidos 
                       (usuario_id, nome_cliente, email, telefone, cpf, endereco, cidade, estado, cep, 
                        produtos_json, subtotal, desconto, total, cupom_usado, status_pedido, data)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (current_user.id, current_user.nome, current_user.email, 
                     data.get('telefone', current_user.telefone),
                     data.get('cpf', current_user.cpf),
                     data['endereco'], data['cidade'], data['estado'], data['cep'],
                     json.dumps(produtos_validados), total_servidor, desconto, total_final,
                     cupom_codigo if desconto > 0 else None, 'aguardando_pagamento', now))
        
        pedido_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
        
        # Atualizar estoque
        for item in produtos_validados:
            conn.execute('UPDATE produtos SET estoque = estoque - ?, vendas = vendas + ? WHERE id = ?',
                        (item['quantidade'], item['quantidade'], item['id']))
        
        # Limpar carrinho
        conn.execute('UPDATE carrinhos SET status = "convertido" WHERE usuario_id = ? AND status = "ativo"',
                    (current_user.id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'sucesso': True,
            'pedido_id': pedido_id,
            'total': total_final
        })
        
    except Exception as e:
        return jsonify({'sucesso': False, 'erro': str(e)}), 500

@app.route('/validar-cupom', methods=['POST'])
def validar_cupom():
    data = request.get_json()
    codigo = data.get('codigo', '').strip().upper()
    total = float(data.get('total', 0))
    
    conn = get_db_connection()
    cupom = conn.execute('''SELECT * FROM cupons WHERE codigo = ? AND ativo = 1 
                           AND (data_inicio IS NULL OR date(data_inicio) <= date('now'))
                           AND (data_fim IS NULL OR date(data_fim) >= date('now'))
                           AND (quantidade_total IS NULL OR quantidade_usada < quantidade_total)''',
                       (codigo,)).fetchone()
    conn.close()
    
    if not cupom:
        return jsonify({'valido': False, 'erro': 'Cupom inválido ou expirado'})
    
    if total < cupom['valor_minimo']:
        return jsonify({'valido': False, 'erro': f'Valor mínimo: R$ {cupom["valor_minimo"]:.2f}'})
    
    if cupom['tipo'] == 'percentual':
        desconto = total * (cupom['valor'] / 100)
        descricao = f'{cupom["valor"]}% de desconto'
    else:
        desconto = cupom['valor']
        descricao = f'R$ {cupom["valor"]:.2f} de desconto'
    
    return jsonify({
        'valido': True,
        'desconto': desconto,
        'descricao': descricao
    })

# ============== MERCADO PAGO ==============

@app.route('/criar-pagamento', methods=['POST'])
@login_required
def criar_pagamento():
    access_token = get_config('mercadopago_access_token')
    
    if not access_token:
        return jsonify({'erro': 'Pagamento não configurado. Entre em contato com a loja.'}), 400
    
    try:
        import mercadopago
        sdk = mercadopago.SDK(access_token)
        
        data = request.get_json()
        pedido_id = data.get('pedido_id')
        
        conn = get_db_connection()
        pedido = conn.execute('SELECT * FROM pedidos WHERE id = ? AND usuario_id = ?',
                             (pedido_id, current_user.id)).fetchone()
        conn.close()
        
        if not pedido:
            return jsonify({'erro': 'Pedido não encontrado'}), 404
        
        # Criar preferência de pagamento
        preference_data = {
            "items": [{
                "title": f"Pedido #{pedido_id} - SolarPro",
                "quantity": 1,
                "unit_price": float(pedido['total']),
                "currency_id": "BRL"
            }],
            "payer": {
                "email": pedido['email'],
                "name": pedido['nome_cliente']
            },
            "back_urls": {
                "success": url_for('pagamento_sucesso', pedido_id=pedido_id, _external=True),
                "failure": url_for('pagamento_falha', pedido_id=pedido_id, _external=True),
                "pending": url_for('pagamento_pendente', pedido_id=pedido_id, _external=True)
            },
            "auto_return": "approved",
            "external_reference": str(pedido_id)
        }
        
        preference_response = sdk.preference().create(preference_data)
        preference = preference_response["response"]
        
        sandbox = get_config('mercadopago_sandbox', '1') == '1'
        
        return jsonify({
            'id': preference['id'],
            'init_point': preference['sandbox_init_point'] if sandbox else preference['init_point']
        })
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@app.route('/pagamento/sucesso/<int:pedido_id>')
@login_required
def pagamento_sucesso(pedido_id):
    payment_id = request.args.get('payment_id')
    
    conn = get_db_connection()
    conn.execute('''UPDATE pedidos SET status_pagamento = ?, status_pedido = ?, mercadopago_id = ?, data_pagamento = ?
                    WHERE id = ? AND usuario_id = ?''',
                ('aprovado', 'pago', payment_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                 pedido_id, current_user.id))
    conn.commit()
    conn.close()
    
    flash('Pagamento realizado com sucesso!', 'success')
    return redirect(url_for('ver_pedido', id=pedido_id))

@app.route('/pagamento/falha/<int:pedido_id>')
@login_required
def pagamento_falha(pedido_id):
    flash('Houve um problema com o pagamento. Tente novamente.', 'error')
    return redirect(url_for('ver_pedido', id=pedido_id))

@app.route('/pagamento/pendente/<int:pedido_id>')
@login_required
def pagamento_pendente(pedido_id):
    conn = get_db_connection()
    conn.execute('UPDATE pedidos SET status_pagamento = ? WHERE id = ? AND usuario_id = ?',
                ('pendente', pedido_id, current_user.id))
    conn.commit()
    conn.close()
    
    flash('Pagamento pendente. Você receberá uma confirmação quando for aprovado.', 'info')
    return redirect(url_for('ver_pedido', id=pedido_id))

# ============== PAINEL ADMIN ==============

@app.route('/admin')
@admin_required
def admin_dashboard():
    conn = get_db_connection()
    
    # Estatísticas gerais
    total_pedidos = conn.execute('SELECT COUNT(*) FROM pedidos').fetchone()[0]
    pedidos_hoje = conn.execute('''SELECT COUNT(*) FROM pedidos WHERE date(data) = date('now')''').fetchone()[0]
    faturamento_mes = conn.execute('''SELECT COALESCE(SUM(total), 0) FROM pedidos 
                                     WHERE status_pagamento = 'aprovado' 
                                     AND strftime('%Y-%m', data) = strftime('%Y-%m', 'now')''').fetchone()[0]
    faturamento_total = conn.execute('''SELECT COALESCE(SUM(total), 0) FROM pedidos 
                                       WHERE status_pagamento = 'aprovado' ''').fetchone()[0]
    
    total_clientes = conn.execute('SELECT COUNT(*) FROM usuarios WHERE tipo = "cliente"').fetchone()[0]
    clientes_mes = conn.execute('''SELECT COUNT(*) FROM usuarios WHERE tipo = "cliente" 
                                  AND strftime('%Y-%m', data_cadastro) = strftime('%Y-%m', 'now')''').fetchone()[0]
    
    # Produtos com estoque baixo
    produtos_estoque_baixo = conn.execute('''SELECT * FROM produtos WHERE ativo = 1 AND estoque <= estoque_minimo
                                            ORDER BY estoque ASC LIMIT 10''').fetchall()
    
    # Pedidos recentes
    pedidos_recentes = conn.execute('''SELECT p.*, u.nome as cliente_nome FROM pedidos p
                                      LEFT JOIN usuarios u ON p.usuario_id = u.id
                                      ORDER BY p.data DESC LIMIT 10''').fetchall()
    
    # Carrinhos abandonados
    horas_abandono = int(get_config('carrinho_abandono_horas', '24'))
    data_limite = (datetime.now() - timedelta(hours=horas_abandono)).strftime('%Y-%m-%d %H:%M:%S')
    carrinhos_abandonados = conn.execute('''
        SELECT c.*, u.nome as cliente_nome, u.email, u.telefone FROM carrinhos c
        LEFT JOIN usuarios u ON c.usuario_id = u.id
        WHERE c.status = 'ativo' AND c.data_atualizacao < ?
        ORDER BY c.total DESC LIMIT 10
    ''', (data_limite,)).fetchall()
    
    # Contatos não respondidos
    contatos_pendentes = conn.execute('SELECT COUNT(*) FROM contatos WHERE respondido = 0').fetchone()[0]
    
    conn.close()
    
    return render_template('admin/dashboard.html',
                          total_pedidos=total_pedidos,
                          pedidos_hoje=pedidos_hoje,
                          faturamento_mes=faturamento_mes,
                          faturamento_total=faturamento_total,
                          total_clientes=total_clientes,
                          clientes_mes=clientes_mes,
                          produtos_estoque_baixo=produtos_estoque_baixo,
                          pedidos_recentes=pedidos_recentes,
                          carrinhos_abandonados=carrinhos_abandonados,
                          contatos_pendentes=contatos_pendentes)

@app.route('/admin/produtos')
@admin_required
def admin_produtos():
    conn = get_db_connection()
    produtos = conn.execute('SELECT * FROM produtos ORDER BY nome').fetchall()
    conn.close()
    return render_template('admin/produtos.html', produtos=produtos)

@app.route('/admin/upload-imagem', methods=['POST'])
@admin_required
def admin_upload_imagem():
    if 'file' not in request.files:
        return jsonify({'sucesso': False, 'erro': 'Nenhum arquivo enviado'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'sucesso': False, 'erro': 'Nenhum arquivo selecionado'})
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex[:8]}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(filepath)
        return jsonify({'sucesso': True, 'filename': unique_filename})
    
    return jsonify({'sucesso': False, 'erro': 'Tipo de arquivo não permitido'})

@app.route('/admin/produto/novo', methods=['GET', 'POST'])
@admin_required
def admin_produto_novo():
    if request.method == 'POST':
        imagens_list = []
        for i in range(1, 6):
            img = request.form.get(f'imagem_{i}', '').strip()
            if img:
                imagens_list.append(img)
        imagens_json = json.dumps(imagens_list) if imagens_list else None
        imagem_principal = imagens_list[0] if imagens_list else request.form.get('imagem')
        
        conn = get_db_connection()
        conn.execute('''INSERT INTO produtos (nome, descricao, preco, preco_promocional, potencia_watts, 
                       eficiencia, garantia, estoque, estoque_minimo, imagem, imagens, categoria, especificacoes, 
                       ativo, destaque, data_cadastro)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (request.form['nome'], request.form.get('descricao'),
                     float(request.form['preco']), 
                     float(request.form['preco_promocional']) if request.form.get('preco_promocional') else None,
                     int(request.form['potencia_watts']), float(request.form['eficiencia']),
                     int(request.form['garantia']), int(request.form['estoque']),
                     int(request.form.get('estoque_minimo', 5)), imagem_principal, imagens_json,
                     request.form['categoria'], request.form.get('especificacoes'),
                     1 if request.form.get('ativo') else 0, 1 if request.form.get('destaque') else 0,
                     datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()
        conn.close()
        log_admin_action(current_user.id, 'Produto criado', request.form['nome'])
        flash('Produto criado com sucesso!', 'success')
        return redirect(url_for('admin_produtos'))
    
    return render_template('admin/produto_form.html', produto=None)

@app.route('/admin/produto/<int:id>', methods=['GET', 'POST'])
@admin_required
def admin_produto_editar(id):
    conn = get_db_connection()
    
    if request.method == 'POST':
        imagens_list = []
        for i in range(1, 6):
            img = request.form.get(f'imagem_{i}', '').strip()
            if img:
                imagens_list.append(img)
        imagens_json = json.dumps(imagens_list) if imagens_list else None
        imagem_principal = imagens_list[0] if imagens_list else request.form.get('imagem')
        
        conn.execute('''UPDATE produtos SET nome = ?, descricao = ?, preco = ?, preco_promocional = ?,
                       potencia_watts = ?, eficiencia = ?, garantia = ?, estoque = ?, estoque_minimo = ?,
                       imagem = ?, imagens = ?, categoria = ?, especificacoes = ?, ativo = ?, destaque = ?
                       WHERE id = ?''',
                    (request.form['nome'], request.form.get('descricao'),
                     float(request.form['preco']),
                     float(request.form['preco_promocional']) if request.form.get('preco_promocional') else None,
                     int(request.form['potencia_watts']), float(request.form['eficiencia']),
                     int(request.form['garantia']), int(request.form['estoque']),
                     int(request.form.get('estoque_minimo', 5)), imagem_principal, imagens_json,
                     request.form['categoria'], request.form.get('especificacoes'),
                     1 if request.form.get('ativo') else 0, 1 if request.form.get('destaque') else 0, id))
        conn.commit()
        conn.close()
        log_admin_action(current_user.id, 'Produto atualizado', request.form['nome'])
        flash('Produto atualizado com sucesso!', 'success')
        return redirect(url_for('admin_produtos'))
    
    produto = conn.execute('SELECT * FROM produtos WHERE id = ?', (id,)).fetchone()
    conn.close()
    return render_template('admin/produto_form.html', produto=produto)

@app.route('/admin/pedidos')
@admin_required
def admin_pedidos():
    status = request.args.get('status', '')
    conn = get_db_connection()
    
    query = '''SELECT p.*, u.nome as cliente_nome FROM pedidos p
              LEFT JOIN usuarios u ON p.usuario_id = u.id'''
    params = []
    
    if status:
        query += ' WHERE p.status_pedido = ?'
        params.append(status)
    
    query += ' ORDER BY p.data DESC'
    
    pedidos = conn.execute(query, params).fetchall()
    conn.close()
    return render_template('admin/pedidos.html', pedidos=pedidos, status_atual=status)

@app.route('/admin/pedido/<int:id>')
@admin_required
def admin_pedido_detalhe(id):
    conn = get_db_connection()
    pedido = conn.execute('''SELECT p.*, u.nome as cliente_nome, u.email as cliente_email, u.telefone as cliente_telefone
                            FROM pedidos p LEFT JOIN usuarios u ON p.usuario_id = u.id
                            WHERE p.id = ?''', (id,)).fetchone()
    conn.close()
    if not pedido:
        flash('Pedido não encontrado.', 'error')
        return redirect(url_for('admin_pedidos'))
    return render_template('admin/pedido_detalhe.html', pedido=pedido)

@app.route('/admin/pedido/<int:id>/status', methods=['POST'])
@admin_required
def admin_atualizar_status_pedido(id):
    novo_status = request.form.get('status')
    conn = get_db_connection()
    conn.execute('UPDATE pedidos SET status_pedido = ? WHERE id = ?', (novo_status, id))
    conn.commit()
    conn.close()
    log_admin_action(current_user.id, 'Status do pedido atualizado', f'Pedido #{id}: {novo_status}')
    flash('Status do pedido atualizado!', 'success')
    return redirect(url_for('admin_pedido_detalhe', id=id))

@app.route('/admin/clientes')
@admin_required
def admin_clientes():
    conn = get_db_connection()
    clientes = conn.execute('''SELECT u.*, 
                              (SELECT COUNT(*) FROM pedidos WHERE usuario_id = u.id) as total_pedidos,
                              (SELECT COALESCE(SUM(total), 0) FROM pedidos WHERE usuario_id = u.id AND status_pagamento = 'aprovado') as total_gasto
                              FROM usuarios u WHERE tipo = 'cliente' ORDER BY data_cadastro DESC''').fetchall()
    conn.close()
    return render_template('admin/clientes.html', clientes=clientes)

@app.route('/admin/carrinhos-abandonados')
@admin_required
def admin_carrinhos_abandonados():
    conn = get_db_connection()
    horas_abandono = int(get_config('carrinho_abandono_horas', '24'))
    data_limite = (datetime.now() - timedelta(hours=horas_abandono)).strftime('%Y-%m-%d %H:%M:%S')
    
    carrinhos = conn.execute('''
        SELECT c.*, u.nome as cliente_nome, u.email, u.telefone FROM carrinhos c
        LEFT JOIN usuarios u ON c.usuario_id = u.id
        WHERE c.status = 'ativo' AND c.data_atualizacao < ?
        ORDER BY c.total DESC
    ''', (data_limite,)).fetchall()
    conn.close()
    return render_template('admin/carrinhos_abandonados.html', carrinhos=carrinhos)

@app.route('/admin/configuracoes', methods=['GET', 'POST'])
@admin_required
def admin_configuracoes():
    if request.method == 'POST':
        for key in request.form:
            if key.startswith('config_'):
                chave = key.replace('config_', '')
                set_config(chave, request.form[key])
        log_admin_action(current_user.id, 'Configurações atualizadas')
        flash('Configurações salvas com sucesso!', 'success')
        return redirect(url_for('admin_configuracoes'))
    
    conn = get_db_connection()
    configs = conn.execute('SELECT * FROM configuracoes ORDER BY chave').fetchall()
    conn.close()
    return render_template('admin/configuracoes.html', configs=configs)

@app.route('/admin/cupons')
@admin_required
def admin_cupons():
    conn = get_db_connection()
    cupons = conn.execute('SELECT * FROM cupons ORDER BY data_inicio DESC').fetchall()
    conn.close()
    return render_template('admin/cupons.html', cupons=cupons)

@app.route('/admin/cupom/novo', methods=['GET', 'POST'])
@admin_required
def admin_cupom_novo():
    if request.method == 'POST':
        conn = get_db_connection()
        conn.execute('''INSERT INTO cupons (codigo, descricao, tipo, valor, valor_minimo, quantidade_total, ativo, data_inicio, data_fim)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (request.form['codigo'].upper(), request.form.get('descricao'),
                     request.form['tipo'], float(request.form['valor']),
                     float(request.form.get('valor_minimo', 0)),
                     int(request.form['quantidade_total']) if request.form.get('quantidade_total') else None,
                     1 if request.form.get('ativo') else 0,
                     request.form.get('data_inicio'), request.form.get('data_fim')))
        conn.commit()
        conn.close()
        flash('Cupom criado com sucesso!', 'success')
        return redirect(url_for('admin_cupons'))
    return render_template('admin/cupom_form.html', cupom=None)

@app.route('/admin/contatos')
@admin_required
def admin_contatos():
    conn = get_db_connection()
    contatos = conn.execute('SELECT * FROM contatos ORDER BY data DESC').fetchall()
    conn.close()
    return render_template('admin/contatos.html', contatos=contatos)

@app.route('/admin/contato/<int:id>/responder', methods=['POST'])
@admin_required
def admin_marcar_respondido(id):
    conn = get_db_connection()
    conn.execute('UPDATE contatos SET respondido = 1 WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('Contato marcado como respondido.', 'success')
    return redirect(url_for('admin_contatos'))

# ============== ASSISTENTE IA ==============

@app.route('/admin/assistente')
@admin_required
def admin_assistente():
    return render_template('admin/assistente.html')

@app.route('/admin/assistente/chat', methods=['POST'])
@admin_required
def admin_assistente_chat():
    try:
        mensagem = request.json.get('mensagem', '')
        
        if not mensagem:
            return jsonify({'erro': 'Mensagem vazia'}), 400
        
        # Obter dados da loja para contexto
        conn = get_db_connection()
        
        # Estatísticas
        total_pedidos = conn.execute('SELECT COUNT(*) FROM pedidos').fetchone()[0]
        faturamento_mes = conn.execute('''SELECT COALESCE(SUM(total), 0) FROM pedidos 
                                         WHERE status_pagamento = 'aprovado' 
                                         AND strftime('%Y-%m', data) = strftime('%Y-%m', 'now')''').fetchone()[0]
        
        produtos_baixo_estoque = conn.execute('''SELECT nome, estoque FROM produtos 
                                                WHERE ativo = 1 AND estoque <= estoque_minimo''').fetchall()
        
        horas_abandono = int(get_config('carrinho_abandono_horas', '24'))
        data_limite = (datetime.now() - timedelta(hours=horas_abandono)).strftime('%Y-%m-%d %H:%M:%S')
        carrinhos_abandonados = conn.execute('''
            SELECT c.total, u.nome, u.email, u.telefone FROM carrinhos c
            LEFT JOIN usuarios u ON c.usuario_id = u.id
            WHERE c.status = 'ativo' AND c.data_atualizacao < ?
        ''', (data_limite,)).fetchall()
        
        pedidos_pendentes = conn.execute('''SELECT COUNT(*) FROM pedidos 
                                           WHERE status_pedido = 'aguardando_pagamento' ''').fetchone()[0]
        
        produtos_mais_vendidos = conn.execute('''
            SELECT nome, vendas, estoque FROM produtos 
            WHERE ativo = 1 ORDER BY vendas DESC LIMIT 5
        ''').fetchall()
        
        conn.close()
        
        contexto = f"""Você é um assistente de IA especializado em e-commerce de energia solar, ajudando o administrador da loja SolarPro.

📊 DADOS ATUAIS DA LOJA:
• Total de pedidos: {total_pedidos}
• Faturamento do mês: R$ {faturamento_mes:.2f}
• Pedidos aguardando pagamento: {pedidos_pendentes}
• Produtos com estoque baixo: {len(produtos_baixo_estoque)} {('(' + ', '.join([p['nome'] + f' ({p["estoque"]} un)' for p in produtos_baixo_estoque]) + ')') if produtos_baixo_estoque else '(nenhum)'}
• Carrinhos abandonados: {len(carrinhos_abandonados)}

🛒 CARRINHOS ABANDONADOS:
{chr(10).join([f'• {c["nome"] or "Cliente não identificado"}: R$ {c["total"]:.2f} | Email: {c["email"] or "N/A"} | Tel: {c["telefone"] or "N/A"}' for c in carrinhos_abandonados]) if carrinhos_abandonados else '✓ Nenhum carrinho abandonado no momento'}

🏆 PRODUTOS MAIS VENDIDOS:
{chr(10).join([f'• {p["nome"]}: {p["vendas"]} vendas (Estoque: {p["estoque"]} un)' for p in produtos_mais_vendidos]) if produtos_mais_vendidos else 'Nenhuma venda registrada'}

Sua missão é ajudar o administrador a:
✅ Aumentar vendas e conversões
✅ Recuperar carrinhos abandonados
✅ Otimizar gestão de estoque
✅ Sugerir estratégias de marketing
✅ Analisar dados e tendências

Seja específico, prático e forneça sugestões acionáveis."""
        
        resposta = gemini_service.get_response(mensagem, context=contexto)
        
        return jsonify({
            'resposta': resposta,
            'status': gemini_service.get_status()
        })
        
    except Exception as e:
        print(f"[Admin Assistente] Erro: {e}")
        return jsonify({'erro': f'Erro ao processar sua mensagem: {str(e)}'}), 500

# ============== API ==============

@app.route('/api/produtos')
def api_produtos():
    conn = get_db_connection()
    produtos = conn.execute('SELECT * FROM produtos WHERE ativo = 1').fetchall()
    conn.close()
    
    produtos_list = []
    for p in produtos:
        produtos_list.append({
            'id': p['id'],
            'nome': p['nome'],
            'preco': p['preco'],
            'preco_promocional': p['preco_promocional'],
            'potencia_watts': p['potencia_watts'],
            'imagem': p['imagem'],
            'estoque': p['estoque']
        })
    
    return jsonify(produtos_list)

@app.route('/api/buscar-produtos')
def api_buscar_produtos():
    termo = request.args.get('q', '')
    conn = get_db_connection()
    produtos = conn.execute('''SELECT id, nome, preco, imagem FROM produtos 
                              WHERE ativo = 1 AND (nome LIKE ? OR categoria LIKE ?)
                              LIMIT 10''', (f'%{termo}%', f'%{termo}%')).fetchall()
    conn.close()
    
    return jsonify([dict(p) for p in produtos])

# ============== GEMINI AI CHAT ==============

@app.route('/api/chat', methods=['POST'])
def api_chat():
    try:
        data = request.get_json()
        mensagem = data.get('mensagem', '').strip()
        
        if not mensagem:
            return jsonify({'erro': 'Mensagem vazia'}), 400
        
        conn = get_db_connection()
        produtos_destaque = conn.execute('''
            SELECT nome, preco, potencia_watts, categoria FROM produtos 
            WHERE ativo = 1 AND destaque = 1 LIMIT 5
        ''').fetchall()
        conn.close()
        
        contexto = "Produtos em destaque na loja:\n"
        for p in produtos_destaque:
            preco_formatado = f"R$ {p['preco']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            contexto += f"- {p['nome']} ({p['categoria']}): {preco_formatado}, {p['potencia_watts']}W\n"
        
        resposta = gemini_service.get_response(mensagem, context=contexto)
        
        return jsonify({
            'resposta': resposta,
            'status': gemini_service.get_status()
        })
        
    except Exception as e:
        print(f"[Chat API] Erro: {e}")
        return jsonify({'erro': 'Erro ao processar mensagem'}), 500

@app.route('/api/chat/recomendacao', methods=['POST'])
def api_chat_recomendacao():
    try:
        data = request.get_json()
        consumo = data.get('consumo_kwh', 0)
        localizacao = data.get('localizacao')
        orcamento = data.get('orcamento')
        
        resposta = gemini_service.get_product_recommendation(consumo, localizacao, orcamento)
        
        return jsonify({'resposta': resposta})
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@app.route('/api/chat/economia', methods=['POST'])
def api_chat_economia():
    try:
        data = request.get_json()
        consumo = data.get('consumo_kwh', 0)
        tarifa = data.get('tarifa', 0.75)
        
        resposta = gemini_service.get_savings_estimate(consumo, tarifa)
        
        return jsonify({'resposta': resposta})
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@app.route('/api/chat/status')
def api_chat_status():
    return jsonify(gemini_service.get_status())

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
