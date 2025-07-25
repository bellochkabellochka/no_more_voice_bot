import os
os.environ["PATH"] += os.pathsep + os.path.expanduser("~/bin")
import asyncio
from aiogram import Bot, Dispatcher, types, Router, F
from aiogram.types import ContentType
from aiogram.types.input_file import FSInputFile
from dotenv import load_dotenv
import whisper
from pydub import AudioSegment
import ffmpeg
from mistralai import Mistral
import re
import json

load_dotenv()
TOKEN = os.getenv('TELEGRAM_TOKEN')
MISTRAL_API_KEY = os.getenv('MISTRAL_API_KEY')

bot = Bot(token=TOKEN)
dp = Dispatcher()
router = Router()

SAVE_DIR = 'downloads'
os.makedirs(SAVE_DIR, exist_ok=True)

whisper_model = whisper.load_model('medium')

# Mistral client
mistral_client = Mistral(MISTRAL_API_KEY)

MISTRAL_INSTRUCTIONS = '''Ты — бот в групповом чате, саркастический мем-редактор. Тебе на вход присылают транскрибацию голосового сообщения.
Твоя задача: из присланного текста выжать главную мысль и превратить её в короткий абсурдный тезис (до 45 знаков), которые звучали бы как лозунг, демотиватор или просто какой-то абсурдный вброс. А также выбрать наиболее подходящий шаблон мема. 
Необходимо вернуть строго json без лишних пробелов/переносов:
{"text":"основной_посыл (саркастичный_панчлайн)","template":"файл_шаблона.png"}
Сохраняй повествование от первого лица, если в транскрибации человек говорит от первого лица. 
Ты можешь дополнять эту мысль мемным контекстом, но при этом сохранять основной посыл сообщения.
Делай упор на иронию, гиперболу, пафос.
Тональность - саркастичная. 
Используй современный сленг, можно использовать ругательства, эмодзи не ставь. 
никаких пояснений, только json.
 пиши с маленькой буквы, не ставь точку в конце предложения. сначала основной посыл сообщения, а потом в скобочках смешной/саркастичный панчлайн/подкол
можешь ставить смайлики ( или ) в любом количестве в зависимости от тональности сообщения (как смайлики)
template выбирается по смыслу из списка: 
fighting_club.png — работа/офис 
giga_brain.png — гениальное открытие 
opengamer.png — крутость/пофиг 
thisisfine.png — всё плохо, но норм (провал/фиаско/все пошло не по плану)
umnik.png — человек умничает, душнит
wolf.png — философия или тупые/очевидные умозаключения
sad_cat.png — грусть / разочарование / одиночество 
witch_cat.png — отвращение 
angry.png — гнев / злость / раздражение 
stonks.png — деньги/выгода/богатство/криптовалюта
 just_a_girl.png — прошу/умоляю/просьба
gosling.png — пофигизм 
tinkoff.png — сомнения
short_message.png — если текст ≤1 слова или непонятен (тогда text оставляешь пустым: "") 
statham_mem_2.png / statham_meme_3.png/ statham_mem.png - если не подошел ни один шаблон, выбирай случайным образом любой из них'''

async def get_meme_thesis(text):
    inputs = [
        {"role": "user", "content": text}
    ]
    completion_args = {
        "temperature": 0.7,
        "max_tokens": 2048,
        "top_p": 1
    }
    tools = []
    try:
        response = mistral_client.beta.conversations.start(
            inputs=inputs,
            model="mistral-medium-latest",
            instructions=MISTRAL_INSTRUCTIONS,
            completion_args=completion_args,
            tools=tools,
        )
        print("Mistral response:", response)
        print("Response dict:", response.__dict__)
        # Попытка получить мем-тезис из разных мест
        if hasattr(response, 'outputs') and len(response.outputs) > 0 and hasattr(response.outputs[0], 'content'):
            return response.outputs[0].content
        elif hasattr(response, 'choices') and len(response.choices) > 0 and hasattr(response.choices[0].message, 'content'):
            return response.choices[0].message.content
        else:
            return f"Не удалось найти мем-тезис в ответе: {response}"
    except Exception as e:
        return f"Ошибка генерации мема: {str(e)}"

# Заготовка для генерации картинки-мема
from PIL import Image, ImageDraw, ImageFont
import textwrap

