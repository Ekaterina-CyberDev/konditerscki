// Файл: load-new-products.js
async function loadNewProducts() {
    try {
        const response = await fetch('new_products.json');
        if (!response.ok) {
            throw new Error(`Ошибка загрузки: ${response.status}`);
        }
        const data = await response.json();
        console.log('✅ Загружены новинки:', data.new_products.length);
        return data.new_products;
    } catch (error) {
        console.error('❌ Ошибка загрузки новинок:', error);
        return [];
    }
}

function displayNewProducts(products) {
    const newProductsContainer = document.getElementById('new');
    if (!newProductsContainer) return;
    
    const productsGrid = newProductsContainer.querySelector('.products-cards');
    if (!productsGrid) return;
    
    // Очищаем статический контент
    productsGrid.innerHTML = '';
    
    if (products.length === 0) {
        productsGrid.innerHTML = `
            <div style="grid-column: 1 / -1; text-align: center; padding: 50px;">
                <i class="fas fa-gift" style="font-size: 48px; color: #d4ac0d; margin-bottom: 20px;"></i>
                <h3 style="color: #7d6608;">Новинок пока нет</h3>
                <p style="color: #b7950b;">Скоро появятся новые товары!</p>
            </div>
        `;
        return;
    }
    
    // Сортируем по дате добавления (сначала новые)
    products.sort((a, b) => {
        return new Date(b.added_at) - new Date(a.added_at);
    });
    
    // Ограничиваем количество (например, 12 новинок)
    const displayProducts = products.slice(0, 12);
    
    displayProducts.forEach(product => {
        const imagePath = product.image_filename || product.photo_id || 'ку-ку.jpg';
        const addedDate = new Date(product.added_at);
        const daysAgo = Math.floor((new Date() - addedDate) / (1000 * 60 * 60 * 24));
        
        let daysText = '';
        if (daysAgo === 0) {
            daysText = '<span class="new-badge">НОВИНКА!</span>';
        } else if (daysAgo < 7) {
            daysText = `<span class="new-badge">${daysAgo} дн. назад</span>`;
        }
        
        const productCard = `
            <div class="product-card new-product">
                ${daysText}
                <div class="product-image">
                    <img src="${imagePath}" alt="${product.name}" 
                         onerror="this.src='ку-ку.jpg'">
                </div>
                <h3>${product.name}</h3>
                <div class="product-meta">
                    <span class="product-category">${product.category_name}</span>
                </div>
                <p class="price">${product.price} ₽</p>
                <button class="btn-buy" onclick="addToCart('${product.name}', ${product.price}, '${imagePath}')">
                    В корзину
                </button>
            </div>
        `;
        productsGrid.innerHTML += productCard;
    });
    
    // Добавляем стили для бейджа новинки
    const style = document.createElement('style');
    style.textContent = `
        .new-product {
            position: relative;
        }
        .new-badge {
            position: absolute;
            top: 15px;
            left: 15px;
            background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);
            color: white;
            padding: 5px 10px;
            border-radius: 15px;
            font-size: 11px;
            font-weight: bold;
            z-index: 10;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        }
        .product-meta {
            margin: 8px 0;
            font-size: 12px;
            color: #b7950b;
        }
        .product-category {
            background: #fef9e7;
            padding: 3px 8px;
            border-radius: 10px;
            border: 1px solid #f1c40f;
        }
    `;
    document.head.appendChild(style);
}

// Загружаем новинки при загрузке страницы
document.addEventListener('DOMContentLoaded', async () => {
    const newProducts = await loadNewProducts();
    displayNewProducts(newProducts);
    
    // Обновляем каждые 30 секунд
    setInterval(async () => {
        const newProducts = await loadNewProducts();
        displayNewProducts(newProducts);
    }, 30000);
});