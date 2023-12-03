import subprocess

import pyaudio
import wave
import numpy as np
import tempfile
import os
import asyncio
from recognize.speech_unless import start_streaming_recognition

from speech import send_audio_to_sber, gen_speech
from giga import check_type


async def process_audio(data, fs):
    try:
        # Создание временного WAV файла
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as wav_file:
            wav_filename = wav_file.name
            with wave.open(wav_file, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(fs)
                wf.writeframes(data)

        # Конвертирование WAV в OGG с использованием ffmpeg
        ogg_filename = wav_filename.replace(".wav", ".ogg")
        subprocess.run(['ffmpeg', '-i', wav_filename, '-c:a', 'libopus', ogg_filename], check=True)

        # Чтение OGG файла
        with open(ogg_filename, 'rb') as ogg_file:
            ogg_data = ogg_file.read()

        # Асинхронная отправка OGG файла
        result = await send_audio_to_sber(ogg_data)
        print("Transcription Result:", result)

        # Удаление временных файлов
        os.remove(wav_filename)
        os.remove(ogg_filename)

        return result['result'][0]
    except Exception as e:
        print("Error in process_audio:", e)
        return ""


async def record_and_process(fs, duration):
    p = pyaudio.PyAudio()

    stream = p.open(format=pyaudio.paInt16,
                    channels=1,
                    rate=fs,
                    input=True,
                    frames_per_buffer=1024)

    print("Recording...")
    frames = []

    for _ in range(0, int(fs / 1024 * duration)):
        try:
            data = stream.read(1024, exception_on_overflow=False)
            frames.append(np.frombuffer(data, dtype=np.int16))
        except IOError as e:
            print(f"IOError: {e}")

    # print("Finished recording.")

    stream.stop_stream()
    stream.close()
    p.terminate()

    audio_data = np.concatenate(frames)
    return await process_audio(audio_data, fs)


def play_sound(path):
    chunk_size = 1024

    wf = wave.open(path, 'rb')
    p = pyaudio.PyAudio()

    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True)

    data = wf.readframes(chunk_size)
    while data:
        stream.write(data)
        data = wf.readframes(chunk_size)

    stream.stop_stream()
    stream.close()
    p.terminate()


def play_raw_audio(audio_data, sample_width=1, channels=1, sample_rate=44100):
    chunk_size = 1024

    # Создаем объект PyAudio
    p = pyaudio.PyAudio()

    # Открываем аудио-стрим
    stream = p.open(format=p.get_format_from_width(sample_width),
                    channels=channels,
                    rate=sample_rate,
                    output=True)

    # Чтение и воспроизведение данных
    while audio_data:
        chunk = audio_data[:chunk_size]
        audio_data = audio_data[chunk_size:]
        stream.write(chunk)

    # Закрываем поток и PyAudio
    stream.stop_stream()
    stream.close()
    p.terminate()


async def main_loop():
    fs = 16000  # Sample rate
    duration = 3  # Duration of each recording segment in seconds

    while True:
        text = await record_and_process(fs, duration)
        print(text)
        if "мать" in text.lower():
            print("Trigger word detected.")
            play_sound("beep.wav")

            question = start_streaming_recognition()
            while question == '':
                question = start_streaming_recognition()
            res = check_type(question, "test", 0)
            audio_content = await gen_speech(res)

            with open("out.wav", "wb") as file:
                file.write(audio_content)

            play_sound("out.wav")
            os.remove("out.wav")
            break


asyncio.run(main_loop())
