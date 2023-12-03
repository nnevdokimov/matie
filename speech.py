import asyncio
import base64
import uuid
from config import speech_oath
from aiohttp import ClientSession

SBER_API_TOKEN = speech_oath


async def gen_speech(text):
    global SBER_API_TOKEN
    url = "https://smartspeech.sber.ru/rest/v1/text:synthesize"

    headers = {
        "Authorization": f"Bearer {SBER_API_TOKEN}",
        "Content-Type": "application/text"
    }

    data = text.encode('utf-8')

    params = {
        "format": "wav16",
        "voice": "Nec_24000"
    }

    async with ClientSession() as session:
        async with session.post(url, headers=headers, params=params, data=data, ssl=False ) as response:
            if response.status == 200:
                audio_content = await response.read()
                return audio_content
            elif response.status == 401:
                SBER_API_TOKEN = await gen_oath()
                return await gen_speech(text)
            else:
                print("Failed to synthesize speech. Status code:", response.status)
                print("Response:", await response.text())
                return None


async def send_audio_to_sber(audio_file):
    global SBER_API_TOKEN
    url = "https://smartspeech.sber.ru/rest/v1/speech:recognize"

    headers = {
        "Authorization": f"Bearer {SBER_API_TOKEN}",
        "Content-Type": "audio/ogg; codecs=opus"
    }

    async with ClientSession() as session:
        async with session.post(url, headers=headers, data=audio_file, ssl=False) as response:
            if response.status == 200:
                return await response.json()
            elif response.status == 401:
                SBER_API_TOKEN = await gen_oath()
                return await send_audio_to_sber(audio_file)
            else:
                return f"Ошибка запроса. Статус-код: {response.status}, Ответ: {await response.text()}"


async def gen_oath():
    url = 'https://ngw.devices.sberbank.ru:9443/api/v2/oauth'

    headers = {
        'Authorization': 'Basic NTYyNDIwOWQtNTcxNC00YTk0LTkyZjItZDhmNTFhNGFiYzVkOjIyYjdhMjU4LTZmMzUtNGE2Ny04MjQ4LWRiY2YxN2YzNjU4NQ==',
        'RqUID': str(uuid.uuid4()),
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    data = {
        'scope': 'SALUTE_SPEECH_PERS'
    }

    async with ClientSession() as session:
        async with session.post(url, headers=headers, data=data, ssl=False) as response:
            if response.status == 200:
                json_response = await response.json()
                print("Успешный ответ:", json_response)
                return json_response['access_token']
            else:
                print("Ошибка запроса. Статус-код:", response.status)
                print("Ответ:", await response.text())
                return None


# asyncio.run(gen_oath())