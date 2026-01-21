import logging
import sqlite3
from aiogram import Bot, Dispatcher, types, executor

# --- SOZLAMALAR ---
API_TOKEN = "8372553738:AAEYX1PYsvU8k1nvT0grTEFuSA9IGauc9mw"
ADMIN_ID = 1960796624  # Sizning ID raqamingiz
CHANNEL_ID = "@islomiykinolar77" # Majburiy obuna kanali

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot)

# Ma'lumotlar bazasini yaratish (Foydalanuvchilar va Kinolar uchun)
def init_db():
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)")
    cursor.execute("CREATE TABLE IF NOT EXISTS movies (code TEXT, file_id TEXT, name TEXT)")
    conn.commit()
    conn.close()

init_db()

# Kanalga obunani tekshirish funksiyasi
async def is_subscribed(user_id):
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status != "left"
    except:
        return False

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    # Foydalanuvchini bazaga qo'shish (reklama uchun)
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (message.from_user.id,))
    conn.commit()
    conn.close()

    if await is_subscribed(message.from_user.id):
        await message.answer(f"Assalomu alaykum {message.from_user.full_name}!\nKino kodini yuboring:")
    else:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Obuna bo'lish", url=f"https://t.me/{CHANNEL_ID[1:]}"))
        markup.add(types.InlineKeyboardButton("Tekshirish ✅", callback_data="check"))
        await message.answer(f"Botdan foydalanish uchun kanalimizga obuna bo'ling:", reply_markup=markup)

@dp.callback_query_handler(text="check")
async def check_sub(call: types.CallbackQuery):
    if await is_subscribed(call.from_user.id):
        await call.message.delete()
        await call.message.answer("Rahmat! Endi kino kodini yuborishingiz mumkin.")
    else:
        await call.answer("Avval kanalga obuna bo'ling!", show_alert=True)

# --- ADMIN PANEL ---

@dp.message_handler(commands=['stat'], user_id=ADMIN_ID)
async def stats(message: types.Message):
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    conn.close()
    await message.answer(f"📊 <b>Bot a'zolari soni:</b> {count} ta")

@dp.message_handler(commands=['reklama'], user_id=ADMIN_ID)
async def reklama_start(message: types.Message):
    await message.answer("Reklama xabarini yuboring (rasm, video yoki matn). Bekor qilish uchun 'stop' deb yozing.")
    dp.register_message_handler(send_reklama, user_id=ADMIN_ID, content_types=types.ContentTypes.ANY)

async def send_reklama(message: types.Message):
    if message.text == 'stop':
        await message.answer("Reklama bekor qilindi.")
        return
    
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    users = cursor.fetchall()
    conn.close()

    count = 0
    for user in users:
        try:
            await message.copy_to(user[0])
            count += 1
        except:
            pass
    await message.answer(f"✅ Reklama {count} kishiga yuborildi.")

# --- KINO QO'SHISH VA QIDIRISH ---

@dp.message_handler(lambda m: m.text.startswith('+'), user_id=ADMIN_ID)
async def add_kino(message: types.Message):
    try:
        parts = message.text[1:].split('|')
        code, f_id, name = parts[0], parts[1], parts[2]
        conn = sqlite3.connect("bot_data.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO movies VALUES (?, ?, ?)", (code, f_id, name))
        conn.commit()
        conn.close()
        await message.answer(f"✅ Kino qo'shildi: {name}")
    except:
        await message.answer("Xato! Format: +kod|file_id|nomi")

@dp.message_handler()
async def get_kino(message: types.Message):
    if not await is_subscribed(message.from_user.id):
        return await start(message)

    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT file_id, name FROM movies WHERE code=?", (message.text,))
    res = cursor.fetchone()
    conn.close()

    if res:
        await bot.send_video(message.chat.id, res[0], caption=f"🎬 {res[1]}")
    else:
        await message.answer("Kino topilmadi ❌")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