def remove_laughter(text):
    # Удаляет слова, содержащие подряд 3+ символа из набора смеха
    return re.sub(r'\b[ахехaxeh]{3,}\b', '', text, flags=re.IGNORECASE)

def extract_meme_text(meme_thesis):
    # Если это dict с text, вернуть text
    if isinstance(meme_thesis, dict) and 'text' in meme_thesis:
        return meme_thesis['text']
    # Если это строка, которая выглядит как JSON
    if isinstance(meme_thesis, str) and meme_thesis.strip().startswith('{'):
        try:
            data = json.loads(meme_thesis)
            if 'text' in data:
                return data['text']
        except Exception:
            pass
    return meme_thesis

def generate_meme_image(text, template_path='statham_meme.jpg', output_path='meme_result.jpg'):
    image = Image.open(template_path).convert('RGB')
    draw = ImageDraw.Draw(image)
    w, h = image.size
    # Автоматический подбор размера шрифта
    font_path = "DejaVuSans.ttf"
    max_font_size = 48
    min_font_size = 16
    font_size = max_font_size
    wrapped_text = text
    while font_size >= min_font_size:
        font = ImageFont.truetype(font_path, size=font_size)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        if text_w <= w - 40:
            break
        font_size -= 2
    else:
        # Если даже минимальный шрифт не влезает, переносим текст на строки
        font = ImageFont.truetype(font_path, size=min_font_size)
        # Примерно подбираем ширину строки
        max_chars_per_line = max(1, int(len(text) * (w - 40) / (text_w + 1)))
        wrapped_text = '\n'.join(textwrap.wrap(text, width=max_chars_per_line))
    # Пересчитываем размеры для финального текста
    bbox = draw.textbbox((0, 0), wrapped_text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    x = (w - text_w) // 2
    y = h - text_h - 40
    # Рисуем текст с обводкой
    outline_color = 'black'
    for dx in [-2, 2]:
        for dy in [-2, 2]:
            draw.text((x+dx, y+dy), wrapped_text, font=font, fill=outline_color, align='center')
    draw.text((x, y), wrapped_text, font=font, fill='white', align='center')
    image.save(output_path)
    return output_path

def select_meme_template(meme_thesis, recognized_text):
    text = (meme_thesis or '').lower() + ' ' + (recognized_text or '').lower()
    # Особый случай: короткое или нераспознанное сообщение
    if len(recognized_text.split()) == 1 or len(recognized_text.strip()) < 5:
        return 'short_message.png', False
    # Приоритет: просьба/жалоба
    if any(kw in text for kw in ['не хочу', 'помоги', 'прошу', 'пожалуйста', 'устал', 'не могу', 'дай', 'дайте', 'надоело', 'спасите', 'help', 'save me']):
        return 'just_a_girl.png', True
    if any(kw in text for kw in ['работ', 'работа', 'работать', 'работаю', 'работаем', 'работает', 'работают', 'офис', 'коллег', 'совещан', 'босс', 'начальник']):
        return 'fighting_club.png', True
    if any(kw in text for kw in ['гениальн', 'умозаключен', 'открытие', 'инсайт', 'прозрение', 'гениально', 'гениальный']):
        return 'giga_brain.png', True
    if any(kw in text for kw in ['круто', 'крут', 'пофиг', 'изи', 'изи катка', 'изи-бризи', 'расслаб', 'пофигизм', 'без разницы', 'все равно', 'всё равно']):
        return 'opengamer.png', True
    if any(kw in text for kw in ['не по плану', 'развал', 'катастроф', 'провал', 'fail', 'все плохо', 'всё плохо', 'горит', 'this is fine']):
        return 'thisisfine.png', True
    if any(kw in text for kw in ['умник', 'умничаешь', 'умничаю', 'умничать', 'знаешь', 'знаю', 'знание', 'знания']):
        return 'umnik.png', True
    if any(kw in text for kw in ['философ', 'философт', 'смысл', 'бытие', 'жизнь', 'экзистенц', 'вселенн', 'судьба', 'смысл жизни']):
        return 'wolf.png', True
    if any(kw in text for kw in ['грусть', 'разочарован', 'разочарование', 'одиночество', 'печаль', 'тоска', 'грустно', 'плакать', 'слез', 'слёзы', 'депресс', 'уныние']):
        return 'sad_cat.png', True
    if any(kw in text for kw in ['отвращен', 'отвращение', 'фу', 'мерзко', 'противно', 'брр', 'ужас', 'witch']):
        return 'witch_cat.png', True
    if any(kw in text for kw in ['злость', 'гнев', 'раздраж', 'бесит', 'разозлил', 'разозлило', 'разозлила', 'разозлили', 'раздражает', 'раздражение', 'агресс', 'angry']):
        return 'angry.png', True
    if any(kw in text for kw in ['богат', 'богатство', 'деньги', 'миллион', 'миллиард', 'капитал', 'инвест', 'успех', 'финанс', 'stonks']):
        return 'stonks.png', True
    if any(kw in text for kw in ['девочка', 'помоги', 'помогите', 'прошу', 'пожалуйста', 'just a girl', 'girl']):
        return 'just_a_girl.png', True
    if any(kw in text for kw in ['пофиг', 'гослинг', 'безразлич', 'равнодуш', 'спокойно', 'спокойствие']):
        return 'gosling.png', True
    if any(kw in text for kw in ['сомневаюсь', 'сомнение', 'сомнения', 'сомневаешься', 'сомнительно', 'сомнительн', 'tinkoff']):
        return 'tinkoff.png', True
    # Стэйтем — дефолтный мем
    if any(kw in text for kw in ['стэйтем', 'стетхем', 'statham']):
        return 'statham_mem_2.png', True
    # Если ничего не подошло — дефолтный шаблон
    return 'statham_meme.jpg', True

@router.message(F.content_type == ContentType.VOICE)
async def handle_voice(message: types.Message):
    voice = message.voice
    file_info = await bot.get_file(voice.file_id)
    file_path = file_info.file_path
    file_name = f"voice_{message.from_user.id}_{voice.file_unique_id}.ogg"
    save_path = os.path.join(SAVE_DIR, file_name)
    await bot.download_file(file_path, save_path)
    audio = AudioSegment.from_file(save_path)
    wav_path = save_path.replace('.ogg', '.wav')
    audio.export(wav_path, format='wav')
    text = await asyncio.get_event_loop().run_in_executor(
        None, lambda: whisper_model.transcribe(wav_path, language='ru')
    )
    recognized_text = text['text']
    filtered_text = remove_laughter(recognized_text)
    meme_thesis = await get_meme_thesis(filtered_text)
    template, add_text = select_meme_template(meme_thesis, recognized_text)
    meme_text = extract_meme_text(meme_thesis)
    meme_img_path = generate_meme_image(meme_text if add_text else '', template_path=template)
    photo = FSInputFile(meme_img_path)
    await message.reply_photo(photo)

@router.message(F.content_type == ContentType.VIDEO_NOTE)
async def handle_video_note(message: types.Message):
    video_note = message.video_note
    file_info = await bot.get_file(video_note.file_id)
    file_path = file_info.file_path
    file_name = f"video_note_{message.from_user.id}_{video_note.file_unique_id}.mp4"
    save_path = os.path.join(SAVE_DIR, file_name)
    await bot.download_file(file_path, save_path)
    audio_path = save_path.replace('.mp4', '.wav')
    (
        ffmpeg
        .input(save_path)
        .output(audio_path, format='wav', acodec='pcm_s16le', ac=1, ar='16k')
        .overwrite_output()
        .run(quiet=True)
    )
    text = await asyncio.get_event_loop().run_in_executor(
        None, lambda: whisper_model.transcribe(audio_path, language='ru')
    )
    recognized_text = text['text']
    filtered_text = remove_laughter(recognized_text)
    meme_thesis = await get_meme_thesis(filtered_text)
    template, add_text = select_meme_template(meme_thesis, recognized_text)
    meme_text = extract_meme_text(meme_thesis)
    meme_img_path = generate_meme_image(meme_text if add_text else '', template_path=template)
    photo = FSInputFile(meme_img_path)
    await message.reply_photo(photo)

# Удаляю универсальный хендлер, чтобы бот реагировал только на VOICE и VIDEO_NOTE

async def main():
    print("Бот запущен и polling стартовал!")
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print("Ошибка при запуске:", e) 