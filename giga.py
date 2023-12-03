import json

from langchain.schema import HumanMessage, SystemMessage, AIMessage
from langchain.chat_models.gigachat import GigaChat
from TaskManager import task_manager_stat

chat = GigaChat(
    credentials='OWRiODI1OGQtYTc0NC00Y2U2LWJhZWItMGMxYjlkZWVjMmY3OjA1NTEwNTdkLWQxMjUtNDljMS04YWYwLTU1ZTIyZTliN2Y2Yw==',
    verify_ssl_certs=False, scope='GIGACHAT_API_PERS')

system_message = 'Ты полезный AI помощник, который выполняет задачи чисто по указаниям'
user_message = """
    Я - ваш помощник в Giga Chat. Пожалуйста, выберите одну из следующих категорий и предоставьте детали вашего запроса:
    1. "create_task": для создания новой задачи либо напоминания что-то сделать {task_title}.
    2. "change_status": для изменения статуса задачи {task_title} на {new_status}.
    3. "change_deadline": для изменения дедлайна задачи {task_title} на {deadline}.
    4. "all_tasks": для вывода списка всех задач.
    5. "ask_giga": для прямых вопросов ко мне.
    6. "create_meeting": для создания созвона или встречи {meeting_name}.

    Ожидаемый ответ:
    {
        "response_type": "classification" or "answer",
        "content": {
            "type": "create_task" or "change_status" or "change_deadline" or "all_tasks" or "create_meeting" or "unknown",
            "details": {
                "task_title": "{task_title}" при наличии,
                "deadline": "{deadline}" если его нет в сообщении человека - то просто пропуск,
                "new_status": "{new_status}" при наличии,
                "all_tasks": {all_tasks_boolean} при наличии,
                "meeting_name": "{meeting_name}" при наличии
            }
        }
    }
    НИ В КОЕМ СЛУЧАЕ НЕ УКАЗЫВАЙ ДАННЫЕ, ЕСЛИ ИХ НЕТ В СООБЩЕНИИ, ЭТО МОЖЕТ НАВРЕДИТЬ ЖИЗНИ ЧЕЛОВЕКА!
"""
bot_answer = 'Я готова помочь вам с созданием задачи. Пожалуйста, отправьте интересующий вас запрос и я классифицирую его.'


def find_answer(messages):
    return chat(messages)


def check_type(message, user_name, user_id):
    messages = [SystemMessage(content=system_message), HumanMessage(content=user_message), AIMessage(content=bot_answer), HumanMessage(content=message)]
    print(messages)
    answer = chat(messages).content
    print(answer)

    try:
        json_object = json.loads(answer)
        print(json_object)
        return task_manager_stat(json_object['content'], user_name=user_name, user_id=user_id)
    except Exception as e:
        print( f"Ошибка обработки: {e}")
        return answer
