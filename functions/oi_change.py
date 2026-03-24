from services.session import get_session
import pandas as pd
import datetime
import io
from tabulate import tabulate

async def get_oi_change(chat_id: int, bot):
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
    
    # Твоя функция open_oi() из user.py
    def open_oi(r):
        now = datetime.datetime.utcnow() + datetime.timedelta(hours=3)
        now = now.strftime("%H:%M:%S")

        mdata = r.text.split("\n\n")[3]
        df = pd.read_csv(io.StringIO(mdata), sep=";")

        secs = r.text.split("\n\n")[1]
        market = pd.read_csv(io.StringIO(secs), sep=";")

        df = df.merge(
            market[["SECID", "SHORTNAME", "LASTTRADEDATE", "ASSETCODE","PREVOPENPOSITION"]], how="left"
        )
        filtered = df.groupby("ASSETCODE").agg({"LASTTRADEDATE": "min"}).reset_index()
        df = df[
            (df["ASSETCODE"] + df["LASTTRADEDATE"]).isin(
                filtered["ASSETCODE"] + filtered["LASTTRADEDATE"]
            )
        ]
        price_change = df[["SHORTNAME", "OPENPOSITION", "PREVOPENPOSITION","VALTODAY","LASTTOPREVPRICE"]].sort_values(by="VALTODAY", ascending=False).iloc[:20]

        price_change["open_change"] = (price_change["OPENPOSITION"] - price_change["PREVOPENPOSITION"])/price_change["PREVOPENPOSITION"]*100
        price_change["open_change_abs"] = price_change['open_change'].abs()
        price_change_abs = price_change.sort_values(by="open_change", ascending=False)

        def color(value1):
            if value1 > 0:
                return "🟢"
            elif value1 <= 0:
                return "🔴"

        price_change_abs["colorist"] = price_change_abs["open_change"].apply(
            lambda x: color(x)
        )
        price_change_abs["colorist_price"] = price_change_abs["LASTTOPREVPRICE"].apply(
            lambda x: color(x)
        )

        price_change_abs["display"] = price_change_abs["LASTTOPREVPRICE"].map('{0:.1f}'.format)
        price_change_abs["open_display"] = price_change_abs["open_change"].map('{0:.1f}'.format)

        assets = tabulate(
            price_change_abs.iloc[:20][["SHORTNAME", "open_display","colorist", "display","colorist_price"]],
            showindex="false",
            tablefmt="plain",
            numalign="right",
        )
        assets = f"<pre>{assets}</pre>"
        final_text = f"<b>Изменение OI</b>\n\n<i>Изменение открытых позиций и цены последней сделки текущего дня к предыдущему дню</i>\n\nВремя обновления: <code>{now}</code> МСК\n\n" \
                    f"<b>Asset OI % Price %</b>\n{assets}\n\n"
        return final_text

    r = get_data()
    text = open_oi(r)
    for cid in chat_id:
        try:
            await bot.send_message(cid, text, parse_mode="HTML")
        except Exception as e:
            print(f"Ошибка отправки oi_change пользователю {cid}: {e}")
