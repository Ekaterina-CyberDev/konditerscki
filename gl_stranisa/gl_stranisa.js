// Header scroll effect
window.addEventListener('scroll', function() {
    const header = document.querySelector('header');
    if (window.scrollY > 50) {
        header.style.background = 'rgba(255, 245, 245, 0.98)';
        header.style.boxShadow = '0 2px 20px rgba(139, 69, 19, 0.15)';
    } else {
        header.style.background = 'rgba(255, 245, 245, 0.95)';
        header.style.boxShadow = '0 2px 10px rgba(139, 69, 19, 0.1)';
    }
});

// Modal functionality
const modal = document.getElementById("contacts-modal");
const favoritesModal = document.getElementById("favorites-modal");
const btn = document.getElementById("contacts-link");
const favoritesBtn = document.getElementById("favorites-link");
const spans = document.getElementsByClassName("close");

btn.onclick = function(event) {
    event.preventDefault();
    modal.style.display = "block";
    document.body.style.overflow = 'hidden';
}

favoritesBtn.onclick = function(event) {
    event.preventDefault();
    favoritesModal.style.display = "block";
    document.body.style.overflow = 'hidden';
    updateFavoritesModal();
}

// Закрытие модальных окон
Array.from(spans).forEach(span => {
    span.onclick = function() {
        modal.style.display = "none";
        favoritesModal.style.display = "none";
        document.body.style.overflow = '';
    }
});

window.onclick = function(event) {
    if (event.target == modal || event.target == favoritesModal) {
        modal.style.display = "none";
        favoritesModal.style.display = "none";
        document.body.style.overflow = '';
    }
}

// Tab navigation functionality
document.addEventListener('DOMContentLoaded', function() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    const productGrids = document.querySelectorAll('.products-grid');
    
    tabBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const tabId = this.getAttribute('data-tab');
            
            // Remove active class from all buttons and grids
            tabBtns.forEach(b => b.classList.remove('active'));
            productGrids.forEach(grid => grid.classList.remove('active'));
            
            // Add active class to clicked button and corresponding grid
            this.classList.add('active');
            document.getElementById(tabId).classList.add('active');
            
            // Smooth scroll to products section
            document.getElementById('categories').scrollIntoView({
                behavior: 'smooth'
            });
        });
    });
    
    // Инициализация избранного и корзины
    initFavorites();
    initCart();
    
    // Smooth scrolling for navigation links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
});

// Функционал избранного
let favorites = JSON.parse(localStorage.getItem('favorites')) || [];
let cart = JSON.parse(localStorage.getItem('cart')) || [];

function initFavorites() {
    updateFavoritesCount();
    addFavoriteButtons();
}

function initCart() {
    updateCartCount();
}

function addFavoriteButtons() {
    const productCards = document.querySelectorAll('.product-card');
    
    productCards.forEach(card => {
        const productName = card.querySelector('h3').textContent;
        const productPrice = card.querySelector('.price').textContent;
        const productImage = card.querySelector('img').src;
        
        // Проверяем, есть ли уже кнопка
        if (!card.querySelector('.favorite-btn')) {
            const favoriteBtn = document.createElement('button');
            favoriteBtn.className = 'favorite-btn';
            favoriteBtn.innerHTML = '<i class="far fa-heart"></i>';
            
            // Проверяем, есть ли товар в избранном
            if (isInFavorites(productName)) {
                favoriteBtn.classList.add('active');
                favoriteBtn.innerHTML = '<i class="fas fa-heart"></i>';
            }
            
            favoriteBtn.addEventListener('click', function(e) {
                e.stopPropagation();
                toggleFavorite(productName, productPrice, productImage, favoriteBtn);
            });
            
            card.appendChild(favoriteBtn);
        }
    });
}

function toggleFavorite(name, price, image, button) {
    const product = { name, price, image };
    const index = favorites.findIndex(item => item.name === name);
    
    if (index === -1) {
        // Добавляем в избранное
        favorites.push(product);
        button.classList.add('active');
        button.innerHTML = '<i class="fas fa-heart"></i>';
        showNotification('Товар добавлен в избранное!', 'success');
    } else {
        // Удаляем из избранного
        favorites.splice(index, 1);
        button.classList.remove('active');
        button.innerHTML = '<i class="far fa-heart"></i>';
        showNotification('Товар удален из избранного', 'info');
    }
    
    localStorage.setItem('favorites', JSON.stringify(favorites));
    updateFavoritesCount();
    
    // Обновляем модальное окно если оно открыто
    if (favoritesModal.style.display === 'block') {
        updateFavoritesModal();
    }
}

