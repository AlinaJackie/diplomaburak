from extensions import db
from app import create_app
from pathlib import Path
import os
import time

from config import BASE_DIR

db_path = BASE_DIR / "foodgo.db"

# Спочатку видаляємо файл БД, і лише потім імпортуємо app/db
if db_path.exists():
    for _ in range(5):
        try:
            os.remove(db_path)
            print(f"Стару базу видалено: {db_path}")
            break
        except PermissionError:
            print(
                "Файл бази зайнятий. Закрий Flask, DB Browser, SQLite viewer у VS Code та спроба повториться...")
            time.sleep(1)
    else:
        print("Не вдалося видалити базу. Вона все ще використовується іншим процесом.")
        raise SystemExit(1)


app = create_app()

with app.app_context():
    db.create_all()
    print("Нову базу успішно створено")
