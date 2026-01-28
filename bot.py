import json
import os
import re
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler
from telegram.ext import ContextTypes

# Конфигурация
TOKEN = "8594897952:AAGn77df9vPh0wJf0QaqoJFgkV0VcGmu_jw"
SITE_PATH = r"C:\Users\kolba\Desktop\konditerscki\gl_stranisa"
JSON_FILE = os.path.join(SITE_PATH, "products.json")  # Файл будет в папке сайта
NEW_PRODUCTS_FILE = os.path.join(SITE_PATH, "new_products.json")  # Файл для новинок
MAIN_PAGE_FILE = os.path.join(SITE_PATH, "gl_stranisa.html")  # Главная страница
NEW_PRODUCT_DAYS = 30  # Товар считается новинкой 30 дней
ITEMS_PER_PAGE = 10  # Товаров на страницу при просмотре списка


# Вспомогательная функция для создания безопасного имени файла
def create_safe_filename(product_name):
    """
    Создает безопасное имя файла из названия товара.
    Пример: 'Товар №1!' -> 'tovar_1.jpg'
    """
    # Транслитерация русских букв в латинские
    translit_dict = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd',
        'е': 'e', 'ё': 'yo', 'ж': 'zh', 'з': 'z', 'и': 'i',
        'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n',
        'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't',
        'у': 'u', 'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch',
        'ш': 'sh', 'щ': 'sch', 'ъ': '', 'ы': 'y', 'ь': '',
        'э': 'e', 'ю': 'yu', 'я': 'ya',
        'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D',
        'Е': 'E', 'Ё': 'Yo', 'Ж': 'Zh', 'З': 'Z', 'И': 'I',
        'Й': 'Y', 'К': 'K', 'Л': 'L', 'М': 'M', 'Н': 'N',
        'О': 'O', 'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T',
        'У': 'U', 'Ф': 'F', 'Х': 'H', 'Ц': 'Ts', 'Ч': 'Ch',
        'Ш': 'Sh', 'Щ': 'Sch', 'Ъ': '', 'Ы': 'Y', 'Ь': '',
        'Э': 'E', 'Ю': 'Yu', 'Я': 'Ya'
    }

    # Транслитерация
    result = ''
    for char in product_name:
        if char in translit_dict:
            result += translit_dict[char]
        else:
            result += char

    # Убираем все кроме букв, цифр, подчеркиваний и точек
    result = re.sub(r'[^\w\s\.-]', '', result)
    # Заменяем пробелы и дефисы на подчеркивания
    result = re.sub(r'[-\s]+', '_', result)
    # Убираем множественные подчеркивания
    result = re.sub(r'_+', '_', result)
    # Убираем подчеркивания в начале и конце
    result = result.strip('_')
    # Делаем строчными
    result = result.lower()

    # Если после обработки пустая строка, используем timestamp
    if not result:
        result = f"product_{int(datetime.now().timestamp())}"

    # Добавляем расширение .jpg
    return f"{result}.jpg"


# Категории с вашего сайта (файлы и названия)
CATEGORIES = {
    "chocolate": {"name": "Шоколад и какао", "file": "chocolate.html"},
    "fillings": {"name": "Начинки и джемы", "file": "fillings.html"},
    "flour": {"name": "Мука и смеси", "file": "flour.html"},
    "colors": {"name": "Красители и ароматизаторы", "file": "colors.html"},
    "molds": {"name": "Формы и упаковка", "file": "molds.html"},
    "tools": {"name": "Инструменты", "file": "tools.html"},
    "decor": {"name": "Декор и посыпки", "file": "decor.html"},
    "special": {"name": "Специальные ингредиенты", "file": "special.html"}
}

# Состояния
MAIN_MENU, SELECT_CATEGORY, GET_NAME, GET_PRICE, GET_PHOTO = range(5)
SELECT_EDIT, EDIT_FIELD, EDIT_NAME, EDIT_PRICE, SELECT_DELETE, CONFIRM_DELETE = range(5, 11)
MANAGE_NEW, VIEW_ALL_PRODUCTS = range(11, 13)


# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========

def get_main_menu():
    keyboard = [
        [InlineKeyboardButton("➕ Добавить товар", callback_data="add")],
        [InlineKeyboardButton("📋 Список товаров", callback_data="list")],
        [InlineKeyboardButton("👁️ Просмотреть все товары", callback_data="view_all")],
        [InlineKeyboardButton("✏️ Редактировать", callback_data="edit")],
        [InlineKeyboardButton("🗑️ Удалить", callback_data="delete")],
        [InlineKeyboardButton("🆕 Управление новинками", callback_data="manage_new")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_categories_menu(prefix=""):
    keyboard = []
    for key, cat_info in CATEGORIES.items():
        keyboard.append([InlineKeyboardButton(cat_info["name"], callback_data=f"{prefix}{key}")])
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back")])
    return InlineKeyboardMarkup(keyboard)


def get_products_menu(page=0, prefix=""):
    data = load_products()
    products = data["products"]

    if not products:
        return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="back")]])

    # Сортируем товары по ID (новые сначала)
    products_sorted = sorted(products, key=lambda x: x['id'], reverse=True)

    # Для выбора товара (редактирование/удаление) - пагинация
    total_pages = (len(products_sorted) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    start_idx = page * ITEMS_PER_PAGE
    end_idx = start_idx + ITEMS_PER_PAGE

    keyboard = []

    # Добавляем товары текущей страницы
    for product in products_sorted[start_idx:end_idx]:
        # Обрезаем длинное название для кнопки
        name = product['name']
        if len(name) > 30:
            name = name[:27] + "..."

        btn_text = f"{product['id']}: {name} - {product['price']}₽"
        keyboard.append([
            InlineKeyboardButton(btn_text, callback_data=f"{prefix}{product['id']}")
        ])

    # Добавляем навигацию по страницам если нужно
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"{prefix}page_{page - 1}"))

    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton("Вперед ➡️", callback_data=f"{prefix}page_{page + 1}"))

    if nav_buttons:
        keyboard.append(nav_buttons)

    keyboard.append([InlineKeyboardButton("🔙 На главную", callback_data="back")])

    return InlineKeyboardMarkup(keyboard)


