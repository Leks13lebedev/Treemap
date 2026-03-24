from services.session import get_session
import pandas as pd
import datetime
import io
from tabulate import tabulate
import emoji

async def get_positions(chat_id: int, bot):
    if isinstance(chat_id, int):
        chat_id = [chat_id]
    else:
        chat_id = chat_id
    session = get_session()
    
    # Твоя функция get_futoi_data() из user.py
    def get_futoi_data():
        current_date = datetime.date.today()
        url = f"https://iss.moex.com/iss/analyticalproducts/futoi/securities.csv?date={current_date}"
        r = session.get(url)
        
        lines = r.text.splitlines()
        start, end = None, None
        
        for i, line in enumerate(lines):
            if line.strip() == "futoi":
                start = i + 1
            elif start and line.startswith("futoi."):
                end = i
                break
        
        data_lines = lines[start:end]
        csv_text = "\n".join(data_lines)
        df = pd.read_csv(io.StringIO(csv_text), sep=";")
        return df
    
    # Твоя функция get_data() для фьючерсов
    def get_data():
        url = "https://iss.moex.com/iss/engines/futures/markets/forts/securities.csv"
        r = session.get(url)
        return r
    
    # Твоя функция get_oi1() из user.py (первая часть с физиками)
    def get_oi1():
        u = get_data()
        secs2 = u.text.split("\n\n")[1]
        market2 = pd.read_csv(io.StringIO(secs2), sep=";")
        market4 = market2.drop_duplicates()
        market = get_futoi_data()
        df = market[["ticker", "clgroup", "pos", "pos_short", "pos_long", "systime"]]
        df['pos_abs'] = df["pos_short"].abs() + df["pos_long"].abs()
        df_new = df.sort_values(by=["systime", "pos_abs"], ascending=False)
        df_new = df_new.drop_duplicates(subset=['ticker','clgroup'])
        df_new['ticker_str'] = df_new['ticker'].astype(str)
        df_new['ticker_length'] = df_new['ticker_str'].str.len()
        gl_tickers = df_new[df_new['ticker_str'] == 'GL'].copy()
        other_short = df_new[(df_new['ticker_length'] <= 2) & (df_new['ticker_str'] != 'GL')].copy()
        long_tickers = df_new[df_new['ticker_length'] > 2].copy()
        merged_parts = []
        
        if not other_short.empty:
            market3 = market4[["SECTYPE", "ASSETCODE"]]
            market3.columns = ['ticker', 'ASSETCODE']
            merged_short = other_short.merge(market3, on='ticker', how='left')
            merged_short['ASSETCODE'] = merged_short['ASSETCODE'].fillna(merged_short['ticker'])
            merged_parts.append(merged_short)

        if not gl_tickers.empty:
            gl_tickers['ASSETCODE'] = gl_tickers['ticker']
            merged_parts.append(gl_tickers)
            
        if not long_tickers.empty:
            long_tickers['ASSETCODE'] = long_tickers['ticker']
            merged_parts.append(long_tickers)
        
        dflast = pd.concat(merged_parts, ignore_index=True).drop_duplicates(subset=['ticker', 'clgroup'])
        dflast2 = dflast[dflast["clgroup"] == "FIZ"]
        dflast3 = dflast2[["ASSETCODE", "pos_abs", "pos_short","pos_long"]]
        dflast4 = dflast3.sort_values(by=["pos_abs", "ASSETCODE"], ascending=False)

        dflast4["pos_abs"] = dflast4["pos_abs"]/1000
        dflast4["pos_short"] = dflast4["pos_short"]/1000
        dflast4["pos_long"] = dflast4["pos_long"]/1000

        dflast4["pos_short_display"] = dflast4["pos_short"].abs().map('{0:.0f}'.format)
        dflast4["pos_long_display"] = dflast4["pos_long"].abs().map('{0:.0f}'.format)
        dflast4["position"] = dflast4["pos_abs"].map('{0:.0f}'.format)
        dflast5 = dflast4[["ASSETCODE", "position", "pos_long_display","pos_short_display"]].iloc[:10]

        assets = tabulate(
            dflast5.iloc[:20],
            showindex="false",
            tablefmt="plain",
            numalign="right",
        )
        assets = f"<pre>{assets}</pre>"

        # Юрики
        dfur2 = dflast[dflast["clgroup"] == "YUR"]
        dfur3 = dfur2[["ASSETCODE", "pos_abs", "pos_short", "pos_long"]]
        dfur4 = dfur3.sort_values(by=["pos_abs", "ASSETCODE"], ascending=False)

        dfur4["pos_abs"] = dfur4["pos_abs"] / 1000
        dfur4["pos_short"] = dfur4["pos_short"] / 1000
        dfur4["pos_long"] = dfur4["pos_long"] / 1000

        dfur4["pos_short_display"] = dfur4["pos_short"].abs().map('{0:.0f}'.format)
        dfur4["pos_long_display"] = dfur4["pos_long"].abs().map('{0:.0f}'.format)
        dfur4["position"] = dfur4["pos_abs"].map('{0:.0f}'.format)
        dfur5 = dfur4[["ASSETCODE", "position", "pos_long_display", "pos_short_display"]].iloc[:10]

        assets2 = tabulate(
            dfur5.iloc[:20],
            showindex="false",
            tablefmt="plain",
            numalign="right",
        )
        assets2 = f"<pre>{assets2}</pre>"

        final_text = f"<b>📊 Открытые позиции физ. лиц,</b>\n" \
                    f"<b>тыс. штук</b>\n\n" \
                    f"<b>Asset Total Long Short</b>\n{assets}\n\n"\
                    f"<b>📊 Открытые позиции юр. лиц,</b>\n" \
                    f"<b>тыс. штук</b>\n\n" \
                    f"<b>Asset Total Long Short</b>\n{assets2}\n\n"
        return final_text

    text = get_oi1()
    for cid in chat_id:
        try:
            await bot.send_message(cid, text, parse_mode="HTML")
        except Exception as e:
            print(f"Ошибка отправки positions пользователю {cid}: {e}")