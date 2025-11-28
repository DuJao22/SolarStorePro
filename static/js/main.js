// Otimização do vídeo hero
document.addEventListener('DOMContentLoaded', function() {
    const heroVideo = document.getElementById('heroVideo');

    if (heroVideo) {
        // Configurações para garantir reprodução
        heroVideo.muted = true;
        heroVideo.playsInline = true;
        heroVideo.loop = true;
        
        // Força reprodução
        const playVideo = () => {
            heroVideo.play().catch(err => {
                console.log('Aguardando interação do usuário para reproduzir vídeo');
            });
        };
        
        // Tenta reproduzir imediatamente
        playVideo();
        
        // Tenta novamente após interação do usuário
        document.body.addEventListener('click', playVideo, { once: true });
        document.body.addEventListener('touchstart', playVideo, { once: true });

        // Otimização para economizar dados em mobile
        if (window.innerWidth < 768) {
            heroVideo.style.filter = 'brightness(0.8)';
        }

        // Pausar vídeo quando não estiver visível (economia de recursos)
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    heroVideo.play().catch(() => {});
                } else {
                    heroVideo.pause();
                }
            });
        }, { threshold: 0.25 });

        observer.observe(heroVideo);
    }

    // Detectar toque para melhor UX mobile
    const isTouchDevice = () => {
        return (('ontouchstart' in window) ||
                (navigator.maxTouchPoints > 0) ||
                (navigator.msMaxTouchPoints > 0));
    };

    if (isTouchDevice()) {
        document.body.classList.add('touch-device');
        
        // Melhorar cliques em elementos pequenos
        document.querySelectorAll('.action-btn, .btn-icon').forEach(el => {
            el.style.minHeight = '44px';
            el.style.minWidth = '44px';
        });
    }

    // Prevenir zoom duplo-toque em iOS
    let lastTouchEnd = 0;
    document.addEventListener('touchend', function (event) {
        const now = (new Date()).getTime();
        if (now - lastTouchEnd <= 300) {
            event.preventDefault();
        }
        lastTouchEnd = now;
    }, false);

    // Otimizar scroll performance
    let ticking = false;
    window.addEventListener('scroll', () => {
        if (!ticking) {
            window.requestAnimationFrame(() => {
                handleScroll();
                ticking = false;
            });
            ticking = true;
        }
    });

    function handleScroll() {
        const header = document.getElementById('header');
        if (header) {
            if (window.scrollY > 100) {
                header.style.boxShadow = '0 4px 20px rgba(0,0,0,0.15)';
            } else {
                header.style.boxShadow = '0 2px 10px rgba(0,0,0,0.1)';
            }
        }
    }
});


AOS.init({
    duration: 800,
    once: true,
    offset: 100
});

function formatPrice(value) {
    const num = parseFloat(value);
    return num.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
}

// Carrinho de Compras
let carrinho = JSON.parse(localStorage.getItem('solarpro_cart')) || [];

function updateCartBadge() {
    const badge = document.getElementById('cartCount');
    if (badge) {
        const totalItems = carrinho.reduce((sum, item) => sum + item.quantidade, 0);
        badge.textContent = totalItems;
        badge.style.display = totalItems > 0 ? 'flex' : 'none';
    }
}

function addToCart(produtoId, nome, preco, imagem) {
    const existingItem = carrinho.find(item => item.id === produtoId);

    if (existingItem) {
        existingItem.quantidade += 1;
    } else {
        carrinho.push({
            id: produtoId,
            nome: nome,
            preco: preco,
            imagem: imagem,
            quantidade: 1
        });
    }

    localStorage.setItem('solarpro_cart', JSON.stringify(carrinho));
    updateCartBadge();

    // Sincronizar com o backend se o usuário estiver logado
    sincronizarCarrinho();

    alert('Produto adicionado ao carrinho!');
}