def get_all_products_menu(page=0, prefix=""):
    """Получает меню для просмотра всех товаров с группировкой по категориям"""
    data = load_products()
    products = data["products"]

    if not products:
        return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="back")]])

    # Группируем товары по категориям
    products_by_category = {}
    for product in products:
        cat_key = product.get('category')
        if cat_key in CATEGORIES:
            cat_name = CATEGORIES[cat_key]["name"]
        else:
            cat_name = 'Без категории'

        if cat_name not in products_by_category:
            products_by_category[cat_name] = []
        products_by_category[cat_name].append(product)

    # Сортируем категории по алфавиту
    sorted_categories = sorted(products_by_category.keys())

    # Пагинация по категориям
    total_categories = len(sorted_categories)
    total_pages = (total_categories + 5 - 1) // 5  # 5 категорий на страницу
    start_idx = page * 5
    end_idx = min(start_idx + 5, total_categories)

    keyboard = []

    # Добавляем категории текущей страницы
    for i in range(start_idx, end_idx):
        cat_name = sorted_categories[i]
        cat_products = products_by_category[cat_name]
        product_count = len(cat_products)

        btn_text = f"📁 {cat_name} ({product_count})"
        keyboard.append([
            InlineKeyboardButton(btn_text, callback_data=f"{prefix}cat_{i}")
        ])

    # Добавляем навигацию по страницам
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"{prefix}all_page_{page - 1}"))

    page_info = f"📄 {page + 1}/{total_pages}" if total_pages > 1 else ""

    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton("Вперед ➡️", callback_data=f"{prefix}all_page_{page + 1}"))

    if nav_buttons:
        keyboard.append(nav_buttons)

    keyboard.append([InlineKeyboardButton("🔙 На главную", callback_data="back")])

    return InlineKeyboardMarkup(keyboard)


def get_category_products_menu(category_index, page=0, prefix=""):
    """Получает меню товаров конкретной категории"""
    data = load_products()
    products = data["products"]

    if not products:
        return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="back")]])

    # Группируем товары по категориям
    products_by_category = {}
    for product in products:
        cat_key = product.get('category')
        if cat_key in CATEGORIES:
            cat_name = CATEGORIES[cat_key]["name"]
        else:
            cat_name = 'Без категории'

        if cat_name not in products_by_category:
            products_by_category[cat_name] = []
        products_by_category[cat_name].append(product)

    # Сортируем категории по алфавиту
    sorted_categories = sorted(products_by_category.keys())

    if category_index >= len(sorted_categories):
        return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="back")]])

    cat_name = sorted_categories[category_index]
    cat_products = sorted(products_by_category[cat_name], key=lambda x: x['id'], reverse=True)

    total_pages = (len(cat_products) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    start_idx = page * ITEMS_PER_PAGE
    end_idx = start_idx + ITEMS_PER_PAGE

    keyboard = []

    # Добавляем заголовок категории
    keyboard.append([InlineKeyboardButton(f"📁 {cat_name}", callback_data="noop")])

    # Добавляем товары текущей страницы
    for product in cat_products[start_idx:end_idx]:
        # Обрезаем длинное название для кнопки
        name = product['name']
        if len(name) > 25:
            name = name[:22] + "..."

        btn_text = f"• {product['id']}: {name} - {product['price']}₽"
        keyboard.append([
            InlineKeyboardButton(btn_text, callback_data=f"{prefix}{product['id']}")
        ])

    # Добавляем навигацию по страницам
    nav_buttons = []
    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton("⬅️ Назад", callback_data=f"{prefix}cat_{category_index}_page_{page - 1}"))

    if page < total_pages - 1:
        nav_buttons.append(
            InlineKeyboardButton("Вперед ➡️", callback_data=f"{prefix}cat_{category_index}_page_{page + 1}"))

    if nav_buttons:
        keyboard.append(nav_buttons)

    keyboard.append([InlineKeyboardButton("🔙 К категориям", callback_data=f"{prefix}back_to_cats")])
    keyboard.append([InlineKeyboardButton("🔙 На главную", callback_data="back")])

    return InlineKeyboardMarkup(keyboard)


# ========== ФУНКЦИИ ДЛЯ РАБОТЫ С ТОВАРАМИ ==========

def load_products():
    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"products": []}


