from services.session import get_session
import pandas as pd
import datetime
import io
from tabulate import tabulate
import emoji

async def get_leaders(chat_id: int, bot):
    if isinstance(chat_id, int):
        chat_id = [chat_id]
    else:
        chat_id = chat_id
    session = get_session()
    
    # Твоя функция get_data() из user.py
    def get_data():
        url = "https://iss.moex.com/iss/engines/futures/markets/forts/securities.csv"
        r = session.get(url)
        return r

    # Твоя функция get_prices_EV() из user.py
    def get_prices_EV(r):
        now = datetime.datetime.utcnow() + datetime.timedelta(hours=3)
        now = now.strftime("%H:%M:%S")

        mdata = r.text.split("\n\n")[3]
        df = pd.read_csv(io.StringIO(mdata), sep=";")

        secs = r.text.split("\n\n")[1]
        market = pd.read_csv(io.StringIO(secs), sep=";")

        df = df.merge(
            market[["SECID", "SHORTNAME", "LASTTRADEDATE", "ASSETCODE"]], how="left"
        )
        filtered = df.groupby("ASSETCODE").agg({"LASTTRADEDATE": "min"}).reset_index()
        df = df[
            (df["ASSETCODE"] + df["LASTTRADEDATE"]).isin(
                filtered["ASSETCODE"] + filtered["LASTTRADEDATE"]
            )
        ]

        price_change = df[["SHORTNAME", "LASTTOPREVPRICE", "LAST"]]

        def format_percent(value):
            if value > 0:
                return "+" + str(round(value, 2)) + "%"
            elif value < 0:
                return "" + str(round(value, 2)) + "%"

        price_change["display"] = price_change["LASTTOPREVPRICE"].apply(
            lambda x: format_percent(x)
        )
        price_change["LAST"] = price_change["LAST"].astype("float")

        gainers = tabulate(
            price_change[price_change["LASTTOPREVPRICE"] > 0]
            .sort_values(by="LASTTOPREVPRICE", ascending=False)
            .iloc[:10][["SHORTNAME", "display", "LAST"]],
            showindex="false",
            tablefmt="plain",
            numalign="right",
        )
        gainers = f"<pre>{gainers}</pre>"

        losers = tabulate(
            price_change[price_change["LASTTOPREVPRICE"] < 0]
            .sort_values(by="LASTTOPREVPRICE", ascending=True)
            .iloc[:10][["SHORTNAME", "display", "LAST"]],
            showindex="false",
            tablefmt="plain",
            numalign="right",
        )
        losers = f"<pre>{losers}</pre>"

        n_gain = (price_change["LASTTOPREVPRICE"] > 0).sum()
        n_lost = (price_change["LASTTOPREVPRICE"] < 0).sum()
        if n_gain == 0 or n_lost == 0:
            bar = ""
        else:
            total = n_gain + n_lost
            length = 12
            bar = "=" * length
            position = round(round(n_gain / total, 2) * length)
            bar = len(bar[:position]) * emoji.emojize(":green_square:") + emoji.emojize(
                ":red_square:"
            ) * len(bar[position + 1 :])
            bar = str(n_gain) + bar + str(n_lost)
            
        final_text = f"<b>📈 СВОДКА РЫНКА 📉</b>\n\n<i>Изменение цены последней сделки текущего дня к цене предыдущего дня и котировка</i>\n\nВремя обновления: <code>{now}</code> МСК\n\n<b>Структура рынка (фьючерсы)</b><pre>{bar}</pre>\n\n🟢 <b>Лидеры роста</b> 🟢\n{gainers}\n\n🔴 <b>Лидеры падения</b> 🔴\n{losers}"
        return final_text

    r = get_data()
    text = get_prices_EV(r)
    for cid in chat_id:
        try:
            await bot.send_message(cid, text, parse_mode="HTML")
        except Exception as e:
            print(f"Ошибка отправки leaders пользователю {cid}: {e}")