import logging
import sqlite3
import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

# --- SOZLAMALAR ---
API_TOKEN = 8372553738:AAEYX1PYsvU8k1nvT0grTEFuSA9IGauc9mw 
ADMIN_ID = 1960796624
CHANNEL_ID = "@islomiykinolar77"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Ma'lumotlar bazasi
db = sqlite3.connect("kino.db")
cursor = db.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY)")
cursor.execute("CREATE TABLE IF NOT EXISTS movies (code TEXT PRIMARY KEY, file_id TEXT, title TEXT)")
db.commit()

async def check_sub(user_id):
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except: return True

@dp.message(Command("start"))
async def start(message: types.Message):
    cursor.execute("INSERT OR IGNORE INTO users VALUES (?)", (message.from_user.id,))
    db.commit()
    await message.answer(f"Assalomu alaykum! Kino kodini yuboring.")

@dp.message(Command("stat"), F.from_user.id == ADMIN_ID)
async def stats(message: types.Message):
    cursor.execute("SELECT COUNT(*) FROM users")
    res = cursor.fetchone()[0]
    await message.answer(f"Bot a'zolari: {res} ta")

@dp.message(F.text.isdigit())
async def get_movie(message: types.Message):
    if not await check_sub(message.from_user.id):
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="Kanalga a'zo bo'lish", url=f"https://t.me/{CHANNEL_ID[1:]}"))
        await message.answer("Obuna bo'ling!", reply_markup=builder.as_markup())
        return
    cursor.execute("SELECT file_id, title FROM movies WHERE code = ?", (message.text,))
    res = cursor.fetchone()
    if res: await bot.send_video(message.chat.id, video=res[0], caption=res[1])
    else: await message.answer("Topilmadi.")

@dp.message(F.from_user.id == ADMIN_ID, F.text.startswith("+"))
async def add(message: types.Message):
    d = message.text[1:].split("|")
    cursor.execute("INSERT INTO movies VALUES (?, ?, ?)", (d[0].strip(), d[1].strip(), d[2].strip()))
    db.commit()
    await message.answer("Qo'shildi!")

async def main():
    # Render'da bot o'chib qolmasligi uchun port ochish
    if os.environ.get('RENDER'):
        from aiohttp import web
        app = web.Application()
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', int(os.environ.get('PORT', 8080)))
        await site.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