def save_products(data):
    with open(JSON_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def generate_id(data):
    if not data["products"]:
        return 1
    return max(item["id"] for item in data["products"]) + 1


def get_product_by_id(product_id):
    data = load_products()
    for product in data["products"]:
        if product["id"] == product_id:
            return product
    return None


# ========== ФУНКЦИИ ДЛЯ РАБОТЫ С НОВИНКАМИ ==========

def load_new_products():
    """Загружает список новинок"""
    if os.path.exists(NEW_PRODUCTS_FILE):
        with open(NEW_PRODUCTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"new_products": []}


def save_new_products(data):
    """Сохраняет список новинок"""
    with open(NEW_PRODUCTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def add_to_new_products(product):
    """Добавляет товар в список новинок"""
    data = load_new_products()

    # Удаляем старые новинки
    data = clean_old_new_products(data)

    # Проверяем, не добавлен ли уже этот товар
    if not any(p.get('id') == product['id'] for p in data["new_products"]):
        product_data = {
            "id": product['id'],
            "name": product['name'],
            "price": product['price'],
            "image_filename": product['image_filename'],
            "category": product['category'],
            "category_name": product['category_name'],
            "added_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "expires_at": (datetime.now() + timedelta(days=NEW_PRODUCT_DAYS)).strftime("%Y-%m-%d %H:%M:%S")
        }
        data["new_products"].append(product_data)
        save_new_products(data)
        print(f"✅ Товар добавлен в новинки: {product['name']}")

        # Обновляем раздел новинок на главной странице
        update_new_products_on_main_page()

        return True
    return False


def clean_old_new_products(data=None):
    """Удаляет старые новинки (старше NEW_PRODUCT_DAYS дней)"""
    if data is None:
        data = load_new_products()

    if not data["new_products"]:
        return data

    current_time = datetime.now()
    initial_count = len(data["new_products"])

    # Фильтруем новинки, оставляя только те, что еще не истекли
    data["new_products"] = [
        product for product in data["new_products"]
        if datetime.strptime(product['expires_at'], "%Y-%m-%d %H:%M:%S") > current_time
    ]

    removed_count = initial_count - len(data["new_products"])
    if removed_count > 0:
        print(f"🗑️ Удалено {removed_count} старых новинок")
        save_new_products(data)
        # Обновляем раздел новинок на главной странице
        update_new_products_on_main_page()

    return data


def remove_from_new_products(product_id):
    """Удаляет товар из списка новинок"""
    data = load_new_products()
    initial_count = len(data["new_products"])
    data["new_products"] = [p for p in data["new_products"] if p['id'] != product_id]

    if len(data["new_products"]) < initial_count:
        save_new_products(data)
        print(f"✅ Товар ID {product_id} удален из новинок")
        # Обновляем раздел новинок на главной странице
        update_new_products_on_main_page()
        return True

    return False


def update_new_product(product_id, new_data):
    """Обновляет информацию о товаре в новинках"""
    data = load_new_products()
    updated = False

    for product in data["new_products"]:
        if product['id'] == product_id:
            # Обновляем только те поля, которые есть в new_data
            for key, value in new_data.items():
                if key in product:
                    product[key] = value
            updated = True
            break

    if updated:
        save_new_products(data)
        print(f"✅ Товар ID {product_id} обновлен в новинках")
        # Обновляем раздел новинок на главной странице
        update_new_products_on_main_page()

    return updated


def update_new_products_on_main_page():
    """Обновляет раздел новинок на главной странице"""
    data = load_new_products()

    # Удаляем старые новинки перед обновлением
    data = clean_old_new_products(data)

    if os.path.exists(MAIN_PAGE_FILE):
        with open(MAIN_PAGE_FILE, 'r', encoding='utf-8') as f:
            content = f.read()

        # Находим начало и конец секции с новинками
        start_marker = '<!-- НОВИНКИ_START -->'
        end_marker = '<!-- НОВИНКИ_END -->'

        start_idx = content.find(start_marker)
        end_idx = content.find(end_marker)

        if start_idx == -1 or end_idx == -1:
            print("❌ Не найдены маркеры новинок на главной странице")
            return

        # Создаем новый HTML для новинок с исправленным макетом
        products_html = '\n'

        if not data["new_products"]:
            products_html += '''
                    <div class="product-card">
                        <div class="product-image">
                            <img src="ку-ку.jpg" alt="Нет новинок">
                        </div>
                        <div class="product-card-content">
                            <h3>Нет новинок</h3>
                            <p class="price">0 ₽</p>
                            <button class="btn-buy">В корзину</button>
                        </div>
                    </div>
'''
        else:
            # Берем только последние 6 новинок
            for product in data["new_products"][:6]:
                product_card = f'''
                    <div class="product-card">
                        <div class="product-image">
                            <img src="{product.get('image_filename', 'ку-ку.jpg')}" alt="{product['name']}" onerror="this.src='ку-ку.jpg'">
                        </div>
                        <div class="product-card-content">
                            <h3>{product['name']}</h3>
                            <p class="product-desc">Новинка! Категория: {product.get('category_name', 'Без категории')}</p>
                            <p class="price">{product['price']} ₽</p>
                            <button class="btn-buy">В корзину</button>
                        </div>
                    </div>
'''
                products_html += product_card + '\n'

        # Заменяем старый контент на новый
        new_content = content[:start_idx + len(start_marker)] + products_html + content[end_idx:]

        # Сохраняем обновленный файл
        with open(MAIN_PAGE_FILE, 'w', encoding='utf-8') as f:
            f.write(new_content)

        print(f"✅ Обновлен раздел новинок на главной странице (товаров: {min(6, len(data['new_products']))})")
    else:
        print(f"❌ Главная страница не найдена: {MAIN_PAGE_FILE}")


# ========== ФУНКЦИЯ ДЛЯ ОБНОВЛЕНИЯ HTML ФАЙЛОВ ==========

def update_html_files():
    data = load_products()

    for category_key, cat_info in CATEGORIES.items():
        filename = os.path.join(SITE_PATH, cat_info["file"])
        category_products = [p for p in data["products"] if p.get("category") == category_key]

        # Читаем существующий файл
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()

            # Находим начало и конец секции с товарами
            start_marker = '<!-- PRODUCTS_START -->'
            end_marker = '<!-- PRODUCTS_END -->'

            start_idx = content.find(start_marker)
            end_idx = content.find(end_marker)

            if start_idx != -1 and end_idx != -1:
                # Создаем новый HTML для товаров с исправленным макетом
                products_html = '\n'

                for product in category_products:
                    product_card = f'''
                        <div class="product-card">
                            <div class="product-image">
                                <img src="{product.get('image_filename', 'ку-ку.jpg')}" alt="{product['name']}" onerror="this.src='ку-ку.jpg'">
                            </div>
                            <div class="product-card-content">
                                <h3>{product['name']}</h3>
                                <p class="price">{product['price']} ₽</p>
                                <button class="btn-buy">В корзину</button>
                            </div>
                        </div>
                        '''
                    products_html += product_card + '\n'

                # Заменяем старый контент на новый
                new_content = content[:start_idx + len(start_marker)] + products_html + content[end_idx:]

                # Сохраняем обновленный файл
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(new_content)

                print(f"✅ Обновлен файл: {filename} (товаров: {len(category_products)})")


# ========== ОСНОВНЫЕ ОБРАБОТЧИКИ ==========

# Начало работы
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_products()
    new_data = load_new_products()
    clean_old_new_products(new_data)

    stats = (
        f"🛍️ Добро пожаловать в менеджер товаров для 'Сам Кондитер'!\n\n"
        f"📊 Статистика магазина:\n"
        f"📦 Всего товаров: {len(data['products'])}\n"
        f"🆕 Новинок: {len(new_data['new_products'])}\n"
        f"⏱️ Новинки активны: {NEW_PRODUCT_DAYS} дней\n\n"
        f"Выберите действие:"
    )

    await update.message.reply_text(
        stats,
        reply_markup=get_main_menu()
    )
    return MAIN_MENU


async def main_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "back":
        await query.edit_message_text(
            "Главное меню:",
            reply_markup=get_main_menu()
        )
        return MAIN_MENU

    elif query.data == "add":
        await query.edit_message_text(
            "📂 Выберите категорию для нового товара:",
            reply_markup=get_categories_menu("cat_")
        )
        return SELECT_CATEGORY

    elif query.data == "list":
        data = load_products()
        if not data["products"]:
            await query.edit_message_text(
                "📭 Список товаров пуст.",
                reply_markup=get_main_menu()
            )
            return MAIN_MENU

        # Группируем по категориям
        products_by_category = {}
        for product in data["products"]:
            cat_key = product.get('category')
            if cat_key in CATEGORIES:
                cat_name = CATEGORIES[cat_key]["name"]
            else:
                cat_name = 'Без категории'

            if cat_name not in products_by_category:
                products_by_category[cat_name] = []
            products_by_category[cat_name].append(product)

        message = "📋 Список товаров:\n\n"
        for cat_name, products in products_by_category.items():
            message += f"📁 {cat_name}:\n"
            for product in products:
                message += f"  • ID {product['id']}: {product['name']} - {product['price']}₽\n"
            message += "\n"

        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="back")]])
        )
        return MAIN_MENU

    elif query.data == "view_all":
        data = load_products()
        if not data["products"]:
            await query.edit_message_text(
                "📭 Список товаров пуст.",
                reply_markup=get_main_menu()
            )
            return MAIN_MENU

        await query.edit_message_text(
            "👁️ Просмотр всех товаров:\n\n"
            "Выберите категорию для просмотра товаров:",
            reply_markup=get_all_products_menu(0, "view_")
        )
        return VIEW_ALL_PRODUCTS

    elif query.data == "edit":
        data = load_products()
        if not data["products"]:
            await query.edit_message_text(
                "📭 Список товаров пуст.",
                reply_markup=get_main_menu()
            )
            return MAIN_MENU

        await query.edit_message_text(
            "✏️ Выберите товар для редактирования:\n\n"
            "📄 Используйте кнопки навигации для просмотра всех товаров:",
            reply_markup=get_products_menu(0, "edit_")
        )
        return SELECT_EDIT

    elif query.data == "delete":
        data = load_products()
        if not data["products"]:
            await query.edit_message_text(
                "📭 Список товаров пуст.",
                reply_markup=get_main_menu()
            )
            return MAIN_MENU

        await query.edit_message_text(
            "🗑️ Выберите товар для удаления:\n\n"
            "📄 Используйте кнопки навигации для просмотра всех товаров:",
            reply_markup=get_products_menu(0, "del_")
        )
        return SELECT_DELETE

    elif query.data == "manage_new":
        keyboard = [
            [InlineKeyboardButton("👀 Просмотреть новинки", callback_data="view_new")],
            [InlineKeyboardButton("🗑️ Удалить старые новинки", callback_data="clean_new")],
            [InlineKeyboardButton("🔄 Обновить новинки на сайте", callback_data="update_new_site")],
            [InlineKeyboardButton("🔙 Назад", callback_data="back")]
        ]

        data = load_new_products()
        clean_old_new_products(data)
        new_count = len(data["new_products"])

        await query.edit_message_text(
            f"🆕 Управление новинками\n\n"
            f"📊 Всего новинок: {new_count}\n"
            f"⏱️ Срок новинки: {NEW_PRODUCT_DAYS} дней\n"
            f"📄 Обновляется: Раздел 'Новинки' на главной странице\n\n"
            f"Выберите действие:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return MANAGE_NEW

    return MAIN_MENU


# ========== ПРОСМОТР ВСЕХ ТОВАРОВ ==========

async def view_all_products_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data.startswith("view_cat_"):
        # Пользователь выбрал категорию для просмотра
        try:
            category_index = int(query.data[9:])  # "view_cat_1" -> 1
            context.user_data['view_category_index'] = category_index
            context.user_data['view_page'] = 0

            # Получаем название категории
            data = load_products()
            products_by_category = {}
            for product in data["products"]:
                cat_key = product.get('category')
                if cat_key in CATEGORIES:
                    cat_name = CATEGORIES[cat_key]["name"]
                else:
                    cat_name = 'Без категории'

                if cat_name not in products_by_category:
                    products_by_category[cat_name] = []
                products_by_category[cat_name].append(product)

            sorted_categories = sorted(products_by_category.keys())
            if category_index < len(sorted_categories):
                cat_name = sorted_categories[category_index]
                cat_products = products_by_category[cat_name]

                await query.edit_message_text(
                    f"📁 Категория: {cat_name}\n"
                    f"📦 Товаров: {len(cat_products)}\n\n"
                    f"Выберите товар для просмотра деталей:",
                    reply_markup=get_category_products_menu(category_index, 0, "view_item_")
                )
            else:
                await query.edit_message_text(
                    "❌ Категория не найдена.",
                    reply_markup=get_all_products_menu(0, "view_", show_all=True)
                )
        except ValueError:
            await query.edit_message_text(
                "❌ Ошибка при обработке запроса.",
                reply_markup=get_all_products_menu(0, "view_", show_all=True)
            )

    elif query.data.startswith("view_all_page_"):
        # Переход по страницам списка категорий
        try:
            page = int(query.data[14:])  # "view_all_page_1" -> 1
            await query.edit_message_text(
                "👁️ Просмотр всех товаров:\n\n"
                "Выберите категорию для просмотра товаров:",
                reply_markup=get_all_products_menu(page, "view_", show_all=True)
            )
        except ValueError:
            await query.edit_message_text(
                "❌ Ошибка при обработке запроса.",
                reply_markup=get_main_menu()
            )

    elif query.data.startswith("view_item_"):
        # Пользователь выбрал конкретный товар для просмотра
        try:
            if query.data.startswith("view_item_cat_"):
                # Обработка навигации внутри категории
                parts = query.data[14:].split("_")
                if len(parts) >= 3 and parts[0] == "cat":
                    category_index = int(parts[1])
                    page = int(parts[3])

                    # Получаем название категории
                    data = load_products()
                    products_by_category = {}
                    for product in data["products"]:
                        cat_key = product.get('category')
                        if cat_key in CATEGORIES:
                            cat_name = CATEGORIES[cat_key]["name"]
                        else:
                            cat_name = 'Без категории'

                        if cat_name not in products_by_category:
                            products_by_category[cat_name] = []
                        products_by_category[cat_name].append(product)

                    sorted_categories = sorted(products_by_category.keys())
                    if category_index < len(sorted_categories):
                        cat_name = sorted_categories[category_index]

                        await query.edit_message_text(
                            f"📁 Категория: {cat_name}\n"
                            f"📦 Товаров: {len(products_by_category[cat_name])}\n\n"
                            f"Выберите товар для просмотра деталей:",
                            reply_markup=get_category_products_menu(category_index, page, "view_item_")
                        )
            elif query.data.startswith("view_item_back_to_cats"):
                # Возврат к списку категорий
                await query.edit_message_text(
                    "👁️ Просмотр всех товаров:\n\n"
                    "Выберите категорию для просмотра товаров:",
                    reply_markup=get_all_products_menu(0, "view_", show_all=True)
                )
            else:
                # Просмотр деталей товара
                product_id = int(query.data[10:])  # "view_item_123" -> 123
                product = get_product_by_id(product_id)

                if product:
                    # Проверяем, есть ли товар в новинках
                    new_data = load_new_products()
                    is_new = any(p['id'] == product_id for p in new_data["new_products"])

                    message = (
                        f"📋 Детали товара:\n\n"
                        f"🆔 ID: {product['id']}\n"
                        f"📦 Название: {product['name']}\n"
                        f"💰 Цена: {product['price']}₽\n"
                        f"📂 Категория: {product.get('category_name', 'Без категории')}\n"
                        f"📷 Фото: {product.get('image_filename', 'ку-ку.jpg')}\n"
                        f"📅 Добавлен: {product.get('created_at', 'Неизвестно')}\n"
                        f"🆕 В новинках: {'Да' if is_new else 'Нет'}\n\n"
                    )

                    # Получаем индекс категории для кнопки "Назад"
                    data = load_products()
                    products_by_category = {}
                    for p in data["products"]:
                        cat_key = p.get('category')
                        if cat_key in CATEGORIES:
                            cat_name = CATEGORIES[cat_key]["name"]
                        else:
                            cat_name = 'Без категории'

                        if cat_name not in products_by_category:
                            products_by_category[cat_name] = []
                        products_by_category[cat_name].append(p)

                    sorted_categories = sorted(products_by_category.keys())
                    category_name = product.get('category_name', 'Без категории')

                    # Находим индекс категории
                    category_index = None
                    for i, cat in enumerate(sorted_categories):
                        if cat == category_name:
                            category_index = i
                            break

                    keyboard = []
                    if category_index is not None:
                        keyboard.append([InlineKeyboardButton(
                            "🔙 К товарам категории",
                            callback_data=f"view_item_cat_{category_index}_page_0"
                        )])

                    keyboard.append([InlineKeyboardButton(
                        "🔙 К списку категорий",
                        callback_data="view_item_back_to_cats"
                    )])
                    keyboard.append([InlineKeyboardButton("🔙 На главную", callback_data="back")])

                    await query.edit_message_text(
                        message,
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                else:
                    await query.edit_message_text(
                        "❌ Товар не найден.",
                        reply_markup=get_all_products_menu(0, "view_", show_all=True)
                    )
        except ValueError:
            await query.edit_message_text(
                "❌ Ошибка при обработке запроса.",
                reply_markup=get_main_menu()
            )

    elif query.data == "back":
        await query.edit_message_text(
            "Главное меню:",
            reply_markup=get_main_menu()
        )
        return MAIN_MENU

    return VIEW_ALL_PRODUCTS


# ========== ДОБАВЛЕНИЕ ТОВАРА ==========

# Выбор категории
async def select_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data.startswith("cat_"):
        category_key = query.data[4:]
        context.user_data['category'] = category_key
        context.user_data['category_name'] = CATEGORIES[category_key]["name"]

        await query.edit_message_text(
            f"📂 Категория: {CATEGORIES[category_key]['name']}\n\n"
            f"Введите название товара:"
        )
        return GET_NAME

    return MAIN_MENU


# Получение названия
async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['name'] = update.message.text
    await update.message.reply_text("Введите цену товара (только число):")
    return GET_PRICE


# Получение цены
async def get_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        price = int(update.message.text)
        context.user_data['price'] = price
        await update.message.reply_text(
            "Отправьте фотографию товара или нажмите /skip чтобы пропустить:"
        )
        return GET_PHOTO
    except ValueError:
        await update.message.reply_text("❌ Пожалуйста, введите корректную цену (число). Попробуйте снова:")
        return GET_PRICE


# Получение фото или пропуск
async def get_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        # Получаем название товара
        product_name = context.user_data['name']

        # Создаем безопасное имя файла из названия товара
        safe_filename = create_safe_filename(product_name)

        # Скачиваем фото
        photo_file = await update.message.photo[-1].get_file()

        # Сохраняем в папку сайта
        image_path = os.path.join(SITE_PATH, safe_filename)
        await photo_file.download_to_drive(image_path)

        # Сохраняем только имя файла
        context.user_data['image_filename'] = safe_filename
        print(f"📸 Фото сохранено как: {safe_filename}")
    else:
        context.user_data['image_filename'] = "ку-ку.jpg"

    # Сохраняем товар в основной файл
    data = load_products()

    product = {
        "id": generate_id(data),
        "name": context.user_data['name'],
        "price": context.user_data['price'],
        "image_filename": context.user_data['image_filename'],
        "category": context.user_data['category'],
        "category_name": context.user_data['category_name'],
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    data["products"].append(product)
    save_products(data)

    # ДОБАВЛЯЕМ ТОВАР В НОВИНКИ!
    add_to_new_products(product)

    # Обновляем HTML файлы
    update_html_files()

    await update.message.reply_text(
        f"✅ Товар успешно добавлен на сайт!\n\n"
        f"📂 Категория: {product['category_name']}\n"
        f"📦 Название: {product['name']}\n"
        f"💰 Цена: {product['price']}₽\n"
        f"🆔 ID: {product['id']}\n"
        f"📷 Файл фото: {product['image_filename']}\n"
        f"🆕 Товар добавлен в НОВИНКИ!\n"
        f"📄 Обновлены файлы:\n"
        f"  • {CATEGORIES[product['category']]['file']}\n"
        f"  • Главная страница (раздел 'Новинки')",
        reply_markup=get_main_menu()
    )

    context.user_data.clear()
    return MAIN_MENU


async def skip_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Для пропущенных фото используем стандартное изображение
    context.user_data['image_filename'] = "ку-ку.jpg"

    # Сохраняем товар в основной файл
    data = load_products()

    product = {
        "id": generate_id(data),
        "name": context.user_data['name'],
        "price": context.user_data['price'],
        "image_filename": "ку-ку.jpg",
        "category": context.user_data['category'],
        "category_name": context.user_data['category_name'],
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    data["products"].append(product)
    save_products(data)

    # ДОБАВЛЯЕМ ТОВАР В НОВИНКИ!
    add_to_new_products(product)

    # Обновляем HTML файлы
    update_html_files()

    await update.message.reply_text(
        f"✅ Товар успешно добавлен на сайт!\n\n"
        f"📂 Категория: {product['category_name']}\n"
        f"📦 Название: {product['name']}\n"
        f"💰 Цена: {product['price']}₽\n"
        f"🆔 ID: {product['id']}\n"
        f"📷 Использовано стандартное изображение\n"
        f"🆕 Товар добавлен в НОВИНКИ!\n"
        f"📄 Обновлены файлы:\n"
        f"  • {CATEGORIES[product['category']]['file']}\n"
        f"  • Главная страница (раздел 'Новинки')",
        reply_markup=get_main_menu()
    )

    context.user_data.clear()
    return MAIN_MENU


# ========== РЕДАКТИРОВАНИЕ ТОВАРА ==========

async def select_edit_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data.startswith("edit_"):
        if query.data.startswith("edit_page_"):
            # Обработка пагинации
            try:
                page = int(query.data[10:])  # "edit_page_1" -> 1
                await query.edit_message_text(
                    "✏️ Выберите товар для редактирования:\n\n"
                    "📄 Используйте кнопки навигации для просмотра всех товаров:",
                    reply_markup=get_products_menu(page, "edit_")
                )
                return SELECT_EDIT
            except ValueError:
                await query.edit_message_text(
                    "❌ Ошибка при обработке запроса.",
                    reply_markup=get_main_menu()
                )
                return MAIN_MENU

        # Выбор конкретного товара
        product_id = int(query.data[5:])
        context.user_data['edit_id'] = product_id

        product = get_product_by_id(product_id)
        if not product:
            await query.edit_message_text(
                "❌ Товар не найден.",
                reply_markup=get_main_menu()
            )
            context.user_data.clear()
            return MAIN_MENU

        keyboard = [
            [InlineKeyboardButton("📝 Название", callback_data="edit_name")],
            [InlineKeyboardButton("💰 Цена", callback_data="edit_price")],
            [InlineKeyboardButton("📂 Категория", callback_data="edit_cat")],
            [InlineKeyboardButton("🔙 Назад", callback_data="back")]
        ]

        message = (
            f"✏️ Редактирование товара:\n\n"
            f"🆔 ID: {product['id']}\n"
            f"📦 Название: {product['name']}\n"
            f"💰 Цена: {product['price']}₽\n"
            f"📂 Категория: {product.get('category_name', 'Без категории')}\n\n"
            f"Что вы хотите изменить?"
        )

        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return EDIT_FIELD

    return MAIN_MENU


async def edit_field_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    product_id = context.user_data.get('edit_id')
    if not product_id:
        await query.edit_message_text(
            "❌ Ошибка: ID товара не найден.",
            reply_markup=get_main_menu()
        )
        return MAIN_MENU

    if query.data == "edit_name":
        await query.edit_message_text(f"Введите новое название для товара ID {product_id}:")
        context.user_data['edit_field'] = 'name'
        return EDIT_NAME

    elif query.data == "edit_price":
        await query.edit_message_text(f"Введите новую цену для товара ID {product_id}:")
        context.user_data['edit_field'] = 'price'
        return EDIT_PRICE

    elif query.data == "edit_cat":
        await query.edit_message_text(
            "📂 Выберите новую категорию:",
            reply_markup=get_categories_menu("newcat_")
        )
        context.user_data['edit_field'] = 'category'
        return SELECT_CATEGORY

    return MAIN_MENU


async def update_edited_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    product_id = context.user_data.get('edit_id')

    if not product_id:
        await update.message.reply_text(
            "❌ Ошибка: ID товара не найден.",
            reply_markup=get_main_menu()
        )
        context.user_data.clear()
        return MAIN_MENU

    try:
        price = int(update.message.text)

        data = load_products()
        updated = False

        for product in data["products"]:
            if product["id"] == product_id:
                product['price'] = price
                message = f"✅ Цена товара ID {product_id} обновлена!"
                updated = True
                break

        if updated:
            save_products(data)
            # Обновляем также в новинках если товар там есть
            update_new_product(product_id, {'price': price})
            # Обновляем HTML файлы
            update_html_files()
            await update.message.reply_text(
                f"{message}\n\n📄 Изменения применены на сайте!",
                reply_markup=get_main_menu()
            )
        else:
            await update.message.reply_text(
                "❌ Товар не найден.",
                reply_markup=get_main_menu()
            )

    except ValueError:
        await update.message.reply_text(
            "❌ Неверный формат цены. Введите число:",
            reply_markup=get_main_menu()
        )
        return EDIT_PRICE

    context.user_data.clear()
    return MAIN_MENU


async def update_edited_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    product_id = context.user_data.get('edit_id')

    if not product_id:
        await update.message.reply_text(
            "❌ Ошибка: ID товара не найден.",
            reply_markup=get_main_menu()
        )
        context.user_data.clear()
        return MAIN_MENU

    name = update.message.text

    data = load_products()
    updated = False

    for product in data["products"]:
        if product["id"] == product_id:
            product['name'] = name
            message = f"✅ Название товара ID {product_id} обновлено!"
            updated = True
            break

    if updated:
        save_products(data)
        # Обновляем также в новинках если товар там есть
        update_new_product(product_id, {'name': name})
        # Обновляем HTML файлы
        update_html_files()
        await update.message.reply_text(
            f"{message}\n\n📄 Изменения применены на сайте!",
            reply_markup=get_main_menu()
        )
    else:
        await update.message.reply_text(
            "❌ Товар не найден.",
            reply_markup=get_main_menu()
        )

    context.user_data.clear()
    return MAIN_MENU


async def update_category_for_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data.startswith("newcat_"):
        product_id = context.user_data.get('edit_id')
        category_key = query.data[7:]  # Убираем "newcat_"

        if not product_id:
            await query.edit_message_text(
                "❌ Ошибка: ID товара не найден.",
                reply_markup=get_main_menu()
            )
            return MAIN_MENU

        data = load_products()
        updated = False

        for product in data["products"]:
            if product["id"] == product_id:
                product['category'] = category_key
                product['category_name'] = CATEGORIES[category_key]["name"]
                message = f"✅ Категория товара ID {product_id} изменена на: {CATEGORIES[category_key]['name']}"
                updated = True
                break

        if updated:
            save_products(data)
            # Обновляем также в новинках если товар там есть
            update_new_product(product_id, {
                'category': category_key,
                'category_name': CATEGORIES[category_key]["name"]
            })
            # Обновляем HTML файлы
            update_html_files()
            await query.edit_message_text(
                f"{message}\n\n📄 Изменения применены на сайте!",
                reply_markup=get_main_menu()
            )
        else:
            await query.edit_message_text(
                "❌ Товар не найден.",
                reply_markup=get_main_menu()
            )

        context.user_data.clear()

    return MAIN_MENU


# ========== УДАЛЕНИЕ ТОВАРА ==========

async def select_delete_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data.startswith("del_"):
        if query.data.startswith("del_page_"):
            # Обработка пагинации
            try:
                page = int(query.data[9:])  # "del_page_1" -> 1
                await query.edit_message_text(
                    "🗑️ Выберите товар для удаления:\n\n"
                    "📄 Используйте кнопки навигации для просмотра всех товаров:",
                    reply_markup=get_products_menu(page, "del_")
                )
                return SELECT_DELETE
            except ValueError:
                await query.edit_message_text(
                    "❌ Ошибка при обработке запроса.",
                    reply_markup=get_main_menu()
                )
                return MAIN_MENU

        # Выбор конкретного товара
        product_id = int(query.data[4:])
        context.user_data['delete_id'] = product_id

        product = get_product_by_id(product_id)
        if not product:
            await query.edit_message_text(
                "❌ Товар не найден.",
                reply_markup=get_main_menu()
            )
            context.user_data.clear()
            return MAIN_MENU

        keyboard = [
            [
                InlineKeyboardButton("✅ Да, удалить", callback_data="confirm_delete"),
                InlineKeyboardButton("❌ Нет, отменить", callback_data="cancel_delete")
            ]
        ]

        message = (
            f"🗑️ Вы уверены, что хотите удалить этот товар?\n\n"
            f"🆔 ID: {product['id']}\n"
            f"📦 Название: {product['name']}\n"
            f"📂 Категория: {product.get('category_name', 'Без категории')}\n"
            f"💰 Цена: {product['price']}₽"
        )

        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return CONFIRM_DELETE

    return MAIN_MENU


async def confirm_delete_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "confirm_delete":
        product_id = context.user_data.get('delete_id')

        if product_id:
            data = load_products()
            initial_count = len(data["products"])
            data["products"] = [p for p in data["products"] if p["id"] != product_id]

            if len(data["products"]) < initial_count:
                save_products(data)
                # Также удаляем из новинок если там есть
                remove_from_new_products(product_id)
                # Обновляем HTML файлы
                update_html_files()
                await query.edit_message_text(
                    f"✅ Товар ID {product_id} успешно удален с сайта!",
                    reply_markup=get_main_menu()
                )
            else:
                await query.edit_message_text(
                    "❌ Товар не найден.",
                    reply_markup=get_main_menu()
                )
        else:
            await query.edit_message_text(
                "❌ Ошибка: ID товара не найден.",
                reply_markup=get_main_menu()
            )

    elif query.data == "cancel_delete":
        await query.edit_message_text(
            "❌ Удаление отменено.",
            reply_markup=get_main_menu()
        )

    context.user_data.clear()
    return MAIN_MENU


# ========== УПРАВЛЕНИЕ НОВИНКАМИ ==========

async def manage_new_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "view_new":
        data = load_new_products()
        clean_old_new_products(data)  # Очищаем старые перед показом

        if not data["new_products"]:
            await query.edit_message_text(
                "🆕 Список новинок пуст.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="back")]])
            )
            return MANAGE_NEW

        # Группируем по категориям
        products_by_category = {}
        for product in data["new_products"]:
            cat_name = product.get('category_name', 'Без категории')
            if cat_name not in products_by_category:
                products_by_category[cat_name] = []
            products_by_category[cat_name].append(product)

        message = "🆕 Список новинок:\n\n"
        for cat_name, products in products_by_category.items():
            message += f"📁 {cat_name}:\n"
            for product in products:
                added_date = datetime.strptime(product['added_at'], "%Y-%m-%d %H:%M:%S")
                expires_date = datetime.strptime(product['expires_at'], "%Y-%m-%d %H:%M:%S")
                days_left = (expires_date - datetime.now()).days
                message += f"  • ID {product['id']}: {product['name']} - {product['price']}₽\n"
                message += f"    📅 Добавлен: {added_date.strftime('%d.%m.%Y')}\n"
                message += f"    ⏳ Осталось дней: {max(0, days_left)}\n"
            message += "\n"

        message += f"📄 Новинки отображаются на главной странице в разделе 'Новинки'"

        keyboard = [
            [InlineKeyboardButton("🗑️ Удалить все старые", callback_data="clean_new")],
            [InlineKeyboardButton("🔄 Обновить новинки на сайте", callback_data="update_new_site")],
            [InlineKeyboardButton("🔙 Назад", callback_data="back")]
        ]

        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return MANAGE_NEW

    elif query.data == "clean_new":
        data = load_new_products()
        initial_count = len(data["new_products"])
        data = clean_old_new_products(data)
        removed_count = initial_count - len(data["new_products"])

        await query.edit_message_text(
            f"✅ Очистка завершена!\n\n"
            f"🗑️ Удалено новинок: {removed_count}\n"
            f"🆕 Осталось новинок: {len(data['new_products'])}\n\n"
            f"📄 Раздел 'Новинки' на главной странице обновлен",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="back")]])
        )
        return MANAGE_NEW

    elif query.data == "update_new_site":
        update_new_products_on_main_page()
        await query.edit_message_text(
            f"✅ Раздел 'Новинки' на главной странице обновлен!\n\n"
            f"📄 Файл: gl_stranisa.html\n"
            f"🔗 Откройте главную страницу чтобы увидеть изменения",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="back")]])
        )
        return MANAGE_NEW

    elif query.data == "back":
        await query.edit_message_text(
            "Главное меню:",
            reply_markup=get_main_menu()
        )
        return MAIN_MENU

    return MANAGE_NEW


