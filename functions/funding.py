from services.session import get_session  
import pandas as pd
import datetime
from tabulate import tabulate

async def get_funding(chat_id: int, bot):
    if isinstance(chat_id, int):
        chat_id = [chat_id]
    else:
        chat_id = chat_id
    session = get_session()  
    
    data_frame = []
    tickers = ['USDRUBF','EURRUBF','CNYRUBF','IMOEXF', 'RGBIF', 'GLDRUBF','SBERF','GAZPF']
    
    for url in tickers:
        link = f'https://iss.moex.com/iss/engines/futures/markets/forts/securities/{url}.json?marketdata.columns=SECID,SWAPRATE'
        
        response = session.get(link)
        
        dt = response.json()
        columns = dt['marketdata']['columns']
        row = dt['marketdata']['data']
        
        if len(row) > 0:
            df = pd.DataFrame(row, columns=columns)
            data_frame.append(df)
    
    df = pd.concat(data_frame, axis=0)
    now = (datetime.datetime.utcnow() + datetime.timedelta(hours=3)).strftime("%H:%M:%S")
    df['lot'] = [1000, 1000, 1000, 10, 100, 1, 100, 100]
    
    gainers = tabulate(df, showindex=False, tablefmt="plain", numalign="right")
    
    k = f"""<b>📈 СВОДКА РЫНКА 📉</b>\n
    \nВремя обновления: <code>{now}</code> МСК\n
    \n<pre>{gainers}</pre>"""
    for cid in chat_id:
        try:
            await bot.send_message(cid, k, parse_mode="HTML")
        except Exception as e:
            print(f"Ошибка отправки oi_change пользователю {cid}: {e}")
    
