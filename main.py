import logging
import sqlite3
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- SOZLAMALAR ---
API_TOKEN = "8372553738:AAEYX1PYsvU8k1nvT0grTEFuSA9IGauc9mw"
ADMIN_ID = 1960796624  # O'z ID raqamingizni tekshiring

# 4 ta kanal username'ini kiriting
CHANNELS = ["@islomiykinolar77"]

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Ma'lumotlar bazasini sozlash
conn = sqlite3.connect("movies.db")
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS movies (code TEXT, file_id TEXT, name TEXT)")
cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)")
conn.commit()

async def check_subscription(user_id):
    """Foydalanuvchi barcha kanallarga a'zo ekanligini tekshiradi."""
    for channel in CHANNELS:
        try:
            member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status == 'left':
                return False
        except Exception:
            return False
    return True

@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    # Foydalanuvchini bazaga qo'shish (reklama yuborish uchun)
    try:
        cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (message.from_user.id,))
        conn.commit()
    except:
        pass

    if await check_subscription(message.from_user.id):
        await message.answer(f"Assalomu alaykum, {message.from_user.first_name}!\nKino kodini yuboring.")
    else:
        markup = InlineKeyboardMarkup(row_width=1)
        for i, channel in enumerate(CHANNELS, 1):
            markup.add(InlineKeyboardButton(text=f"{i}-kanalga obuna bo'lish", url=f"https://t.me/{channel[1:]}"))
        markup.add(InlineKeyboardButton(text="Tekshirish ✅", callback_data="check"))
        await message.answer("Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling:", reply_markup=markup)

@dp.callback_query_handler(text="check")
async def check_callback(call: types.CallbackQuery):
    if await check_subscription(call.from_user.id):
        await call.message.delete()
        await call.message.answer("Rahmat! Endi kino kodini yuborishingiz mumkin.")
    else:
        await call.answer("Hali hamma kanallarga a'zo emassiz!", show_alert=True)

# --- ADMIN FUNKSIYALARI ---

@dp.message_handler(commands=['stat'])
async def statistics(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        await message.answer(f"Bot foydalanuvchilari soni: {count} ta")

@dp.message_handler(commands=['reklama'])
async def broadcast(message: types.Message):
    """Admin reklama yuborishi uchun: /reklama [xabar]"""
    if message.from_user.id == ADMIN_ID:
        text = message.get_args()
        if not text:
            return await message.answer("Xabarni yozing. Misol: /reklama Salom barchaga!")
        
        cursor.execute("SELECT user_id FROM users")
        users = cursor.fetchall()
        
        count = 0
        for user in users:
            try:
                await bot.send_message(user[0], text)
                count += 1
            except:
                continue
        await message.answer(f"Reklama {count} ta foydalanuvchiga yuborildi.")

@dp.message_handler(lambda message: message.text.startswith('+'))
async def add_movie(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        try:
            data = message.text[1:].split('|')
            code, file_id, name = data[0], data[1], data[2]
            cursor.execute("INSERT INTO movies VALUES (?, ?, ?)", (code, file_id, name))
            conn.commit()
            await message.answer(f"Kino qo'shildi: {name}")
        except:
            await message.answer("Xato! Format: +kod|file_id|nomi")

@dp.message_handler()
async def get_movie(message: types.Message):
    if not await check_subscription(message.from_user.id):
        return await start_command(message)
    
    code = message.text
    cursor.execute("SELECT file_id, name FROM movies WHERE code=?", (code,))
    movie = cursor.fetchone()
    
    if movie:
        await bot.send_video(message.chat.id, movie[0], caption=f"🎬 {movie[1]}")
    else:
        await message.answer("Kino topilmadi. Kodni to'g'ri yozganingizni tekshiring.")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
