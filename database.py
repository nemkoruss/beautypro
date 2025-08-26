import sqlite3
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_name='beauty_salon.db'):
        self.db_name = db_name
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_name)

    def init_db(self):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Services table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS services (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        category TEXT NOT NULL,
                        name TEXT NOT NULL,
                        price INTEGER NOT NULL,
                        duration TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # Clients table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS clients (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        name TEXT NOT NULL,
                        phone TEXT NOT NULL,
                        service_category TEXT NOT NULL,
                        service_name TEXT NOT NULL,
                        service_price INTEGER NOT NULL,
                        service_duration TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        status TEXT DEFAULT 'pending'
                    )
                ''')

                # Insert default services
                self._insert_default_services(cursor)

                conn.commit()

        except Exception as e:
            logger.error(f"Error initializing database: {e}")

    def _insert_default_services(self, cursor):
        # Check if services already exist
        cursor.execute("SELECT COUNT(*) FROM services")
        if cursor.fetchone()[0] == 0:
            default_services = [
                ('Маникюр', 'Классический', 1500, '3 часа'),
                ('Маникюр', 'Гель-лак', 2500, '5 часов'),
                ('Маникюр', 'Аппаратный', 3500, '2 часа'),
                ('Педикюр', 'Аппаратный', 1000, '30 минут'),
                ('Наращивание', 'Верхние формы', 3000, '2 часа'),
                ('Наращивание', 'Типсы', 1500, '1.5 часа')
            ]

            cursor.executemany('''
                INSERT INTO services (category, name, price, duration)
                VALUES (?, ?, ?, ?)
            ''', default_services)

    def get_services_by_category(self, category):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, name, price, duration FROM services
                    WHERE category = ? ORDER BY name
                ''', (category,))
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Error getting services: {e}")
            return []

    def get_all_categories(self):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT DISTINCT category FROM services ORDER BY category')
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting categories: {e}")
            return []

    def get_service_by_id(self, service_id):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM services WHERE id = ?', (service_id,))
                return cursor.fetchone()
        except Exception as e:
            logger.error(f"Error getting service: {e}")
            return None

    def add_client(self, user_id, name, phone, service_category, service_name, service_price, service_duration):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO clients (user_id, name, phone, service_category, service_name, service_price, service_duration)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (user_id, name, phone, service_category, service_name, service_price, service_duration))
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error adding client: {e}")
            return None

    def get_all_clients(self):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, name, phone, service_category, service_name, service_price, service_duration, created_at, status
                    FROM clients ORDER BY created_at DESC
                ''')
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Error getting clients: {e}")
            return []

    def get_recent_clients(self, days=30):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, name, phone, service_category, service_name, service_price, service_duration, created_at, status
                    FROM clients
                    WHERE created_at >= date('now', ?)
                    ORDER BY created_at DESC
                ''', (f'-{days} days',))
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Error getting recent clients: {e}")
            return []

    def add_service(self, category, name, price, duration):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO services (category, name, price, duration)
                    VALUES (?, ?, ?, ?)
                ''', (category, name, price, duration))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error adding service: {e}")
            return False

    def update_service(self, service_id, name, price, duration):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE services SET name = ?, price = ?, duration = ?
                    WHERE id = ?
                ''', (name, price, duration, service_id))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error updating service: {e}")
            return False

    def delete_service(self, service_id):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM services WHERE id = ?', (service_id,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error deleting service: {e}")
            return False
