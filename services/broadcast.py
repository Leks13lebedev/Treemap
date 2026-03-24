import json
import os
from functions.heatmap import get_heatmap
from functions.leaders import get_leaders
from functions.funding import get_funding
from functions.positions import get_positions
from functions.oi_change import get_oi_change

SUB_FILE = 'subscribers.json'

def get_subs():
    if os.path.exists(SUB_FILE):
        try:
            with open(SUB_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Ошибка чтения subscribers.json: {e}")
            return []
    return []

async def send_morning_stats(bot):
    chat_ids = get_subs()
    if not chat_ids:
        print("Нет подписчиков для утренней рассылки")
        return

    print(f"Начало утренней рассылки для {len(chat_ids)} пользователей...")
    
    try:
        await get_heatmap(chat_ids, bot)
        await get_leaders(chat_ids, bot)
        print("Утренняя рассылка завершена успешно")
    except Exception as e:
        print(f"Критическая ошибка утренней рассылки: {e}")

async def send_evening_stats(bot):
    chat_ids = get_subs()
    if not chat_ids:
        print("Нет подписчиков для вечерней рассылки")
        return

    print(f"Начало вечерней рассылки для {len(chat_ids)} пользователей...")
    
    try:
        await get_heatmap(chat_ids, bot)
        await get_funding(chat_ids, bot)
        await get_leaders(chat_ids, bot)
        await get_positions(chat_ids, bot)
        await get_oi_change(chat_ids, bot)
        print("Вечерняя рассылка завершена успешно")
    except Exception as e:
        print(f"Критическая ошибка вечерней рассылки: {e}")
