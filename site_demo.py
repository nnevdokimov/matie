import flask

from TaskManager import ChatTaskManagerDB
from giga import find_answer, check_type
import json

app = flask.Flask(__name__)


@app.before_request
def before_request():
    flask.g.task_manager = ChatTaskManagerDB('chat_task_manager.db')


@app.teardown_request
def teardown_request(exception):
    db_conn = flask.g.pop('db_conn', None)
    if db_conn is not None:
        db_conn.close()


@app.route('/')
def index():
    return flask.render_template('index.html')


@app.route('/send_message', methods=['POST'])
def send_message():
    data = json.loads(flask.request.data)
    user_message = data['message']

    # Сейчас обработчик имеет такой вид, так как мы используем sqllite и там нет многопоточости для telegram
    user = "percyve11e"
    user_id = 1
    answer = check_type(user_message, user_name=user, user_id=user_id)

    return flask.jsonify({'answer': answer})


if __name__ == '__main__':
    app.run(debug=True)
