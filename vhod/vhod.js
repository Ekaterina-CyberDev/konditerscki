// Обработчик клика на кнопку регистрации
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
        // form.submit();
    }
});