# ========== ДОПОЛНИТЕЛЬНЫЕ ФУНКЦИИ ==========

# Отмена
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "❌ Операция отменена.",
        reply_markup=get_main_menu()
    )
    context.user_data.clear()
    return MAIN_MENU


# Быстрые команды
async def quick_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Быстрые команды"""
    message = update.message.text.lower()

    if message == '/новинки':
        data = load_new_products()
        clean_old_new_products(data)
        count = len(data["new_products"])
        await update.message.reply_text(
            f"🆕 Всего новинок: {count}\n"
            f"📄 Отображаются на главной странице в разделе 'Новинки'\n"
            f"Используйте меню для управления новинками."
        )
        return

    elif message == '/очиститьновинки':
        data = load_new_products()
        initial_count = len(data["new_products"])
        data = clean_old_new_products(data)
        removed_count = initial_count - len(data["new_products"])
        await update.message.reply_text(
            f"✅ Очистка завершена!\n"
            f"🗑️ Удалено: {removed_count} новинок\n"
            f"🆕 Осталось: {len(data['new_products'])} новинок\n"
            f"📄 Раздел 'Новинки' на главной странице обновлен."
        )
        return

    elif message == '/обновитьновинки':
        update_new_products_on_main_page()
        await update.message.reply_text(
            f"✅ Раздел 'Новинки' на главной странице обновлен!\n"
            f"📄 Файл: gl_stranisa.html"
        )
        return


# ========== ГЛАВНАЯ ФУНКЦИЯ ==========

def main():
    # Создаем JSON файлы если их нет
    if not os.path.exists(JSON_FILE):
        save_products({"products": []})
        print(f"📁 Создан файл товаров: {JSON_FILE}")

    if not os.path.exists(NEW_PRODUCTS_FILE):
        save_new_products({"new_products": []})
        print(f"🆕 Создан файл новинок: {NEW_PRODUCTS_FILE}")

    print(f"📁 Фото будут сохраняться в: {SITE_PATH}")
    print(f"📄 Главная страница: gl_stranisa.html")

    # Создаем начальные маркеры в главном файле если их нет
    if os.path.exists(MAIN_PAGE_FILE):
        with open(MAIN_PAGE_FILE, 'r', encoding='utf-8') as f:
            content = f.read()

        # Проверяем наличие маркеров новинок
        if '<!-- НОВИНКИ_START -->' not in content:
            # Найдем где начинается раздел новинок
            new_section_start = content.find('<div class="products-grid" id="new">')
            if new_section_start != -1:
                # Найдем где начинается products-cards внутри новинок
                cards_start = content.find('<div class="products-cards">', new_section_start)
                if cards_start != -1:
                    # Найдем где заканчивается products-cards
                    cards_end = content.find('</div>', content.find('</div>', cards_start) + 1)

                    if cards_end != -1:
                        # Вставляем маркеры
                        new_content = content[:cards_start + len(
                            '<div class="products-cards">')] + '\n<!-- НОВИНКИ_START -->\n<!-- НОВИНКИ_END -->' + content[
                                          cards_end:]

                        with open(MAIN_PAGE_FILE, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                        print("✅ Добавлены маркеры новинок в главную страницу")

    # Обновляем новинки на главной странице
    update_new_products_on_main_page()

    # Создаем приложение
    application = Application.builder().token(TOKEN).build()

    # Создаем ConversationHandler с правильными настройками
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MAIN_MENU: [
                CallbackQueryHandler(main_menu_handler, pattern="^(add|list|edit|delete|manage_new|view_all|back)$"),
            ],
            SELECT_CATEGORY: [
                CallbackQueryHandler(select_category, pattern="^cat_.*$"),
                CallbackQueryHandler(update_category_for_edit, pattern="^newcat_.*$"),
                CallbackQueryHandler(main_menu_handler, pattern="^back$"),
            ],
            GET_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_name),
                CommandHandler("cancel", cancel),
            ],
            GET_PRICE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_price),
                CommandHandler("cancel", cancel),
            ],
            GET_PHOTO: [
                MessageHandler(filters.PHOTO, get_photo),
                CommandHandler("skip", skip_photo),
                CommandHandler("cancel", cancel),
            ],
            SELECT_EDIT: [
                CallbackQueryHandler(select_edit_product, pattern="^edit_.*$"),
                CallbackQueryHandler(main_menu_handler, pattern="^back$"),
            ],
            EDIT_FIELD: [
                CallbackQueryHandler(edit_field_handler, pattern="^edit_(name|price|cat)$"),
                CallbackQueryHandler(main_menu_handler, pattern="^back$"),
            ],
            EDIT_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, update_edited_name),
                CommandHandler("cancel", cancel),
            ],
            EDIT_PRICE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, update_edited_price),
                CommandHandler("cancel", cancel),
            ],
            SELECT_DELETE: [
                CallbackQueryHandler(select_delete_product, pattern="^del_.*$"),
                CallbackQueryHandler(main_menu_handler, pattern="^back$"),
            ],
            CONFIRM_DELETE: [
                CallbackQueryHandler(confirm_delete_handler, pattern="^(confirm_delete|cancel_delete)$"),
                CallbackQueryHandler(main_menu_handler, pattern="^back$"),
            ],
            MANAGE_NEW: [
                CallbackQueryHandler(manage_new_menu, pattern="^(view_new|clean_new|update_new_site|back)$"),
            ],
            VIEW_ALL_PRODUCTS: [
                CallbackQueryHandler(view_all_products_handler, pattern="^(view_|back).*$"),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False
    )

    # Добавляем обработчики
    application.add_handler(conv_handler)

    # Добавляем обработчик быстрых команд отдельно
    application.add_handler(MessageHandler(
        filters.TEXT & filters.Regex(r'^/(новинки|очиститьновинки|обновитьновинки)$'),
        quick_commands
    ))

    # Запускаем бота
    print("🤖 Бот запущен с функцией новинок на главной странице!")
    print(f"📁 Категории товаров и файлы:")
    for key, cat_info in CATEGORIES.items():
        print(f"  • {key}: {cat_info['name']} -> {cat_info['file']}")
    print(f"\n🆕 Новинки активны: {NEW_PRODUCT_DAYS} дней")
    print(f"📄 Главная страница: gl_stranisa.html")
    print(f"🔗 Раздел 'Новинки' будет обновляться автоматически")
    print(f"📊 Товаров на страницу: {ITEMS_PER_PAGE}")
    print("\n📊 Для начала работы отправьте /start в Telegram")

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()