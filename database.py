import sqlite3
import logging
from datetime import datetime
from config import config

# Настройка логирования
logging.basicConfig(
    filename='bot.log',
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class Database:
    def __init__(self):
        self.db_name = config.DATABASE_NAME
        self.init_db()

    def get_connection(self):
        """Создание соединения с базой данных"""
        try:
            conn = sqlite3.connect(self.db_name)
            conn.row_factory = sqlite3.Row
            return conn
        except sqlite3.Error as e:
            logging.error(f"Ошибка подключения к БД: {e}")
            return None

    def init_db(self):
        """Инициализация таблиц базы данных"""
        try:
            conn = self.get_connection()
            if conn:
                cursor = conn.cursor()

                # Таблица услуг
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS services (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        category TEXT NOT NULL,
                        name TEXT NOT NULL,
                        price INTEGER NOT NULL,
                        duration TEXT NOT NULL,
                        is_active BOOLEAN DEFAULT TRUE
                    )
                ''')

                # Таблица клиентов
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS clients (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        name TEXT NOT NULL,
                        phone TEXT NOT NULL,
                        service_id INTEGER,
                        appointment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        status TEXT DEFAULT 'pending',
                        FOREIGN KEY (service_id) REFERENCES services (id)
                    )
                ''')

                # Вставка начальных данных
                self._insert_initial_data(cursor)

                conn.commit()
                conn.close()

        except sqlite3.Error as e:
            logging.error(f"Ошибка инициализации БД: {e}")

    def _insert_initial_data(self, cursor):
        """Вставка начальных данных услуг"""
        # Проверяем, есть ли уже данные
        cursor.execute("SELECT COUNT(*) FROM services")
        count = cursor.fetchone()[0]

        if count == 0:
            initial_services = [
                ('Маникюр', 'Классический', 1500, '3 часа'),
                ('Маникюр', 'Гель-лак', 2500, '5 часов'),
                ('Маникюр', 'Аппаратный', 3500, '2 часа'),
                ('Педикюр', 'Аппаратный', 1000, '30 минут'),
                ('Наращивание', 'Верхние формы', 3000, '2 часа'),
                ('Наращивание', 'Типсы', 1500, '1.5 часа')
            ]

            cursor.executemany(
                "INSERT INTO services (category, name, price, duration) VALUES (?, ?, ?, ?)",
                initial_services
            )

    def get_services_by_category(self, category):
        """Получение услуг по категории"""
        try:
            conn = self.get_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM services WHERE category = ? AND is_active = TRUE ORDER BY name",
                    (category,)
                )
                services = cursor.fetchall()
                conn.close()
                return services
        except sqlite3.Error as e:
            logging.error(f"Ошибка получения услуг: {e}")
            return []

    def get_service_by_id(self, service_id):
        """Получение услуги по ID"""
        try:
            conn = self.get_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM services WHERE id = ? AND is_active = TRUE",
                    (service_id,)
                )
                service = cursor.fetchone()
                conn.close()
                return service
        except sqlite3.Error as e:
            logging.error(f"Ошибка получения услуги: {e}")
            return None

    def add_client(self, user_id, name, phone, service_id):
        """Добавление клиента"""
        try:
            conn = self.get_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO clients (user_id, name, phone, service_id) VALUES (?, ?, ?, ?)",
                    (user_id, name, phone, service_id)
                )
                conn.commit()
                client_id = cursor.lastrowid
                conn.close()
                return client_id
        except sqlite3.Error as e:
            logging.error(f"Ошибка добавления клиента: {e}")
            return None

    def get_all_clients(self):
        """Получение всех клиентов"""
        try:
            conn = self.get_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT c.*, s.category, s.name as service_name, s.price, s.duration
                    FROM clients c
                    LEFT JOIN services s ON c.service_id = s.id
                    ORDER BY c.appointment_date DESC
                ''')
                clients = cursor.fetchall()
                conn.close()
                return clients
        except sqlite3.Error as e:
            logging.error(f"Ошибка получения клиентов: {e}")
            return []

    def get_recent_clients(self, days=30):
        """Получение клиентов за последние дни"""
        try:
            conn = self.get_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT c.*, s.category, s.name as service_name, s.price, s.duration
                    FROM clients c
                    LEFT JOIN services s ON c.service_id = s.id
                    WHERE date(c.appointment_date) >= date('now', ?)
                    ORDER BY c.appointment_date DESC
                ''', (f'-{days} days',))
                clients = cursor.fetchall()
                conn.close()
                return clients
        except sqlite3.Error as e:
            logging.error(f"Ошибка получения клиентов: {e}")
            return []

    def update_service(self, service_id, name, price, duration):
        """Обновление услуги"""
        try:
            conn = self.get_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE services SET name = ?, price = ?, duration = ? WHERE id = ?",
                    (name, price, duration, service_id)
                )
                conn.commit()
                conn.close()
                return True
        except sqlite3.Error as e:
            logging.error(f"Ошибка обновления услуги: {e}")
            return False

    def delete_service(self, service_id):
        """Удаление услуги (деактивация)"""
        try:
            conn = self.get_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE services SET is_active = FALSE WHERE id = ?",
                    (service_id,)
                )
                conn.commit()
                conn.close()
                return True
        except sqlite3.Error as e:
            logging.error(f"Ошибка удаления услуги: {e}")
            return False

    def add_service(self, category, name, price, duration):
        """Добавление новой услуги"""
        try:
            conn = self.get_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO services (category, name, price, duration) VALUES (?, ?, ?, ?)",
                    (category, name, price, duration)
                )
                conn.commit()
                service_id = cursor.lastrowid
                conn.close()
                return service_id
        except sqlite3.Error as e:
            logging.error(f"Ошибка добавления услуги: {e}")
            return None

# Создаем экземпляр базы данных
db = Database()
