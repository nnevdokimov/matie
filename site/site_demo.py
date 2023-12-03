import flask

from giga import find_answer, check_type
import json

app = flask.Flask(__name__)


@app.route('/')
def index():
    return flask.render_template('site/index.html')


@app.route('/send_message', methods=['POST'])
def send_message():
    data = json.loads(flask.request.data)
    user_message = data['message']

    # Обработка сообщения пользователя вашим ботом
    # Предполагается, что функция check_type возвращает ответ
    user = "web_user"  # Можете добавить механизм идентификации пользователя
    user_id = 1  # Пример идентификатора пользователя
    answer = check_type(user_message, user_name=user, user_id=user_id)

    return flask.jsonify({'answer': answer})


if __name__ == '__main__':
    app.run(debug=True)
