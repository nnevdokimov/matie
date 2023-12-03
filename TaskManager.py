from sberjazz import get_meet
import sqlite3

class ChatTaskManagerDB:
    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path)
        self.init_db()

    def init_db(self):
        cursor = self.conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, name TEXT UNIQUE)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS tasks (task_id INTEGER PRIMARY KEY, name TEXT, assigned_user_id INTEGER, deadline TEXT, status TEXT, FOREIGN KEY(assigned_user_id) REFERENCES users(user_id))''')
        self.conn.commit()

    def add_user(self, user_id, name):
        try:
            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO users (user_id, name) VALUES (?, ?)", (user_id, name))
            self.conn.commit()
            return f"Пользователь {name} добавлен с ID {user_id}"
        except sqlite3.IntegrityError:
            return "Пользователь с таким именем или ID уже существует."

    def find_user_by_name(self, name):
        cursor = self.conn.cursor()
        cursor.execute("SELECT user_id FROM users WHERE name = ?", (name,))
        user = cursor.fetchone()
        return user[0] if user else None

    def add_task(self, name, user_name, deadline=None, status='Not Started'):
        user_id = self.find_user_by_name(user_name)
        if user_id is None:
            return "Пользователь не найден"

        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO tasks (name, assigned_user_id, deadline, status) VALUES (?, ?, ?, ?)", (name, user_id, deadline, status))
        task_id = cursor.lastrowid
        self.conn.commit()
        return f"Задача '{name}' добавлена для {user_name} с ID {task_id}"

    def show_tasks_by_user_name(self, user_name):
        user_id = self.find_user_by_name(user_name)
        if user_id is None:
            return "Пользователь не найден"

        cursor = self.conn.cursor()
        cursor.execute("SELECT task_id, name, status FROM tasks WHERE assigned_user_id = ?", (user_id,))
        tasks = cursor.fetchall()
        return "\n".join([f"ID: {task_id}, Задача: {name}, Статус: {status}" for task_id, name, status in tasks]) if tasks else "У пользователя нет задач"

    def find_tasks_by_name(self, task_name):
        cursor = self.conn.cursor()
        cursor.execute("SELECT task_id FROM tasks WHERE name = ?", (task_name,))
        return [task_id for task_id, in cursor.fetchall()]

    def update_task_status_by_task_name(self, task_name, new_status, user_name):
        user_id = self.find_user_by_name(user_name)
        if user_id is None:
            return "Пользователь не найден"

        task_ids = self.find_tasks_by_name(task_name)
        if not task_ids:
            return "Задача с таким названием не найдена"

        cursor = self.conn.cursor()
        cursor.execute("UPDATE tasks SET status = ? WHERE name = ? AND assigned_user_id = ?", (new_status, task_name, user_id))
        updated_tasks_count = cursor.rowcount
        self.conn.commit()

        return f"Статус обновлён для {updated_tasks_count} задач" if updated_tasks_count > 0 else "Нет задач для обновления"

    def update_task_deadline_by_name(self, task_name, new_deadline, user_name):
        user_id = self.find_user_by_name(user_name)
        if user_id is None:
            return "Пользователь не найден"

        task_ids = self.find_tasks_by_name(task_name)
        if not task_ids:
            return "Задача с таким названием не найдена"

        cursor = self.conn.cursor()
        cursor.execute("UPDATE tasks SET deadline = ? WHERE name = ? AND assigned_user_id = ?", (new_deadline, task_name, user_id))
        updated_tasks_count = cursor.rowcount
        self.conn.commit()

        return f"Дедлайн обновлён для {updated_tasks_count} задач" if updated_tasks_count > 0 else "Нет задач для обновления"

db_path = 'chat_task_manager.db'
task_manager = ChatTaskManagerDB(db_path)


def task_manager_stat(json_data, user_id, user_name):
    # Проверка существования пользователя перед добавлением
    if task_manager.find_user_by_name(user_name) is None:
        user_addition_result = task_manager.add_user(user_id, user_name)
    data = json_data.get('details', {})

    if json_data['type'] == 'create_task':
        return task_manager.add_task(name=data.get('task_title', '').lower(), user_name=user_name, deadline=data.get('deadline'))
    elif json_data['type'] == 'change_status':
        return task_manager.update_task_status_by_task_name(task_name=data.get('task_title', '').lower(), user_name=user_name,
                                                            new_status=data.get('new_status'))
    elif json_data['type'] == 'change_deadline':
        return task_manager.update_task_deadline_by_name(task_name=data.get('task_title', '').lower(), user_name=user_name,
                                                         new_deadline=data.get('deadline'))
    elif json_data['type'] == 'all_tasks':
        return task_manager.show_tasks_by_user_name(user_name=user_name)
    elif json_data['type'] == 'ask_giga':
        return "Нет такого"
    elif json_data['type'] == 'create_meeting':
        name = data.get('meeting_name')
        return get_meet(name)  #


