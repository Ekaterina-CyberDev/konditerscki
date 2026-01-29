import json
import os
from datetime import datetime
from pathlib import Path

# Конфигурация
SITE_PATH = r"C:\Users\kolba\Desktop\konditerscki\gl_stranisa"
NEW_PRODUCTS_FILE = os.path.join(SITE_PATH, "new_products.json")

def clean_new_products():
    """Автоматическая очистка старых новинок"""
    print("🧹 Начинаю очистку старых новинок...")
    
    if not os.path.exists(NEW_PRODUCTS_FILE):
        print("📭 Файл новинок не найден")
        return
    
    with open(NEW_PRODUCTS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if not data.get("new_products"):
        print("📭 Список новинок пуст")
        return
    
    current_time = datetime.now()
    initial_count = len(data["new_products"])
    
    # Фильтруем новинки
    new_list = []
    for product in data["new_products"]:
        try:
            expires_at = datetime.strptime(product['expires_at'], "%Y-%m-%d %H:%M:%S")
            if expires_at > current_time:
                new_list.append(product)
        except (ValueError, KeyError):
            continue
    
    removed_count = initial_count - len(new_list)
    data["new_products"] = new_list
    
    # Сохраняем результат
    with open(NEW_PRODUCTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Очистка завершена!")
    print(f"🗑️ Удалено: {removed_count} новинок")
    print(f"🆕 Осталось: {len(new_list)} новинок")

if __name__ == "__main__":
    clean_new_products()
