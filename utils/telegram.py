from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import asyncio
import logging

async def snd(tkn: str, cid: str, jbs: list[dict]):
    bot = Bot(tkn)
    for j in jbs:
        msg = f"💼 *{j['t']}*\n🏢 {j['c']}\n🔗 [Ver oferta]({j['l']})\n📅 {j['ts']}"
        try:
            await bot.send_message(chat_id=cid, text=msg, parse_mode="Markdown", disable_web_page_preview=True)
            await asyncio.sleep(0.05)  # Optimizado para <1s
        except Exception as e:
            logging.error(f"Error enviando a Telegram: {e}")

async def get_chat_id(tkn: str):
    async def start(update: Update, _):
        cid = update.message.chat_id
        await update.message.reply_text(f"Tu chat_id es: `{cid}`\nAñádelo a `config.json` como `tg_chat`.", parse_mode="Markdown")
    
    app = Application.builder().token(tkn).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, start))
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    print("Bot iniciado. Envía /start al bot para obtener tu chat_id.")
    await asyncio.sleep(30)
    await app.updater.stop()
    await app.stop()
