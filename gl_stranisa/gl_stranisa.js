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
const btn = document.getElementById("contacts-link");
const span = document.getElementsByClassName("close")[0];

btn.onclick = function(event) {
    event.preventDefault();
    modal.style.display = "block";
    document.body.style.overflow = 'hidden';
}

span.onclick = function() {
    modal.style.display = "none";
    document.body.style.overflow = '';
}

window.onclick = function(event) {
    if (event.target == modal) {
        modal.style.display = "none";
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
    
    // Add to cart functionality
    const buyButtons = document.querySelectorAll('.btn-buy');
    buyButtons.forEach(button => {
        button.addEventListener('click', function() {
            const productName = this.closest('.product-card').querySelector('h3').textContent;
            const productPrice = this.closest('.product-card').querySelector('.price').textContent;
            
            alert(`Товар "${productName}" добавлен в корзину!\nЦена: ${productPrice}`);
            
            // Here you can add actual cart functionality
            // For now, we'll just show an alert
        });
    });
    
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