from app import create_app
from extensions import db
from models import User

app = create_app()

with app.app_context():
    phone = input("Введіть номер телефону користувача: ").strip()

    if not phone:
        print("Номер телефону не введено.")
        raise SystemExit(1)

    user = User.query.filter_by(phone=phone).first()

    if not user:
        print("Користувача не знайдено.")
        raise SystemExit(1)

    user.is_admin = True
    db.session.commit()

    print(f"Користувача {user.phone} зроблено адміністратором.")