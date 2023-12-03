from giga import find_answer, check_type
from aiogram import Bot, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import Dispatcher, FSMContext
from speech import send_audio_to_sber, gen_speech

telegram_token = "6895244936:AAHVMhra1R7qNitXmbaYMK3C-_Jo9Zer-PI"
bot = Bot(token=telegram_token)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

messages = {}


@dp.message_handler(content_types=[types.ContentType.TEXT])
async def message_handle(message: types.Message):
    user = message.from_user.username
    user_id = message.from_user.id
    answer = check_type(message.text, user_name=user, user_id=user_id)
    await message.reply(answer)


@dp.message_handler(content_types=types.ContentType.VOICE)
async def handle_voice(message: types.Message):
    file_info = await bot.get_file(message.voice.file_id)
    file_path = file_info.file_path

    audio_file = await bot.download_file(file_path)

    result = await send_audio_to_sber(audio_file)
    print(f'Расшифровка: {result}')

    text = result['result'][0]
    user = message.from_user.username
    user_id = message.from_user.id
    answer = check_type(text, user_name=user, user_id=user_id)

    if answer.startswith('https://jazz.sber.ru'):
        await message.reply(answer)
        return

    audio_content = await gen_speech(answer)

    if audio_content:
        with open("out.wav", "wb") as file:
            file.write(audio_content)

        with open("out.wav", "rb") as audio:
            await message.reply_voice(audio)


if __name__ == '__main__':
    from aiogram import executor

    executor.start_polling(dp)
