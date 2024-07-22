import logging
import os
import asyncio
import aiohttp
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
import speech_recognition as sr
from pydub import AudioSegment
import soundfile as sf
from conf import TOKEN


# Настройка логирования
logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Путь для сохранения голосовых сообщений
VOICE_PATH = './voices'
os.makedirs(VOICE_PATH, exist_ok=True)

async def download_file(file_id, file_path):
    file = await bot.get_file(file_id)
    file_url = f'https://api.telegram.org/file/bot{TOKEN}/{file.file_path}'
    
    async with aiohttp.ClientSession() as session:
        async with session.get(file_url) as response:
            if response.status == 200:
                with open(file_path, 'wb') as f:
                    f.write(await response.read())

def conver_ogg_to_wav(ogg_path, wav_path):
    data, samplerate = sf.read(ogg_path)
    sf.write(wav_path, data, samplerate)

@dp.message(F.voice)
async def handle_voice_message(message: types.Message):
    voice = message.voice
    file_id = voice.file_id
    file_path = os.path.join(VOICE_PATH, f'{file_id}.ogg')
    wav_path = os.path.join(VOICE_PATH, f'{file_id}.wav')

    await download_file(file_id, file_path)

    try: 
        conver_ogg_to_wav(file_path, wav_path)

        recognizer = sr.Recognizer()
        audio_file = sr.AudioFile(wav_path)
        with audio_file as source:
            audio = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio, language='ru-RU')
            await message.reply(f'Транскрипция: {text}')
        except sr.UnknownValueError:
            await message.reply('Не удалось распознать речь.')
        except sr.RequestError as e:
            await message.reply(f'Ошибка сервиса распознавания речи: {e}')
    except Exception as e:
        await message.reply(f'Произошла ошибка при обработке файла: {e}')
        logging.error(f'Error processing voice message: {e}')
    finally:
        os.remove(file_path)
        os.remove(wav_path)


@dp.message(Command('start'))
async def send_welcome(message: types.Message):
    await message.reply("Привет! Отправь мне голосовое сообщение, и я сделаю его транскрипцию.")

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
