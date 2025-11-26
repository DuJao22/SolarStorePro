
import sqlite3

def fix_product_images():
    conn = sqlite3.connect('solarpro.db')
    cursor = conn.cursor()
    
    # Mapear produtos para suas imagens
    product_images = {
        'Painel Solar 550W Monocristalino': '/static/images/products/painel-550w.jpg',
        'Painel Solar 450W Half-Cell': '/static/images/products/painel-450w.jpg',
        'Painel Solar 600W Vertex': '/static/images/products/painel-600w.jpg',
        'Painel Solar 400W Bifacial': '/static/images/products/painel-400w-bifacial.jpg',
        'Inversor Solar 3kW': '/static/images/products/inversor-3kw.jpg',
        'Inversor Solar 5kW Híbrido': '/static/images/products/inversor-5kw-hibrido.jpg',
        'Microinversor 600W': '/static/images/products/microinversor-600w.jpg',
        'Kit Solar Residencial 5kWp': '/static/images/products/kit-5kwp.jpg',
        'Kit Solar Residencial 10kWp': '/static/images/products/kit-10kwp.jpg',
        'Kit Off-Grid 3kWp': '/static/images/products/kit-offgrid-3kwp.jpg'
    }
    
    # Atualizar cada produto
    for nome, imagem in product_images.items():
        cursor.execute('UPDATE produtos SET imagem = ? WHERE nome = ?', (imagem, nome))
        print(f'✅ Atualizado: {nome} -> {imagem}')
    
    conn.commit()
    conn.close()
    print('\n🎉 Todas as imagens dos produtos foram atualizadas!')

if __name__ == '__main__':
    fix_product_images()
