document.addEventListener('DOMContentLoaded', function() {
    // Элементы формы
    const inputs = {
        fullname: document.getElementById('fullname'),
        contact: document.getElementById('contact'),
        password: document.getElementById('password'),
        confirmPassword: document.getElementById('confirm-password'),
        terms: document.getElementById('terms')
    };
    const registerBtn = document.querySelector('.register-btn');

    // Функции валидации
    const validators = {
        fullname: value => /^[A-Za-zА-Яа-яЁё\s]{2,}$/.test(value),
        contact: value => {
            const isEmail = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
            const isPhone = /^(\+7|8)[\s-]?\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2}$/.test(value);
            return isEmail || isPhone;
        },
        password: value => value.length >= 8,
        confirmPassword: value => value === inputs.password.value
    };

    // Показать сообщение об ошибке
    function showError(input, message) {
        const errorElement = input.parentElement.querySelector('.error-message');
        errorElement.textContent = message;
        input.style.borderColor = '#ff6b6b';
        input.style.boxShadow = '0 0 0 3px rgba(255, 107, 107, 0.3)';
    }

    // Убрать сообщение об ошибке
    function clearError(input) {
        const errorElement = input.parentElement.querySelector('.error-message');
        errorElement.textContent = '';
        input.style.borderColor = '#ffe680';
        input.style.boxShadow = '';
    }

    // Проверка всех полей
    function validateAllFields() {
        let allValid = true;
        
        Object.keys(inputs).forEach(key => {
            if (key === 'terms') return;
            
            const input = inputs[key];
            const value = input.value.trim();
            
            clearError(input);
            
            if (value === '') {
                if (key === 'confirmPassword' && inputs.password.value === '') return;
                showError(input, 'Это поле обязательно для заполнения');
                allValid = false;
                return;
            }
            
            if (!validators[key](value)) {
                let errorMessage = '';
                
                switch(key) {
                    case 'fullname':
                        errorMessage = 'Имя должно содержать только буквы и быть не короче 2 символов';
                        break;
                    case 'contact':
                        errorMessage = 'Введите корректный email или номер телефона';
                        break;
                    case 'password':
                        errorMessage = 'Пароль должен содержать не менее 8 символов';
                        break;
                    case 'confirmPassword':
                        errorMessage = 'Пароли не совпадают';
                        break;
                }
                
                showError(input, errorMessage);
                allValid = false;
            }
        });
        
        return allValid;
    }

    // Обработчики событий
    function setupEventListeners() {
        // Проверка при изменении любого поля
        Object.values(inputs).forEach(input => {
            if (input.type === 'checkbox') return;
            
            input.addEventListener('input', function() {
                const value = this.value.trim();
                if (value === '') {
                    clearError(this);
                } else if (validators[this.id](value)) {
                    clearError(this);
                    this.style.borderColor = '#4ecdc4';
                    this.style.boxShadow = '0 0 0 3px rgba(78, 205, 196, 0.3)';
                }
            });
            
            input.addEventListener('blur', function() {
                const value = this.value.trim();
                if (value !== '' && !validators[this.id](value)) {
                    let errorMessage = '';
                    
                    switch(this.id) {
                        case 'fullname':
                            errorMessage = 'Имя должно содержать только буквы';
                            break;
                        case 'contact':
                            errorMessage = 'Введите корректный email или телефон';
                            break;
                        case 'password':
                            errorMessage = 'Не менее 8 символов';
                            break;
                        case 'confirmPassword':
                            errorMessage = 'Пароли не совпадают';
                            break;
                    }
                    
                    showError(this, errorMessage);
                }
            });
        });
        
        // Отправка формы
        registerBtn.addEventListener('click', function(e) {
            e.preventDefault();
            
            const allValid = validateAllFields();
            const termsChecked = inputs.terms.checked;
            
            if (!termsChecked) {
                alert('Необходимо согласиться с условиями');
                return;
            }
            
            if (allValid) {
                alert(`Регистрация успешна!\nДобро пожаловать, ${inputs.fullname.value.trim()}!\nВаша скидка 5% на первый заказ!`);
                // Здесь можно добавить отправку формы
            }
        });
    }

    // Инициализация
    setupEventListeners();
});