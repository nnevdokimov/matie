from sberjazz import get_meet
import sqlite3
from flask import g

class ChatTaskManagerDB:
    # Инициализация менеджера задач с путём к базе данных
    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path)
        self.init_db()

    # Создание таблиц базы данных, если они ещё не существуют
    def init_db(self):
        cursor = self.conn.cursor()
        # Таблица пользователей
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, name TEXT UNIQUE)''')
        # Таблица задач с внешним ключом на пользователей
        cursor.execute('''CREATE TABLE IF NOT EXISTS tasks (task_id INTEGER PRIMARY KEY, name TEXT, assigned_user_id INTEGER, deadline TEXT, status TEXT, FOREIGN KEY(assigned_user_id) REFERENCES users(user_id))''')
        self.conn.commit()

    # Получение подключения к базе данных через Flask global object g
    def get_conn(self):
        if 'db_conn' not in g:
            g.db_conn = sqlite3.connect(self.db_path)
            g.db_conn.row_factory = sqlite3.Row
        return g.db_conn

    # Добавление пользователя в базу данных
    def add_user(self, user_id, name):
        try:
            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO users (user_id, name) VALUES (?, ?)", (user_id, name))
            self.conn.commit()
            return f"Пользователь {name} добавлен с ID {user_id}"
        except sqlite3.IntegrityError:
            return "Пользователь с таким именем или ID уже существует."

    # Поиск пользователя по имени
    def find_user_by_name(self, name):
        cursor = self.conn.cursor()
        cursor.execute("SELECT user_id FROM users WHERE name = ?", (name,))
        user = cursor.fetchone()
        return user[0] if user else None

    # Добавление задачи в базу данных
    def add_task(self, name, user_name, deadline=None):
        user_id = self.find_user_by_name(user_name)
        if user_id is None:
            return "Пользователь не найден"

        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO tasks (name, assigned_user_id, deadline, status) VALUES (?, ?, ?, ?)", (name, user_id, deadline, 'Не начато'))
        task_id = cursor.lastrowid
        self.conn.commit()
        return f"Задача '{name}' добавлена для {user_name}"

    # Отображение всех задач пользователя
    def show_tasks_by_user_name(self, user_name):
        user_id = self.find_user_by_name(user_name)
        if user_id is None:
            return "Пользователь не найден"

        cursor = self.conn.cursor()
        cursor.execute("SELECT task_id, name, status FROM tasks WHERE assigned_user_id = ?", (user_id,))
        tasks = cursor.fetchall()
        return "\n".join([f"ID: {task_id}, Задача: {name}, Статус: {status}" for task_id, name, status in tasks]) if tasks else "У пользователя нет задач"

    # Обновление статуса задачи
    def update_task_status_by_task_name(self, task_name, new_status, user_name):
        user_id = self.find_user_by_name(user_name)
        if user_id is None:
            return "Пользователь не найден"

        task_ids = self.find_tasks_by_name_id(task_name, user_id)
        if not task_ids:
            return "Задача с таким названием не найдена"

        cursor = self.conn.cursor()
        cursor.execute("UPDATE tasks SET status = ? WHERE name = ? AND assigned_user_id = ?", (new_status, task_name, user_id))
        updated_tasks_count = cursor.rowcount
        self.conn.commit()

        return f"Статус задачи обновлен на {new_status}" if updated_tasks_count > 0 else "Нет задач для обновления"

    # Обновление дедлайна задачи
    def update_task_deadline_by_name(self, task_name, new_deadline, user_name):
        user_id = self.find_user_by_name(user_name)
        if user_id is None:
            return "Пользователь не найден"

        task_ids = self.find_tasks_by_name_id(task_name, user_id)
        if not task_ids:
            return "Задача с таким названием не найдена"

        cursor = self.conn.cursor()
        cursor.execute("UPDATE tasks SET deadline = ? WHERE name = ? AND assigned_user_id = ?", (new_deadline, task_name, user_id))
        updated_tasks_count = cursor.rowcount
        self.conn.commit()

        return f"Дедлайн обновлён для {updated_tasks_count} задач" if updated_tasks_count > 0 else "Нет задач для обновления"

    def find_tasks_by_name_id(self, task_name, user_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT task_id FROM tasks WHERE name = ? AND assigned_user_id = ?", (task_name,user_id))
        return [task_id for task_id, in cursor.fetchall()]


# Путь к базе данных и создание экземпляра менеджера задач
db_path = 'chat_task_manager.db'
task_manager = ChatTaskManagerDB(db_path)

# Функция для обработки запросов связанных с управлением задачами
def task_manager_stat(json_data, user_id, user_name):
    # Используем глобальный объект g, если user_id равен -1
    task_manager = g.task_manager if user_id == -1 else ChatTaskManagerDB(db_path)

    # Проверка и добавление пользователя, если он не существует
    if task_manager.find_user_by_name(user_name) is None:
        task_manager.add_user(user_id, user_name)

    # Извлечение деталей задачи из данных запроса
    data = json_data.get('details', {})
    task_title = data.get('task_title', '').lower()
    task_type = json_data['type']

    # Обработка запроса в зависимости от типа задачи
    if task_type == 'create_task':
        deadline = data.get('deadline')
        return task_manager.add_task(name=task_title, user_name=user_name, deadline=deadline)
    elif task_type == 'change_status':
        new_status = data.get('new_status')
        return task_manager.update_task_status_by_task_name(task_name=task_title, new_status=new_status, user_name=user_name)
    elif task_type == 'change_deadline':
        new_deadline = data.get('deadline')
        return task_manager.update_task_deadline_by_name(task_name=task_title, new_deadline=new_deadline, user_name=user_name)
    elif task_type == 'all_tasks':
        return task_manager.show_tasks_by_user_name(user_name=user_name)
    elif task_type == 'ask_giga':
        # Заполнитель для реализации в будущем или обработки ошибок
        return "Функциональность не реализована."
    elif task_type == 'create_meeting':
        name = data.get('meeting_name')
        return get_meet(name)
    else:
        # Обработка неизвестного типа задачи
        return f"Неизвестный тип задачи: {task_type}"
