from giga import find_answer, check_type
from aiogram import Bot, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import Dispatcher, FSMContext
from speech import send_audio_to_sber, gen_speech
from config import TG_API

# Инициализация бота с токеном Telegram
telegram_token = TG_API
bot = Bot(token=telegram_token)

# Инициализация хранилища состояний и диспетчера
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Обработчик текстовых сообщений
@dp.message_handler(content_types=[types.ContentType.TEXT])
async def message_handle(message: types.Message):
    # Получение имени пользователя и его ID из сообщения
    user = message.from_user.username
    user_id = message.from_user.id
    # Обработка текста сообщения и получение ответа
    answer = check_type(message.text, user_name=user, user_id=user_id)
    # Отправка ответа пользователю
    await message.reply(answer)

# Обработчик голосовых сообщений
@dp.message_handler(content_types=types.ContentType.VOICE)
async def handle_voice(message: types.Message):
    # Получение информации о голосовом сообщении
    file_info = await bot.get_file(message.voice.file_id)
    file_path = file_info.file_path

    # Скачивание голосового сообщения
    audio_file = await bot.download_file(file_path)

    # Отправка аудиофайла на сервер и получение результата расшифровки
    result = await send_audio_to_sber(audio_file)
    print(f'Расшифровка: {result}')

    # Извлечение текста из результата
    text = result['result'][0]
    # Обработка текста и получение ответа
    user = message.from_user.username
    user_id = message.from_user.id
    answer = check_type(text, user_name=user, user_id=user_id)

    # Проверка, является ли ответ ссылкой, и отправка ответа
    if answer.startswith('https://jazz.sber.ru'):
        await message.reply(answer)
        return

    # Генерация голосового ответа
    audio_content = await gen_speech(answer)

    # Сохранение и отправка голосового сообщения
    if audio_content:
        with open("out.wav", "wb") as file:
            file.write(audio_content)

        with open("out.wav", "rb") as audio:
            await message.reply_voice(audio)

# Запуск бота
if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp)
