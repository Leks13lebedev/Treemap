from services.session import get_session
import treemap_1  # Импортируем сам модуль
import datetime
import os
from aiogram import types

async def get_heatmap(chat_id: list, bot):
    if isinstance(chat_id, int):
        chat_id = [chat_id]
    else:
        chat_id = chat_id
    session = get_session()
    
    current_hour = datetime.datetime.now().hour
    h = '09:20' if current_hour < 12 else '18:50'
    stroca = datetime.datetime.now().strftime("%d.%m.%Y") + ' ' + h
    
    # Вызываем функцию map из treemap_1, передавая session
    await treemap_1.map(stroca, session)
    
    photo = types.FSInputFile("1.png")
    now = (datetime.datetime.utcnow() + datetime.timedelta(hours=3)).strftime("%H:%M:%S")
    caption = f"<b>📈 КАРТА СРОЧНОГО РЫНКА 📉</b>\n\nВремя: <code>{now}</code> МСК\n\n#heatmap"
    
    for cid in chat_id:
        try:
            await bot.send_photo(chat_id=cid, caption=caption, photo=photo, parse_mode="HTML")
        except Exception as e:
            print(f"Ошибка отправки {cid}: {e}")
    
    if os.path.exists('1.png'):
        os.remove('1.png')