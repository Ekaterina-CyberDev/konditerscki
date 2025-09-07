// Simple JavaScript for header scroll effect
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

// Animation for product cards on scroll
function animateOnScroll() {
    const cards = document.querySelectorAll('.product-card');
    cards.forEach(card => {
        const cardPosition = card.getBoundingClientRect().top;
        const screenPosition = window.innerHeight / 1.3;
        if (cardPosition < screenPosition) {
            card.style.opacity = 1;
            card.style.transform = 'translateY(0)';
        }
    });
}

// Initialize card opacity for animation
document.addEventListener('DOMContentLoaded', function() {
    const cards = document.querySelectorAll('.product-card');
    cards.forEach(card => {
        card.style.opacity = 0;
        card.style.transform = 'translateY(50px)';
        card.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
    });
    
    window.addEventListener('scroll', animateOnScroll);
    // Trigger once on load
    animateOnScroll();
});

// Horizontal scroll functionality for categories
document.addEventListener('DOMContentLoaded', function() {
    const gridContainer = document.querySelector('.categories-grid-container');
    const categoryRows = document.querySelectorAll('.category-row');
    
    if (gridContainer) {
        // Add scroll indicators
        const scrollIndicators = document.createElement('div');
        scrollIndicators.className = 'scroll-indicators';
        scrollIndicators.innerHTML = `
            <div class="scroll-indicator left">
                <i class="fas fa-chevron-left"></i>
            </div>
            <div class="scroll-indicator right">
                <i class="fas fa-chevron-right"></i>
            </div>
        `;
        gridContainer.parentNode.appendChild(scrollIndicators);
        
        const leftIndicator = document.querySelector('.scroll-indicator.left');
        const rightIndicator = document.querySelector('.scroll-indicator.right');
        
        // Update indicators on scroll
        gridContainer.addEventListener('scroll', function() {
            const scrollLeft = gridContainer.scrollLeft;
            const scrollWidth = gridContainer.scrollWidth;
            const clientWidth = gridContainer.clientWidth;
            
            leftIndicator.style.opacity = scrollLeft > 0 ? '1' : '0.3';
            rightIndicator.style.opacity = scrollLeft < scrollWidth - clientWidth - 10 ? '1' : '0.3';
        });
        
        // Scroll buttons functionality
        leftIndicator.addEventListener('click', function() {
            gridContainer.scrollBy({ left: -300, behavior: 'smooth' });
        });
        
        rightIndicator.addEventListener('click', function() {
            gridContainer.scrollBy({ left: 300, behavior: 'smooth' });
        });
        
        // Hide indicators on mobile
        function checkMobile() {
            if (window.innerWidth <= 768) {
                scrollIndicators.style.display = 'none';
            } else {
                scrollIndicators.style.display = 'flex';
            }
        }
        
        checkMobile();
        window.addEventListener('resize', checkMobile);
    }
});