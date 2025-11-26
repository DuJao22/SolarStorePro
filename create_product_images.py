
from PIL import Image, ImageDraw, ImageFont
import os
import math

# Criar diretório se não existir
os.makedirs('static/images/products', exist_ok=True)

# Produtos e suas configurações
produtos_config = [
    {'nome': 'painel-550w', 'cor': '#0B6A4A', 'texto': 'PAINEL\nSOLAR\n550W', 'subtexto': 'Monocristalino'},
    {'nome': 'painel-450w', 'cor': '#0a5540', 'texto': 'PAINEL\nSOLAR\n450W', 'subtexto': 'Half-Cell'},
    {'nome': 'painel-600w', 'cor': '#2D3436', 'texto': 'PAINEL\nSOLAR\n600W', 'subtexto': 'Vertex'},
    {'nome': 'painel-400w-bifacial', 'cor': '#FFC857', 'texto': 'PAINEL\n400W\nBIFACIAL', 'subtexto': 'Alta Eficiência'},
    {'nome': 'inversor-3kw', 'cor': '#3498db', 'texto': 'INVERSOR\nSOLAR\n3kW', 'subtexto': 'On-Grid'},
    {'nome': 'inversor-5kw-hibrido', 'cor': '#9b59b6', 'texto': 'INVERSOR\n5kW\nHÍBRIDO', 'subtexto': 'Com Bateria'},
    {'nome': 'microinversor-600w', 'cor': '#e74c3c', 'texto': 'MICRO\nINVERSOR\n600W', 'subtexto': 'Modular'},
    {'nome': 'kit-5kwp', 'cor': '#16a085', 'texto': 'KIT SOLAR\nRESIDENCIAL\n5kWp', 'subtexto': 'Completo'},
    {'nome': 'kit-10kwp', 'cor': '#27ae60', 'texto': 'KIT SOLAR\nRESIDENCIAL\n10kWp', 'subtexto': 'Premium'},
    {'nome': 'kit-offgrid-3kwp', 'cor': '#f39c12', 'texto': 'KIT\nOFF-GRID\n3kWp', 'subtexto': 'Autônomo'}
]

def hex_to_rgb(hex_color):
    """Converte cor hexadecimal para RGB"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def criar_imagem_produto(config):
    nome = config['nome']
    cor = config['cor']
    texto = config['texto']
    subtexto = config['subtexto']
    
    # Dimensões da imagem
    width, height = 800, 600
    
    # Converter cor hex para RGB
    cor_rgb = hex_to_rgb(cor)

    # Criar imagem
    img = Image.new('RGB', (width, height), cor_rgb)
    draw = ImageDraw.Draw(img, 'RGBA')  # Usar modo RGBA para suportar transparência

    # Criar gradiente
    for i in range(height):
        factor = i / height
        r = int(cor_rgb[0] * (1 - factor * 0.3))
        g = int(cor_rgb[1] * (1 - factor * 0.3))
        b = int(cor_rgb[2] * (1 - factor * 0.3))
        draw.rectangle([(0, i), (width, i+1)], fill=(r, g, b))

    # Adicionar elementos decorativos (círculos) com transparência
    overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    
    # Círculo superior direito
    overlay_draw.ellipse([width-200, -100, width+100, 200], fill=(255, 255, 255, 30))
    # Círculo inferior esquerdo
    overlay_draw.ellipse([-100, height-200, 200, height+100], fill=(0, 0, 0, 20))
    
    # Mesclar overlay com a imagem base
    img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
    draw = ImageDraw.Draw(img, 'RGBA')

    # Usar fonte
    try:
        font_titulo = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 80)
        font_subtexto = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 40)
    except:
        font_titulo = ImageFont.load_default()
        font_subtexto = ImageFont.load_default()

    # Adicionar texto principal
    linhas = texto.split('\n')
    y_offset = (height - len(linhas) * 90) // 2

    for linha in linhas:
        bbox = draw.textbbox((0, 0), linha, font=font_titulo)
        text_width = bbox[2] - bbox[0]
        x = (width - text_width) // 2

        # Sombra (usando tupla RGBA)
        draw.text((x+3, y_offset+3), linha, fill=(0, 0, 0, 128), font=font_titulo)
        # Texto principal
        draw.text((x, y_offset), linha, fill='white', font=font_titulo)
        y_offset += 90

    # Adicionar subtexto
    bbox = draw.textbbox((0, 0), subtexto, font=font_subtexto)
    sub_width = bbox[2] - bbox[0]
    draw.text(((width - sub_width) // 2, height - 80), subtexto, fill='white', font=font_subtexto)

    # Adicionar ícone solar
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
    filepath = f'static/images/products/{nome}.jpg'
    if os.path.exists(filepath):
        print(f'⚠️  {nome}.jpg já existe, sobrescrevendo...')
    
    img.convert('RGB').save(filepath, 'JPEG', quality=90)
    print(f'✅ Criada: {nome}.jpg')

# Gerar todas as imagens
print('🎨 Criando imagens para produtos...\n')
for config in produtos_config:
    criar_imagem_produto(config)

print('\n🎉 Todas as imagens foram geradas com sucesso!')
print(f'📁 Local: static/images/products/')