function isInFavorites(productName) {
    return favorites.some(item => item.name === productName);
}

function updateFavoritesCount() {
    const countElement = document.querySelector('.favorites-count');
    countElement.textContent = favorites.length;
}

function updateFavoritesModal() {
    const favoritesList = document.getElementById('favorites-list');
    
    if (favorites.length === 0) {
        favoritesList.innerHTML = `
            <div class="empty-favorites">
                <i class="fas fa-heart"></i>
                <p>В избранном пока пусто</p>
                <p>Добавляйте товары, нажимая на сердечко</p>
            </div>
        `;
    } else {
        favoritesList.innerHTML = favorites.map(item => `
            <div class="favorite-item">
                <img src="${item.image}" alt="${item.name}" class="favorite-item-image">
                <div class="favorite-item-info">
                    <div class="favorite-item-name">${item.name}</div>
                    <div class="favorite-item-price">${item.price}</div>
                </div>
                <button class="remove-favorite" onclick="removeFromFavorites('${item.name}')">
                    Удалить
                </button>
            </div>
        `).join('');
    }
}

function removeFromFavorites(productName) {
    favorites = favorites.filter(item => item.name !== productName);
    localStorage.setItem('favorites', JSON.stringify(favorites));
    updateFavoritesCount();
    updateFavoritesModal();
    
    // Обновляем кнопки на карточках товаров
    const favoriteBtns = document.querySelectorAll('.favorite-btn');
    favoriteBtns.forEach(btn => {
        const card = btn.closest('.product-card');
        const name = card.querySelector('h3').textContent;
        if (name === productName) {
            btn.classList.remove('active');
            btn.innerHTML = '<i class="far fa-heart"></i>';
        }
    });
}

// Функционал корзины
function addToCart(productName, productPrice, productImage) {
    const product = { 
        name: productName, 
        price: productPrice, 
        image: productImage,
        quantity: 1
    };
    
    cart.push(product);
    localStorage.setItem('cart', JSON.stringify(cart));
    updateCartCount();
    showNotification('Товар добавлен в корзину!', 'success');
}

function updateCartCount() {
    const countElement = document.querySelector('.cart-count');
    countElement.textContent = cart.length;
}

// Уведомления
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <i class="fas fa-${type === 'success' ? 'check' : 'info'}"></i>
            <span>${message}</span>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    // Анимация появления
    setTimeout(() => notification.classList.add('show'), 100);
    
    // Автоматическое скрытие
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Обработчики для кнопок "В корзину"
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('btn-buy')) {
        const card = e.target.closest('.product-card');
        const productName = card.querySelector('h3').textContent;
        const productPrice = card.querySelector('.price').textContent;
        const productImage = card.querySelector('img').src;
        
        addToCart(productName, productPrice, productImage);
    }
});

// Очистка избранного
document.getElementById('clear-favorites')?.addEventListener('click', function() {
    if (favorites.length > 0) {
        if (confirm('Вы уверены, что хотите очистить избранное?')) {
            favorites = [];
            localStorage.setItem('favorites', JSON.stringify(favorites));
            updateFavoritesCount();
            updateFavoritesModal();
            
            // Сбрасываем все кнопки избранного
            const favoriteBtns = document.querySelectorAll('.favorite-btn');
            favoriteBtns.forEach(btn => {
                btn.classList.remove('active');
                btn.innerHTML = '<i class="far fa-heart"></i>';
            });
            
            showNotification('Избранное очищено', 'info');
        }
    }
});

// Продолжить покупки
document.getElementById('continue-shopping')?.addEventListener('click', function() {
    favoritesModal.style.display = 'none';
    document.body.style.overflow = '';
});

// Animation for cards on scroll
function animateOnScroll() {
    const cards = document.querySelectorAll('.category-card, .product-card');
    cards.forEach(card => {
        const cardPosition = card.getBoundingClientRect().top;
        const screenPosition = window.innerHeight / 1.3;
        if (cardPosition < screenPosition) {
            card.style.opacity = 1;
            card.style.transform = 'translateY(0)';
        }
    });
}

// Initialize animations
document.addEventListener('DOMContentLoaded', function() {
    const cards = document.querySelectorAll('.category-card, .product-card');
    cards.forEach(card => {
        card.style.opacity = 0;
        card.style.transform = 'translateY(50px)';
        card.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
    });
    
    window.addEventListener('scroll', animateOnScroll);
    animateOnScroll();
});