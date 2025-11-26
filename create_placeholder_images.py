
from PIL import Image, ImageDraw, ImageFont
import os

# Criar diretórios se não existirem
os.makedirs('static/images/testimonials', exist_ok=True)
os.makedirs('static/images/projects', exist_ok=True)

# Cores para as imagens
colors = ['#0B6A4A', '#FFC857', '#2D3436', '#3498db']

# Criar imagens de depoimentos (300x300)
for i in range(1, 5):
    img = Image.new('RGB', (300, 300), color=colors[i-1])
    draw = ImageDraw.Draw(img)
    
    # Adicionar texto
    text = f"Cliente {i}"
    bbox = draw.textbbox((0, 0), text)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (300 - text_width) // 2
    y = (300 - text_height) // 2
    draw.text((x, y), text, fill='white')
    
    img.save(f'static/images/testimonials/cliente{i}.jpg', 'JPEG')
    print(f'Criada: cliente{i}.jpg')

# Criar imagens de projetos (600x400)
for i in range(1, 5):
    img = Image.new('RGB', (600, 400), color=colors[i-1])
    draw = ImageDraw.Draw(img)
    
    # Adicionar texto
    text = f"Projeto {i}"
    bbox = draw.textbbox((0, 0), text)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (600 - text_width) // 2
    y = (400 - text_height) // 2
    draw.text((x, y), text, fill='white')
    
    img.save(f'static/images/projects/projeto{i}-depois.jpg', 'JPEG')
    print(f'Criada: projeto{i}-depois.jpg')

print('\n✅ Todas as imagens placeholder foram criadas com sucesso!')
