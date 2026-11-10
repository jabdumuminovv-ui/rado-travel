import os
import json
import uuid
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

DATA_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
USERS_FILE = os.path.join(DATA_DIR, "users.json")
SESSIONS_FILE = os.path.join(DATA_DIR, "sessions.json")

def hash_password(password: str) -> str:
    # Простой и надежный SHA-256 с солью для полной независимости от тяжелых C-библиотек
    salt = "rado_travel_secure_salt_2026"
    return hashlib.sha256((password + salt).encode('utf-8')).hexdigest()

def get_default_users() -> List[Dict[str, Any]]:
    now = datetime.now().isoformat()
    return [
        {
            "id": "usr_admin",
            "login": "admin",
            "password_hash": hash_password("rado2026admin"),
            "raw_password": "rado2026admin",  # Сохраняем для удобного копирования админом
            "agency_name": "RaDo Travel HQ",
            "manager_name": "Главный Администратор",
            "phone": "+998 90 000-00-00",
            "telegram": "@radotravel",
            "role": "admin",
            "is_active": True,
            "subscription_plan": "lifetime",
            "expires_at": None,
            "price_paid": 0.0,
            "created_at": now,
            "last_login": None,
            "notes": "Главный аккаунт владельца платформы"
        },
        {
            "id": "usr_friend",
            "login": "partner",
            "password_hash": hash_password("rado777partner"),
            "raw_password": "rado777partner",
            "agency_name": "VIP Partner Agency",
            "manager_name": "Партнёр",
            "phone": "+998 90 123-45-67",
            "telegram": "@partner",
            "role": "user",
            "is_active": True,
            "subscription_plan": "lifetime",
            "expires_at": None,
            "price_paid": 0.0,
            "created_at": now,
            "last_login": None,
            "notes": "Постоянный бесплатный доступ для друга"
        }
    ]

