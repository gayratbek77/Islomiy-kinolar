import asyncio
import sqlite3
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- SOZLAMALAR ---
API_TOKEN = "8372553738:AAEYX1PYsvU8k1nvT0grTEFuSA9IGauc9mw"
ADMIN_ID = 1960796624
CHANNEL_ID = "@islomiykinolar77"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- BAZA BILAN ISHLASH ---
def init_db():
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)")
    cursor.execute("CREATE TABLE IF NOT EXISTS movies (code TEXT, file_id TEXT, name TEXT)")
    conn.commit()
    conn.close()

init_db()

# --- OBUNANI TEKSHIRISH ---
async def is_subscribed(user_id):
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

# --- COMMANDS ---
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (message.from_user.id,))
    conn.commit()
    conn.close()

    if await is_subscribed(message.from_user.id):
        await message.answer("<b>Assalomu alaykum!</b>\nKino kodini yuboring:")
    else:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Kanalga obuna bo'lish", url=f"https://t.me/{CHANNEL_ID[1:]}")],
            [InlineKeyboardButton(text="Tekshirish ✅", callback_data="check")]
        ])
        await message.answer("Botdan foydalanish uchun kanalimizga obuna bo'ling:", reply_markup=kb)

@dp.callback_query(F.data == "check")
async def check_cb(call: types.CallbackQuery):
    if await is_subscribed(call.from_user.id):
        await call.message.delete()
        await call.message.answer("Rahmat! Endi kino kodini yuborishingiz mumkin.")
    else:
        await call.answer("Avval kanalga obuna bo'ling!", show_alert=True)

@dp.message(Command("stat"))
async def stat_cmd(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        conn = sqlite3.connect("bot_data.db")
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        conn.close()
        await message.answer(f"📊 <b>Bot a'zolari:</b> {count} ta")

@dp.message(Command("reklama"))
async def reklama_cmd(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer("Reklama xabarini yuboring (rasm, video yoki matn).")

@dp.message(lambda m: m.text and m.text.startswith('+'))
async def add_movie(message: types.Message):
    if message.from_user.id == ADMIN_ID:
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

@dp.message()
async def search_movie(message: types.Message):
    if not await is_subscribed(message.from_user.id):
        return await start_cmd(message)
    
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT file_id, name FROM movies WHERE code=?", (message.text,))
    res = cursor.fetchone()
    conn.close()

    if res:
        await bot.send_video(message.chat.id, res[0], caption=f"🎬 {res[1]}")
    else:
        await message.answer("Kino topilmadi ❌")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
