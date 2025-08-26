import sqlite3
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_name='beauty_bot.db'):
        self.db_name = db_name
        self.init_db()

    def get_connection(self):
        try:
            conn = sqlite3.connect(self.db_name)
            conn.row_factory = sqlite3.Row
            return conn
        except sqlite3.Error as e:
            logger.error(f"Database connection error: {e}")
            raise

    def init_db(self):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Таблица категорий
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS categories (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL UNIQUE
                    )
                ''')

                # Таблица услуг
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS services (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        category_id INTEGER,
                        name TEXT NOT NULL,
                        price REAL NOT NULL,
                        duration TEXT NOT NULL,
                        FOREIGN KEY (category_id) REFERENCES categories (id)
                    )
                ''')

                # Таблица клиентов
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS clients (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        phone TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # Таблица записей
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS appointments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        client_id INTEGER,
                        service_id INTEGER,
                        status TEXT DEFAULT 'pending',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (client_id) REFERENCES clients (id),
                        FOREIGN KEY (service_id) REFERENCES services (id)
                    )
                ''')

                # Добавляем начальные данные
                self._add_initial_data(cursor)

                conn.commit()
                logger.info("База данных инициализирована успешно")

        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise

    def _add_initial_data(self, cursor):
        try:
            # Добавляем категории
            categories = ['Маникюр', 'Педикюр', 'Наращивание']
            for category in categories:
                cursor.execute('INSERT OR IGNORE INTO categories (name) VALUES (?)', (category,))

            # Получаем ID категорий
            cursor.execute('SELECT id, name FROM categories')
            category_map = {name: id for id, name in cursor.fetchall()}

            # Добавляем начальные услуги
            services_data = [
                (category_map['Маникюр'], 'Классический', 1500.0, '3 часа'),
                (category_map['Маникюр'], 'Гель-лак', 2500.0, '5 часов'),
                (category_map['Маникюр'], 'Аппаратный', 3500.0, '2 часа'),
                (category_map['Педикюр'], 'Аппаратный', 1000.0, '30 минут'),
                (category_map['Наращивание'], 'Верхние формы', 3000.0, '2 часа'),
                (category_map['Наращивание'], 'Типсы', 1500.0, '1.5 часа')
            ]

            for service in services_data:
                cursor.execute('''
                    INSERT OR IGNORE INTO services (category_id, name, price, duration)
                    VALUES (?, ?, ?, ?)
                ''', service)

        except Exception as e:
            logger.error(f"Error adding initial data: {e}")
            raise

    # Методы для работы с категориями
    def get_categories(self):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT id, name FROM categories ORDER BY id')
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Error getting categories: {e}")
            return []

    def get_category_name(self, category_id):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT name FROM categories WHERE id = ?', (category_id,))
                result = cursor.fetchone()
                return result['name'] if result else None
        except Exception as e:
            logger.error(f"Error getting category name: {e}")
            return None

    # Методы для работы с услугами
    def get_services_by_category(self, category_id):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, name, price, duration
                    FROM services
                    WHERE category_id = ?
                    ORDER BY id
                ''', (category_id,))
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Error getting services: {e}")
            return []

    def get_service(self, service_id):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT s.id, s.name, s.price, s.duration, c.name as category_name
                    FROM services s
                    JOIN categories c ON s.category_id = c.id
                    WHERE s.id = ?
                ''', (service_id,))
                result = cursor.fetchone()
                if result:
                    return (result['id'], result['name'], result['price'],
                           result['duration'], result['category_name'])
                return None
        except Exception as e:
            logger.error(f"Error getting service: {e}")
            return None

    def update_service(self, service_id, name, price, duration):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE services
                    SET name = ?, price = ?, duration = ?
                    WHERE id = ?
                ''', (name, price, duration, service_id))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error updating service: {e}")
            return False

    def delete_service(self, service_id):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM services WHERE id = ?', (service_id,))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error deleting service: {e}")
            return False

    def add_service(self, category_id, name, price, duration):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO services (category_id, name, price, duration)
                    VALUES (?, ?, ?, ?)
                ''', (category_id, name, price, duration))
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error adding service: {e}")
            return None

    # Методы для работы с клиентами
    def add_client(self, name, phone):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO clients (name, phone)
                    VALUES (?, ?)
                ''', (name, phone))
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error adding client: {e}")
            return None

    def get_clients(self):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT id, name, phone, created_at FROM clients ORDER BY created_at DESC')
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Error getting clients: {e}")
            return []

    # Методы для работы с записями
    def add_appointment(self, client_id, service_id):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO appointments (client_id, service_id)
                    VALUES (?, ?)
                ''', (client_id, service_id))
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error adding appointment: {e}")
            return None

    def get_appointments_last_30_days(self):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d %H:%M:%S')
                cursor.execute('''
                    SELECT a.id, c.name, c.phone, s.name as service_name,
                           s.price, s.duration, cat.name as category_name, a.created_at
                    FROM appointments a
                    JOIN clients c ON a.client_id = c.id
                    JOIN services s ON a.service_id = s.id
                    JOIN categories cat ON s.category_id = cat.id
                    WHERE a.created_at >= ?
                    ORDER BY a.created_at DESC
                ''', (thirty_days_ago,))
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Error getting appointments: {e}")
            return []
