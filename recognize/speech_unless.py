import grpc
import pyaudio
import itertools

import recognize.recognition_pb2 as recognition_pb2
import recognize.recognition_pb2_grpc as recognition_pb2_grpc
from config import speech_oath

def generate_audio_chunks_from_microphone(stream, chunk_size):
    """Генерация аудио-чанков из потока микрофона."""
    while True:
        data = stream.read(chunk_size, exception_on_overflow=False)
        yield recognition_pb2.RecognitionRequest(audio_chunk=data)


def start_streaming_recognition(host='smartspeech.sber.ru',
                                token=speech_oath,
                                ca_certificate='recognize/russian-trusted-cacert.pem',
                                metadata=['key1', 'value1', 'key2', 'value2']):
    # Параметры аудио потока
    CHUNK_SIZE = 2048
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000

    # Настройка PyAudio
    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK_SIZE)

    # Настройка gRPC соединения
    ssl_cred = grpc.ssl_channel_credentials(
        root_certificates=open(ca_certificate, 'rb').read() if ca_certificate else None,
    )
    token_cred = grpc.access_token_call_credentials(token)

    channel = grpc.secure_channel(
        host,
        grpc.composite_channel_credentials(ssl_cred, token_cred)
    )

    stub = recognition_pb2_grpc.SmartSpeechStub(channel)

    # Создание словаря для speaker_separation_options
    speaker_separation_options_dict = {
        'enable': False,
        'enable_only_main_speaker': False,
        'count': 2
    }

    # Создание словаря для recognition_options
    recognition_options_dict = {
        'audio_encoding': recognition_pb2.RecognitionOptions.PCM_S16LE,
        'sample_rate': 16000,
        'language': 'ru-RU'
    }

    # Инициализация RecognitionOptions с использованием словаря
    recognition_options = recognition_pb2.RecognitionOptions(**recognition_options_dict)

    # Преобразование метаданных
    metadata_pairs = [(metadata[i], metadata[i + 1]) for i in range(0, len(metadata), 2)] if metadata else []

    # Создание запроса распознавания
    con = stub.Recognize(itertools.chain(
        [recognition_pb2.RecognitionRequest(options=recognition_options)],
        generate_audio_chunks_from_microphone(stream, CHUNK_SIZE),
    ), metadata=metadata_pairs)

    # Обработка ответов
    try:
        for resp in con:
            if not resp.eou:
                res = resp.text
                print('Got partial result:', resp.text)
            else:
                res = ''
                # Доступ к результатам внутри resp как к атрибутам объекта
                for result in resp.results:
                    res += result.text
                    print('Got end-of-utterance result:', result.text)  # Используйте result.text для доступа к тексту

    except grpc.RpcError as err:
        res = None
        print('RPC error: code = {}, details = {}'.format(err.code(), err.details()))
    finally:
        try:
            stream.stop_stream()
        except Exception as e:
            print(f"Ошибка при остановке потока: {e}")

        try:
            stream.close()
        except Exception as e:
            print(f"Ошибка при закрытии потока: {e}")

        try:
            audio.terminate()
        except Exception as e:
            print(f"Ошибка при завершении аудио: {e}")

        try:
            channel.close()
        except Exception as e:
            print(f"Ошибка при закрытии канала: {e}")

        return res

