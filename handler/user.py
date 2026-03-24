from aiogram import Router, types, F
from aiogram.filters import CommandStart
from keyboards import inline
import json
import os
from functions.heatmap import get_heatmap
from functions.funding import get_funding
from functions.leaders import get_leaders
from functions.positions import get_positions
from functions.oi_change import get_oi_change

user_rt = Router()

SUB_FILE = 'subscribers.json'
FUNCTIONS = {
    'heatmap': 'Тепловая карта',
    'funding': 'Фандинг',
    'leaders': 'Лидеры роста/падения',
    'positions': 'Открытые позиции',
    'oi_change': 'Изменение OI',
}



def get_subs():
    if os.path.exists(SUB_FILE):
        with open(SUB_FILE, 'r') as f:
            return json.load(f)
    return []

def save_subs(subs):
    with open(SUB_FILE, 'w') as f:
        json.dump(subs, f)

@user_rt.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer(
        'Выберите нужную функцию:',
        reply_markup=inline.keyboard(
            btns={
                FUNCTIONS['heatmap']: 'heatmap',
                FUNCTIONS['funding']: 'funding',
                FUNCTIONS['leaders']: 'leaders',
                FUNCTIONS['positions']: 'positions',
                FUNCTIONS['oi_change']: 'oi_change',
                'Подписаться': 'subscribe',
                'Отписаться': 'unsubscribe',
            },
            sizes=(2, 2, 1, 2)
        )
    )

@user_rt.callback_query(F.data == 'subscribe')
async def cb_subscribe(callback: types.CallbackQuery):
    subs = get_subs()
    user_id = str(callback.from_user.id)
    if user_id not in subs:
        subs.append(user_id)
        save_subs(subs)
        await callback.answer('Вы подписались на рассылку')
    else:
        await callback.answer('Вы уже подписаны')

@user_rt.callback_query(F.data == 'unsubscribe')
async def cb_unsubscribe(callback: types.CallbackQuery):
    subs = get_subs()
    user_id = str(callback.from_user.id)
    if user_id in subs:
        subs.remove(user_id)
        save_subs(subs)
        await callback.answer('Вы отписались от рассылки')
    else:
        await callback.answer('Вы не были подписаны')

@user_rt.callback_query(F.data == 'heatmap')
async def cb_heatmap(callback: types.CallbackQuery):
    await callback.answer('Тепловая карта (в разработке)')
    await get_heatmap(callback.message.chat.id, callback.bot)

@user_rt.callback_query(F.data == 'funding')
async def cb_funding(callback: types.CallbackQuery):
    await callback.answer('Фандинг (в разработке)')
    await get_funding(callback.message.chat.id, callback.bot)

@user_rt.callback_query(F.data == 'leaders')
async def cb_leaders(callback: types.CallbackQuery):
    await callback.answer('Лидеры роста/падения (в разработке)')
    await get_leaders(callback.message.chat.id, callback.bot)

@user_rt.callback_query(F.data == 'positions')
async def cb_positions(callback: types.CallbackQuery):
    await callback.answer('Открытые позиции (в разработке)')
    await get_positions(callback.message.chat.id, callback.bot)

@user_rt.callback_query(F.data == 'oi_change')
async def cb_oi_change(callback: types.CallbackQuery):
    await callback.answer('Изменение OI (в разработке)')
    await get_oi_change(callback.message.chat.id, callback.bot)
