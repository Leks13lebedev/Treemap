import asyncio
from aiogram import Bot, Dispatcher
from handler.user import user_rt
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from services.session import init_session
from services.broadcast import send_morning_stats, send_evening_stats

# КОНФИГУРАЦИЯ
TOKEN = '7814730509:AAEwhlZVbO2mK9xYN_JRSIq5qDKUpD-6yxw'
TIMEZONE = 'Europe/Moscow'

# ИНИЦИАЛИЗАЦИЯ
bot = Bot(token=TOKEN)
dp = Dispatcher()
dp.include_routers(user_rt)

scheduler = AsyncIOScheduler(timezone=TIMEZONE)

async def on_startup():
    """Запуск планировщика при старте бота"""
    # Утренняя рассылка: каждый день в 09:20:15
    scheduler.add_job(
        send_morning_stats,
        CronTrigger(hour=9, minute=20, second=15),
        args=[bot],
        id='morning_stats',
        replace_existing=True
    )
    
    # Вечерняя рассылка: каждый день в 18:50:15
    scheduler.add_job(
        send_evening_stats,
        CronTrigger(hour=18, minute=50, second=15),
        args=[bot],
        id='evening_stats',
        replace_existing=True
    )
    
    scheduler.start()
    print("Планировщик запущен. Рассылки: 09:20:15 и 18:50:15 MSK")

async def main():
    init_session()
    await on_startup()
    await bot.delete_webhook()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())