async function sincronizarCarrinho() {
    try {
        await fetch('/api/carrinho', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ produtos: carrinho })
        });
    } catch (error) {
        console.error('Erro ao sincronizar carrinho:', error);
    }
}


function updateCartDisplay() {
    const cartItems = document.getElementById('cartItems');
    const cartTotal = document.getElementById('cartTotal');

    if (!cartItems) return;

    if (carrinho.length === 0) {
        cartItems.innerHTML = '<p style="text-align: center; padding: 2rem;">Carrinho vazio</p>';
        cartTotal.textContent = 'R$ 0,00';
        return;
    }

    let html = '';
    let total = 0;

    carrinho.forEach((item, index) => {
        const subtotal = item.preco * item.quantidade;
        total += subtotal;

        html += `
            <div class="cart-item">
                <img src="/static/images/products/${item.imagem}"
                     class="cart-item-image"
                     alt="${item.nome}"
                     onerror="this.src='https://via.placeholder.com/80x80/0B6A4A/FFFFFF?text=Produto'">
                <div class="cart-item-info">
                    <div class="cart-item-name">${item.nome}</div>
                    <div class="cart-item-price">${formatPrice(item.preco)}</div>
                    <div class="cart-item-quantity">
                        <button onclick="decreaseQuantity(${index})">-</button>
                        <span>${item.quantidade}</span>
                        <button onclick="increaseQuantity(${index})">+</button>
                        <button onclick="removeItem(${index})" style="margin-left: auto; color: #ff6b6b;">🗑️</button>
                    </div>
                </div>
            </div>
        `;
    });

    cartItems.innerHTML = html;
    cartTotal.textContent = formatPrice(total);
}

function increaseQuantity(index) {
    carrinho[index].quantidade++;
    localStorage.setItem('solarpro_cart', JSON.stringify(carrinho));
    updateCartBadge();
    updateCartDisplay();
}

function decreaseQuantity(index) {
    if (carrinho[index].quantidade > 1) {
        carrinho[index].quantidade--;
    } else {
        removeItem(index);
        return;
    }
    localStorage.setItem('solarpro_cart', JSON.stringify(carrinho));
    updateCartBadge();
    updateCartDisplay();
}

function removeItem(index) {
    carrinho.splice(index, 1);
    localStorage.setItem('solarpro_cart', JSON.stringify(carrinho));
    updateCartBadge();
    updateCartDisplay();
}

document.getElementById('cartBtn')?.addEventListener('click', () => {
    document.getElementById('cartModal').classList.add('active');
    updateCartDisplay();
});

document.getElementById('cartClose')?.addEventListener('click', () => {
    document.getElementById('cartModal').classList.remove('active');
});

document.getElementById('cartModal')?.addEventListener('click', (e) => {
    if (e.target.id === 'cartModal') {
        document.getElementById('cartModal').classList.remove('active');
    }
});

document.getElementById('checkoutBtn')?.addEventListener('click', () => {
    if (carrinho.length === 0) {
        alert('Seu carrinho está vazio!');
        return;
    }
    window.location.href = '/checkout';
});

document.querySelectorAll('.add-to-cart').forEach(btn => {
    btn.addEventListener('click', (e) => {
        const id = btn.dataset.id;
        const nome = btn.dataset.nome;
        const preco = btn.dataset.preco;
        const imagem = btn.dataset.imagem;
        addToCart(id, nome, preco, imagem);
    });
});

document.getElementById('mobileMenuToggle')?.addEventListener('click', () => {
    document.getElementById('nav').classList.toggle('active');
});

updateCartBadge(); // Use updateCartBadge to reflect initial cart count

window.addEventListener('scroll', () => {
    const header = document.getElementById('header');
    if (window.scrollY > 100) {
        header.style.boxShadow = '0 4px 20px rgba(0,0,0,0.15)';
    } else {
        header.style.boxShadow = '0 2px 10px rgba(0,0,0,0.1)';
    }
});