class AuthService:
    def __init__(self):
        self._load_users()
        self._load_sessions()

    def _load_users(self):
        if not os.path.exists(USERS_FILE):
            self.users = get_default_users()
            self._save_users()
        else:
            try:
                with open(USERS_FILE, "r", encoding="utf-8") as f:
                    self.users = json.load(f)
            except Exception:
                self.users = get_default_users()
                self._save_users()

    def _save_users(self):
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(self.users, f, ensure_ascii=False, indent=2)

    def _load_sessions(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        if os.path.exists(SESSIONS_FILE):
            try:
                with open(SESSIONS_FILE, "r", encoding="utf-8") as f:
                    self.sessions = json.load(f)
            except Exception:
                self.sessions = {}

    def _save_sessions(self):
        with open(SESSIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(self.sessions, f, ensure_ascii=False, indent=2)

    def authenticate(self, login: str, password: str) -> Dict[str, Any]:
        login = login.strip().lower()
        user = next((u for u in self.users if u["login"].lower() == login), None)
        if not user:
            raise ValueError("Пользователь с таким логином не найден")

        pwd_hash = hash_password(password)
        if user["password_hash"] != pwd_hash and user.get("raw_password") != password:
            raise ValueError("Неверный пароль")

        if not user.get("is_active", True):
            raise ValueError("Доступ заблокирован администратором. Свяжитесь с RaDo Travel: @radotravel")

        # Проверка срока подписки
        if user.get("subscription_plan") != "lifetime" and user.get("expires_at"):
            try:
                exp = datetime.fromisoformat(user["expires_at"])
                if datetime.now() > exp:
                    raise ValueError(f"Срок действия вашей подписки истёк ({exp.strftime('%d.%m.%Y')}). Для продления напишите в @radotravel")
            except Exception as e:
                if "подписки истёк" in str(e):
                    raise

        # Обновляем last_login
        user["last_login"] = datetime.now().isoformat()
        self._save_users()

        # Создаем сессию
        token = secrets.token_urlsafe(32)
        self.sessions[token] = {
            "user_id": user["id"],
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(days=30)).isoformat()
        }
        self._save_sessions()

        user_info = self._format_user_info(user)
        return {
            "token": token,
            "user": user_info
        }

    def verify_token(self, token: str) -> Dict[str, Any]:
        if not token or token not in self.sessions:
            raise ValueError("Не авторизован. Пожалуйста, войдите в систему.")

        session = self.sessions[token]
        user = next((u for u in self.users if u["id"] == session["user_id"]), None)
        if not user:
            raise ValueError("Пользователь не найден")

        if not user.get("is_active", True):
            raise ValueError("Ваш аккаунт заблокирован администратором")

        # Проверка срока действия подписки
        if user.get("subscription_plan") != "lifetime" and user.get("expires_at"):
            try:
                exp = datetime.fromisoformat(user["expires_at"])
                if datetime.now() > exp:
                    raise ValueError(f"Срок действия подписки истёк {exp.strftime('%d.%m.%Y')}. Обратитесь в @radotravel")
            except Exception as e:
                if "подписки истёк" in str(e):
                    raise

        return self._format_user_info(user)

    def logout(self, token: str):
        if token in self.sessions:
            del self.sessions[token]
            self._save_sessions()

    def _format_user_info(self, u: Dict[str, Any]) -> Dict[str, Any]:
        days_left = None
        is_expired = False
        if u.get("subscription_plan") == "lifetime":
            days_left = 9999
        elif u.get("expires_at"):
            try:
                exp = datetime.fromisoformat(u["expires_at"])
                delta = exp - datetime.now()
                days_left = max(0, delta.days)
                if delta.total_seconds() < 0:
                    is_expired = True
            except Exception:
                pass

        return {
            "id": u["id"],
            "login": u["login"],
            "raw_password": u.get("raw_password", "******"),
            "agency_name": u.get("agency_name", "Турагентство"),
            "manager_name": u.get("manager_name", ""),
            "phone": u.get("phone", ""),
            "telegram": u.get("telegram", ""),
            "role": u.get("role", "user"),
            "is_active": u.get("is_active", True),
            "subscription_plan": u.get("subscription_plan", "monthly"),
            "expires_at": u.get("expires_at"),
            "days_left": days_left,
            "is_expired": is_expired,
            "price_paid": u.get("price_paid", 0.0),
            "created_at": u.get("created_at"),
            "last_login": u.get("last_login"),
            "notes": u.get("notes", "")
        }

    # Админские методы
    def get_all_users(self) -> List[Dict[str, Any]]:
        return [self._format_user_info(u) for u in self.users]

    def create_user(self, data: Dict[str, Any]) -> Dict[str, Any]:
        login = data.get("login", "").strip().lower()
        if not login:
            raise ValueError("Логин обязателен")

        if any(u["login"].lower() == login for u in self.users):
            raise ValueError(f"Пользователь с логином '{login}' уже существует")

        password = data.get("password", "").strip() or "rado" + secrets.token_hex(3)
        plan = data.get("subscription_plan", "monthly")
        
        expires_at = None
        if plan == "trial_7d":
            expires_at = (datetime.now() + timedelta(days=7)).isoformat()
        elif plan == "monthly":
            expires_at = (datetime.now() + timedelta(days=30)).isoformat()
        elif plan == "quarterly":
            expires_at = (datetime.now() + timedelta(days=90)).isoformat()
        elif plan == "yearly":
            expires_at = (datetime.now() + timedelta(days=365)).isoformat()
        elif plan == "lifetime":
            expires_at = None

        new_user = {
            "id": f"usr_{uuid.uuid4().hex[:8]}",
            "login": login,
            "password_hash": hash_password(password),
            "raw_password": password,
            "agency_name": data.get("agency_name", "Новое агентство"),
            "manager_name": data.get("manager_name", ""),
            "phone": data.get("phone", ""),
            "telegram": data.get("telegram", ""),
            "role": data.get("role", "user"),
            "is_active": True,
            "subscription_plan": plan,
            "expires_at": expires_at,
            "price_paid": float(data.get("price_paid", 0.0)),
            "created_at": datetime.now().isoformat(),
            "last_login": None,
            "notes": data.get("notes", "")
        }
        self.users.append(new_user)
        self._save_users()
        return self._format_user_info(new_user)

    def update_user(self, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        user = next((u for u in self.users if u["id"] == user_id), None)
        if not user:
            raise ValueError("Пользователь не найден")

        if "password" in data and data["password"]:
            user["password_hash"] = hash_password(data["password"])
            user["raw_password"] = data["password"]

        if "agency_name" in data and data["agency_name"]:
            user["agency_name"] = data["agency_name"]

        if "manager_name" in data:
            user["manager_name"] = data["manager_name"]

        if "phone" in data:
            user["phone"] = data["phone"]

        if "telegram" in data:
            user["telegram"] = data["telegram"]

        if "is_active" in data:
            user["is_active"] = bool(data["is_active"])

        if "notes" in data:
            user["notes"] = data["notes"]

        if "price_paid" in data:
            user["price_paid"] = float(data["price_paid"])

        # Продление подписки
        if "extend_days" in data and data["extend_days"]:
            days = int(data["extend_days"])
            current_exp = datetime.now()
            if user.get("expires_at"):
                try:
                    parsed_exp = datetime.fromisoformat(user["expires_at"])
                    if parsed_exp > current_exp:
                        current_exp = parsed_exp
                except Exception:
                    pass
            user["expires_at"] = (current_exp + timedelta(days=days)).isoformat()
            if user["subscription_plan"] == "lifetime":
                pass
            else:
                user["subscription_plan"] = "extended"

        if "subscription_plan" in data and data["subscription_plan"]:
            plan = data["subscription_plan"]
            user["subscription_plan"] = plan
            if plan == "lifetime":
                user["expires_at"] = None
            elif plan == "monthly":
                user["expires_at"] = (datetime.now() + timedelta(days=30)).isoformat()
            elif plan == "quarterly":
                user["expires_at"] = (datetime.now() + timedelta(days=90)).isoformat()
            elif plan == "yearly":
                user["expires_at"] = (datetime.now() + timedelta(days=365)).isoformat()

        self._save_users()
        return self._format_user_info(user)

    def delete_user(self, user_id: str) -> bool:
        user = next((u for u in self.users if u["id"] == user_id), None)
        if not user:
            return False
        if user["role"] == "admin" and user["login"] == "admin":
            raise ValueError("Нельзя удалить главного администратора платформы")
        self.users = [u for u in self.users if u["id"] != user_id]
        self._save_users()
        return True

    def get_stats(self) -> Dict[str, Any]:
        total_users = len(self.users)
        active_users = 0
        expired_users = 0
        total_revenue = 0.0

        for u in self.users:
            if u["role"] == "admin":
                continue
            total_revenue += float(u.get("price_paid", 0.0))
            if not u.get("is_active", True):
                continue

            if u.get("subscription_plan") == "lifetime":
                active_users += 1
            elif u.get("expires_at"):
                try:
                    exp = datetime.fromisoformat(u["expires_at"])
                    if datetime.now() <= exp:
                        active_users += 1
                    else:
                        expired_users += 1
                except Exception:
                    expired_users += 1
            else:
                active_users += 1

        return {
            "total_agencies": total_users - 1, # исключая админа
            "active_subscriptions": active_users,
            "expired_subscriptions": expired_users,
            "total_revenue": total_revenue,
            "currency": "USD"
        }
