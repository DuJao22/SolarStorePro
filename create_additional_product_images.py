
from PIL import Image, ImageDraw, ImageFont
import os
import math
import sqlite3

# Criar diretório se não existir
os.makedirs('static/images/products', exist_ok=True)

def hex_to_rgb(hex_color):
    """Converte cor hexadecimal para RGB"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def criar_imagem_vista(nome_base, vista_numero, cor, texto_principal, subtexto):
    """Cria uma imagem para uma vista específica do produto"""
    width, height = 800, 600
    cor_rgb = hex_to_rgb(cor)
    
    # Criar imagem com gradiente
    img = Image.new('RGB', (width, height), cor_rgb)
    draw = ImageDraw.Draw(img, 'RGBA')
    
    # Criar gradiente
    for i in range(height):
        factor = i / height
        r = int(cor_rgb[0] * (1 - factor * 0.3))
        g = int(cor_rgb[1] * (1 - factor * 0.3))
        b = int(cor_rgb[2] * (1 - factor * 0.3))
        draw.rectangle([(0, i), (width, i+1)], fill=(r, g, b))
    
    # Adicionar elementos decorativos
    overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    
    # Variações de decoração por vista
    if vista_numero == 1:
        # Vista frontal - círculos nos cantos
        overlay_draw.ellipse([width-200, -100, width+100, 200], fill=(255, 255, 255, 30))
        overlay_draw.ellipse([-100, height-200, 200, height+100], fill=(0, 0, 0, 20))
    elif vista_numero == 2:
        # Vista lateral - linhas diagonais
        for i in range(0, width + height, 100):
            overlay_draw.line([(i, 0), (i-height, height)], fill=(255, 255, 255, 15), width=3)
    elif vista_numero == 3:
        # Vista detalhes - grid
        for x in range(0, width, 80):
            overlay_draw.line([(x, 0), (x, height)], fill=(255, 255, 255, 10), width=1)
        for y in range(0, height, 80):
            overlay_draw.line([(0, y), (width, y)], fill=(255, 255, 255, 10), width=1)
    else:
        # Vista instalado - círculos aleatórios
        overlay_draw.ellipse([100, 100, 300, 300], fill=(255, 255, 255, 20))
        overlay_draw.ellipse([width-300, height-300, width-100, height-100], fill=(0, 0, 0, 15))
    
    img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
    draw = ImageDraw.Draw(img, 'RGBA')
    
    # Usar fonte
    try:
        font_titulo = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 70)
        font_subtexto = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 35)
        font_vista = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 25)
    except:
        font_titulo = ImageFont.load_default()
        font_subtexto = ImageFont.load_default()
        font_vista = ImageFont.load_default()
    
    # Texto da vista no canto superior direito
    vistas_texto = {
        1: "VISTA FRONTAL",
        2: "VISTA LATERAL", 
        3: "DETALHES",
        4: "INSTALADO"
    }
    vista_label = vistas_texto.get(vista_numero, f"VISTA {vista_numero}")
    bbox = draw.textbbox((0, 0), vista_label, font=font_vista)
    vista_width = bbox[2] - bbox[0]
    draw.rectangle([(width-vista_width-40, 20), (width-20, 60)], fill=(0, 0, 0, 120))
    draw.text((width-vista_width-30, 25), vista_label, fill='white', font=font_vista)
    
    # Adicionar texto principal
    linhas = texto_principal.split('\n')
    y_offset = (height - len(linhas) * 80) // 2
    
    for linha in linhas:
        bbox = draw.textbbox((0, 0), linha, font=font_titulo)
        text_width = bbox[2] - bbox[0]
        x = (width - text_width) // 2
        
        # Sombra
        draw.text((x+3, y_offset+3), linha, fill=(0, 0, 0, 128), font=font_titulo)
        # Texto principal
        draw.text((x, y_offset), linha, fill='white', font=font_titulo)
        y_offset += 80
    
    # Adicionar subtexto
    bbox = draw.textbbox((0, 0), subtexto, font=font_subtexto)
    sub_width = bbox[2] - bbox[0]
    draw.text(((width - sub_width) // 2, height - 70), subtexto, fill='white', font=font_subtexto)
    
    # Adicionar ícone solar (apenas nas vistas 1 e 4)
    if vista_numero in [1, 4]:
        sun_x, sun_y = 100, 100
        sun_radius = 40
        
        # Sol
        draw.ellipse([sun_x-sun_radius, sun_y-sun_radius, sun_x+sun_radius, sun_y+sun_radius], 
                     fill='#FFC857', outline='white', width=3)
        
        # Raios do sol
        for angle in range(0, 360, 45):
            x1 = sun_x + sun_radius * 1.5 * math.cos(math.radians(angle))
            y1 = sun_y + sun_radius * 1.5 * math.sin(math.radians(angle))
            x2 = sun_x + sun_radius * 2.5 * math.cos(math.radians(angle))
            y2 = sun_y + sun_radius * 2.5 * math.sin(math.radians(angle))
            draw.line([(x1, y1), (x2, y2)], fill='white', width=4)
    
    # Salvar imagem
    filepath = f'static/images/products/{nome_base}-vista{vista_numero}.jpg'
    img.convert('RGB').save(filepath, 'JPEG', quality=90)
    print(f'✅ Criada: {nome_base}-vista{vista_numero}.jpg')

# Conectar ao banco de dados para obter produtos
conn = sqlite3.connect('solarpro.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

produtos = cursor.execute('SELECT * FROM produtos WHERE ativo = 1').fetchall()

print('🎨 Criando imagens adicionais para produtos...\n')

# Mapeamento de cores por categoria
cores_categoria = {
    'Painéis Solares': ['#0B6A4A', '#0a5540', '#2D3436', '#16a085'],
    'Inversores': ['#3498db', '#9b59b6', '#e74c3c', '#2980b9'],
    'Kits Completos': ['#16a085', '#27ae60', '#f39c12', '#d35400']
}

for produto in produtos:
    # Determinar nome base do arquivo
    nome_base = produto['imagem'].replace('.jpg', '').replace('static/images/products/', '')
    
    # Determinar cores
    cores = cores_categoria.get(produto['categoria'], ['#0B6A4A', '#0a5540', '#2D3436', '#16a085'])
    
    # Preparar texto
    palavras = produto['nome'].split()
    if len(palavras) <= 3:
        texto = '\n'.join(palavras)
    else:
        meio = len(palavras) // 2
        texto = ' '.join(palavras[:meio]) + '\n' + ' '.join(palavras[meio:])
    
    subtexto = f"{produto['potencia_watts']}W | {produto['garantia']} anos"
    
    # Criar 4 vistas para cada produto
    for vista in range(1, 5):
        cor = cores[(vista - 1) % len(cores)]
        criar_imagem_vista(nome_base, vista, cor, texto, subtexto)
    
    print(f'📦 Produto completo: {produto["nome"]}\n')

# Atualizar banco de dados com as novas imagens
print('\n🔄 Atualizando banco de dados com imagens adicionais...\n')

for produto in produtos:
    import json
    
    nome_base = produto['imagem'].replace('.jpg', '').replace('static/images/products/', '')
    
    # Criar lista de imagens (principal + 3 vistas adicionais)
    imagens = [
        produto['imagem'],  # Imagem principal existente
        f'{nome_base}-vista2.jpg',
        f'{nome_base}-vista3.jpg',
        f'{nome_base}-vista4.jpg'
    ]
    
    imagens_json = json.dumps(imagens)
    
    cursor.execute('UPDATE produtos SET imagens = ? WHERE id = ?', (imagens_json, produto['id']))
    print(f'✅ Atualizado DB: {produto["nome"]}')

conn.commit()
conn.close()

print('\n🎉 Todas as imagens adicionais foram geradas e o banco foi atualizado!')
print(f'📁 Local: static/images/products/')
print(f'📊 Total de imagens criadas: {len(produtos) * 4}')
