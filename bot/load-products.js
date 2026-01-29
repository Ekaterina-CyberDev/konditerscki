// Файл: load-products.js
async function loadProducts() {
    try {
        const response = await fetch('products.json');
        const data = await response.json();
        return data.products || [];
    } catch (error) {
        console.error('Ошибка загрузки товаров:', error);
        return [];
    }
}

function getCurrentCategory() {
    // Определяем категорию из URL страницы
    const pathname = window.location.pathname;
    const filename = pathname.split('/').pop();
    
    const categoryMap = {
        'chocolate.html': 'chocolate',
        'fillings.html': 'fillings', 
        'flour.html': 'flour',
        'colors.html': 'colors',
        'molds.html': 'molds',
        'tools.html': 'tools',
        'decor.html': 'decor',
        'special.html': 'special'
    };
    
    return categoryMap[filename] || null;
}

function displayProducts(products) {
    const currentCategory = getCurrentCategory();
    if (!currentCategory) return;
    
    const categoryProducts = products.filter(product => product.category === currentCategory);
    const productsContainer = document.querySelector('.products-cards');
    if (!productsContainer) return;
    
    productsContainer.innerHTML = '';
    
    categoryProducts.forEach(product => {
        // Используйте относительный путь к изображению
        const imagePath = product.image_filename || product.photo_id || 'ку-ку.jpg';
        
        const productCard = `
            <div class="product-card">
                <div class="product-image">
                    <img src="${imagePath}" alt="${product.name}" 
                         onerror="this.src='ку-ку.jpg'">
                </div>
                <h3>${product.name}</h3>
                <p class="price">${product.price} ₽</p>
                <button class="btn-buy" onclick="addToCart('${product.name}', ${product.price}, '${imagePath}')">
                    В корзину
                </button>
            </div>
        `;
        productsContainer.innerHTML += productCard;
    });
    
    // Если товаров нет, показываем сообщение
    if (categoryProducts.length === 0) {
        productsContainer.innerHTML = `
            <div class="empty-message" style="grid-column: 1 / -1; text-align: center; padding: 50px;">
                <i class="fas fa-box-open" style="font-size: 48px; color: #d4ac0d; margin-bottom: 20px;"></i>
                <h3 style="color: #7d6608;">Товаров пока нет</h3>
                <p style="color: #b7950b;">Добавьте товары через Telegram-бота</p>
            </div>
        `;
    }
}

// Функция для добавления в корзину (добавь в gl_stranisa.js)
function addToCart(productName, productPrice, productImage) {
    // Используй существующую функцию из gl_stranisa.js
    if (typeof addToCart === 'function') {
        addToCart(productName, productPrice, productImage);
    } else {
        // Если функция не найдена, показываем уведомление
        showNotification('Товар добавлен в корзину!');
    }
}

// Загружаем и отображаем товары при загрузке страницы
document.addEventListener('DOMContentLoaded', async () => {
    const products = await loadProducts();
    displayProducts(products);
    
    // Обновляем каждые 30 секунд (опционально)
    setInterval(async () => {
        const products = await loadProducts();
        displayProducts(products);
    }, 30000);
});
