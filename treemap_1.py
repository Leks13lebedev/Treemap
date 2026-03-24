import pandas as pd
import requests as req
import io
from tabulate import tabulate
import plotly.express as px
from PIL import Image

import os


# Это распределение на секции. При введении новых контрактов, необходимо будет просто добавить данный контракт в нужную ячейку
valuta = ['Si','CNY','ED','UCNY','Eu','UKZT','UTRY','TRY','INR','KZT','UCAD','CNI','UCHF','EJPY','EGBP','ECAD','HKD','UJPY','AED','AUDU','INR','AMD','BYN','GBPU']
tovarka = ['BR','GOLD','NG','SILV','GL','COCOA','ZINK','WHEAT','SUGAR','SUGR','NICKEL','ALUMN','NGM','COCOA','PLD','PLT','BRM','COPPER']
fonda = ['SBRF','GAZR','VTBR']
index = ['MIX','RTS','MXI','RTSM','RGBI','RVI','OGI','HOME','MOEXCNY','IPO','MMI','CNI','FNI']
inter_fonda = ['SPYF','NASD','ALIBABA','R2000','EM','BYN','AUDU','HANG','BAIDU','DAX','NIKK','STOX','DJ30','INDIA','IBIT','ETHA','TENCENT','XIA','TLT', 'IBIT','BTC','ETHA','ETH']
vechnicky = ['SBERF','GAZPF','EURRUBF','GLDRUBF','IMOEXF','CNYRUBF','SBERF','USDRUBF']
prosent = ['RUON','1MFR']


# Списки, которые должны обновляться. Почитать, как с ними работать можно вот здесь https://plotly.com/python/treemaps/ ПОМНИ, ЕСЛИ МЕНЯЕШЬ НАЗВАНИЕ РОДИТЕЛЬСКИХ БЛОКОВ,
# ТО МЕНЯТЬ НАДО ВЕЗДЕ, ИНАЧЕ ПРОГРАММА СЛОМАЕТСЯ!!!!
names = ['Карта срочного рынка',
            'Валютные фьючерсы', 'Товарные фьючерсы', 'Фьючерсы на акции', 'Индексные фьючерсы', 'Глобальные активы', 'Вечные фьючерсы']
parents = ['',
        'Карта срочного рынка', 'Карта срочного рынка', 'Карта срочного рынка', 'Карта срочного рынка', 'Карта срочного рынка', 'Карта срочного рынка']
persents = []
changes = []
lasts = []


# Делаем так, чтобы разбить программу на 2 файла, чтобы не делать километровый файл. stroca - какой сегодня день и в какое время была сделана карта
# ЕСЛИ ХОЧЕШЬ ПРОСТО ВЫГРУЗИТЬ ТЕКУЩУЮ КАРТУ В ФАЙЛ 1.png ТЕБЕ НАДО В САМЫЙ НИЗ ВСТАВИТЬ map('01.01.2025 9:20') - или другое время и дату, которое тебе надо поставить 
async def map(stroca, session):
    print(1111111111)
    global names, parents, persents,changes,lasts, valuta, tovarka, fonda, index, inter_fonda, vechnicky, prosent

    # Данные подтягиваются через iss ссылку и преобразуются в нужный формат (нужно, чтобы получить последние фьючерсы для активов).
    def get_data(session):
        url = "https://iss.moex.com/iss/engines/futures/markets/forts/securities.csv"
        r = session.get(url) 
        df = pd.read_csv(io.StringIO(r.text.split('\n\n')[3]), sep=';')
        secs = r.text.split("\n\n")[1]
        market = pd.read_csv(io.StringIO(secs), sep=";")
        df = df.merge(market[["SECID", "SHORTNAME", "LASTTRADEDATE", "ASSETCODE"]], how="left")
        filtered = df.groupby("ASSETCODE").agg({"LASTTRADEDATE": "min"}).reset_index()
        df = df[(df["ASSETCODE"] + df["LASTTRADEDATE"]).isin(filtered["ASSETCODE"] + filtered["LASTTRADEDATE"])]
        df_price = df[["SHORTNAME", "LASTTOPREVPRICE", "LAST", "VALTODAY"]].sort_values(by="VALTODAY",ascending=False)

        def format_percent(value):
            if value > 0:
                return "+" + str(round(value, 2)) + "%"
            elif value <= 0:
                return "" + str(round(value, 2)) + "%"
            
        df_price["display"] = df_price["LASTTOPREVPRICE"].fillna(0).apply(lambda x: format_percent(x))
        df_price["LAST"] = df_price["LAST"].astype("float")
        return df_price



    # Дробим на секции. Надо посчитать обороты по всем из них. ПОМНИ ЧТО ЕСЛИ У РОДИТЕЛЬСКОГО БЛОКА БУДЕТ VALUE МЕНЬШЕ, ЧЕМ У БЛОКА ВХОДЯЩЕГО В НЕГО, ТО ПРОГРАММА НЕ ВЫВЕДЕТ НИЧЕГО!!!
    def drob_section(df):
        global valuta
        global tovarka
        global fonda
        global index
        global inter_fonda
        global vechnicky
        global prosent
        df['SHORTNAME_1'] = df['SHORTNAME'].apply(lambda x: x.split('-')[0])
        df_valuta = df[df['SHORTNAME_1'].isin(valuta)]
        df_tovarka = df[df['SHORTNAME_1'].isin(tovarka)]
        df_fonda = df[df['SHORTNAME_1'].isin(fonda)]
        df_index = df[df['SHORTNAME_1'].isin(index)]
        df_inter_fonda = df[df['SHORTNAME_1'].isin(inter_fonda)]
        df_vechnicky = df[df['SHORTNAME_1'].isin(vechnicky)]
        df_prosent = df[df['SHORTNAME_1'].isin(prosent)]
        return df_valuta, df_tovarka, df_fonda, df_index, df_inter_fonda, df_vechnicky, df_prosent


    # Формируем лист, который будет содержать все наши данные, которые нам нужны. Он формирует их в нужном нам порядке, чтобы потом можно было пробежаться по списку и положить
    # в нужный список нужное значение
    def list_creation(df):
        result_list = []
        for index, row in df[['SHORTNAME', 'VALTODAY', 'LASTTOPREVPRICE', 'display', 'LAST']].iterrows():
            name = row['SHORTNAME']
            values = row['VALTODAY']
            percent = row['display']
            change = row['LASTTOPREVPRICE']
            last = row['LAST']
            result_list.append(name)       # Название объекта
            result_list.append(values)     # Обороты торгов
            result_list.append(percent)    # Процент, который будет выводиться в блоке
            result_list.append(change)     # Насколько изменилось. Это для customdata, чтобы были нормальноые цвета
            result_list.append(last)       # Абсолютное значение
        return result_list

    # Дробим на секции
    r = get_data(session) 
    df_valuta, df_tovarka, df_fonda, df_index, df_inter_fonda, df_vechnicky, df_prosent = drob_section(r)

    # Создаем списки для каждого раздела (наверное, можно сделать, как-то получше, но я не придумал как)
    list_valuta = list_creation(df_valuta)
    list_tovarka = list_creation(df_tovarka)
    list_fonda = list_creation(df_fonda)
    list_index = list_creation(df_index)
    list_inter_foda = list_creation(df_inter_fonda)
    list_vechnicky = list_creation(df_vechnicky)
    list_prosent = list_creation(df_prosent)
    
    # Находим Объем торгов (ОТ) для каждой из секций
    counter = int(df_valuta['VALTODAY'].sum())+int(df_tovarka['VALTODAY'].sum())+int(df_index['VALTODAY'].sum())+int(df_inter_fonda['VALTODAY'].sum())+ int(df_vechnicky['VALTODAY'].sum())+int(df_fonda['VALTODAY'].sum())
    values = [counter,int(df_valuta['VALTODAY'].sum()), int(df_tovarka['VALTODAY'].sum()), int(df_fonda['VALTODAY'].sum()),
            int(df_index['VALTODAY'].sum()), int(df_inter_fonda['VALTODAY'].sum()), int(df_vechnicky['VALTODAY'].sum())]
    

    # Заполняем данные для каждого актива. Вот от сюда перемещаем в нужный список в нужном порядке
    def name_values_creation(lst, section):
        global names, parents, persents, changes, lasts
        for i in range(0, len(lst), 5):
            names.append(lst[i])
            values.append(lst[i+1])
            parents.append(section)
            persents.append(lst[i+2])
            changes.append(lst[i+3])
            lasts.append(lst[i+4])
    # НЕ ЗАБУДЬ, ЕСЛИ ТЫ РЕШИШЬ ПОМЕНЯТЬ НАЗВАНИЕ БОЛЬШОГО БЛОКА, ТО ПРИДЕТСЯ ПОМЕНЯТЬ И ЗДЕСЬ!!! И НАВЕРХУ, ПОТОМУ ЧТО ЕСЛИ У ТЕБЯ НАЗВАНИЕ РОДИТЕЛЬСКОГО И ПРИЕМНОГО СПИСКА
    # НЕ СОЙДУТСЯ, ТО КАРТА НЕ ВЫГРУЗИТСЯ
    name_values_creation(list_valuta, 'Валютные фьючерсы')
    name_values_creation(list_tovarka, 'Товарные фьючерсы')
    name_values_creation(list_fonda, 'Фьючерсы на акции')
    name_values_creation(list_index, 'Индексные фьючерсы')
    name_values_creation(list_inter_foda, 'Глобальные активы')
    name_values_creation(list_vechnicky, 'Вечные фьючерсы')

    # Создаем цветовую шкалу. Суть в том, что мы просто округляем))
    colorscale = [
        [0.0, 'rgb(255, 5, 7)'], # <= -2.5
        [0.0000000001, "rgb(39,41,49)"], # цвет для основной части карты (т.е. самого большого блока)
        [0.0000000002, "rgb(50, 50, 50)"], # цвет для внутренних блоков (Валютные фьючерсы)
        [0.2, 'rgb(166, 27, 14)'],  # (-2.5 to -1.5]
        [0.3, 'rgb(123, 27, 15)'], # (-1.5 to -0.5]
        [0.5, 'rgb(65,69,84)'], # (-0.5 to 0.5)
        [0.7, 'rgb(35, 118, 26)'], # [0.5 to 1.5)
        [0.8, 'rgb(39, 160, 27)'], # [1.5 to 2.5)
        [1.0, 'rgb(35, 205, 18)'] # >= 2.5
    ]

    normalized_changes = []
    # Создаем цвета. НО ВАЖНО ПОМНИТЬ, ЧТО ЕСЛИ ТЫ ХОЧЕШЬ ГРАДИЕНТНЫЙ СПУСК ПО ЦВЕТАМ, ЧТОБЫ ОНИ ПЛАВНО МЕНЯЛИСЬ ОТ ОДНОГО К ДРУГОМУ, МОЖНО ПРОСТО НОРМАЛИЗОВАТЬ (ОТНОРМИРОВАТЬ ОТ 0 К 1)
    # И ТОГДА У ТЕБЯ ПОЛУЧИТСЯ СДЕЛАТЬ СПУСК, НО ОН БУДЕТ ЗАВИСИТЬ ОТ МАКСИМАЛЬНОГО ИЗМЕНЕНИЯ (РАЗМАХА ВАРИАЦИИ), ПОЭТОМУ БУДЬ АККУРАТЕН))
    for change in changes:
        if change <= -2.5:  
            normalized_changes.append(0.0)

        elif -2.5 < change <= -1.5:
            normalized_changes.append(0.2)

        elif -1.5 < change <= -0.5:
            normalized_changes.append(0.3)

        elif -0.5 < change < 0.5:
            normalized_changes.append(0.5)

        elif 0.5 <= change < 1.5:
            normalized_changes.append(0.7)

        elif 1.5 <= change < 2.5:
            normalized_changes.append(0.8)

        else:
            normalized_changes.append(1.0)

    # Добавляем значения для родительских категорий (первые 7 элементов) ПОМНИ, ЧТО ВАЖНО ЧТОБЫ ДЛИННА ВСЕХ СПИСКОВ, ВХОДЯЩИХ В ДАННУЮ КАРТУ, БЫЛА ОДИНАКОВА, ИНАЧЕ ПОЛУЧИШЬ ОШИБКУ
    normalized_changes = [0.0000000001] + [0.0000000002] * 6 + normalized_changes
    persents = [0] * 7 + persents
    lasts = [0] * 7 + lasts

    # ДЕЛАЕМ КАРТУ!!! ЧТО ЗА ЧТО ОТВЕЧАЕТ НЕ ЗНАЮ, СПРОСИ К GPT
    fig = px.treemap(
        names=names,
        parents=parents,
        values=values,
        branchvalues="total",
        color=normalized_changes,
        color_continuous_scale=colorscale,
        range_color=[0, 1],
        custom_data=[persents, lasts]
    )

    # НАСТРАИВАЕМ ОБЩЕЕ ОКРУЖЕНИЕ. 
    fig.update_layout(
        paper_bgcolor='rgb(39,41,49)',
        plot_bgcolor='rgb(39,41,49)',
        font=dict(
            family="Arial",  # Устанавливаем шрифт Arial для блоков
            color='white', # цвет для надписей внутри блоков
            size=14  # Можно также настроить размер шрифта внутри блоков
        ),
        margin=dict(t=0, l=0, r=0, b=80)  # Увеличили отступ снизу для шкалы ДОБАВЛЯЕМ, ЧТОБЫ МОЖНО БЫЛО ДОБАВИТЬ ЛОГОТИП И НАДПИСЬ.
    )

    # КАК РАБОТАЕТ СПРОСИШЬ У GPT. ЭТА ЧАСТЬ НАСТРАИВАЕТ ТО, КАК БУДЕТ РАСПОЛАГАТЬСЯ ИНФОРМАЦИЯ ВНУТРИ БЛОКА
    fig.update_traces(
        texttemplate='<b>%{label}</b><br>%{customdata[0]}<br>%{customdata[1]:.2f}',
        textposition='middle center',
        hovertemplate='<b>%{label}</b><br><b>Объем: %{value}</b><br><b>Изменение: %{customdata[0]}</b><br><b>Цена: %{customdata[1]:.2f}</b>',
        marker_line=dict(color='rgb(39,41,49)', width=1)
    )
    # НЕ ЗНАЮ, ЧТО ЭТО, ВОЗМОЖНО ВАЖНОЕ)))
    fig.update_coloraxes(showscale=False)

    ### Добавляем шкалу внизу (как на image.jpg) ###
    fig.add_annotation(
        x=0.5,
        y=-0.1,
        xref="paper",
        yref="paper",
        text="",
        showarrow=False,
        font=dict(size=12, color="white"),
        align="center",
        bgcolor="rgb(39,41,49)",
        bordercolor="rgb(39,41,49)"
    )

    # Создаем цветовую шкалу в виде аннотации. СДЕЛИ ЗА ТЕМ, ЧТОБЫ У ТЕБЯ ЦВЕТА НАВЕРХУ И ЗДЕСЬ СОВПАДАЛИ
    scale_colors = ['rgb(255, 5, 7)', 'rgb(166, 27, 14)', 'rgb(123, 27, 15)', 'rgb(65,69,84)', 'rgb(35, 118, 26)', 'rgb(39, 160, 27)', 'rgb(35, 205, 18)']
    scale_labels = ['-3%', '-2%', '-1%', '0%', '+1%', '+2%', '+3%']


    # НЕ РАБОТАЕТ ОТ СЛОВА СОВСЕМ НО МОЖНО ЧТО-ТО ПОПОРОБОВАТЬ ПОМЕНЯТЬ
    scale_width = 0.01  # Ширина каждого блока
    scale_spacing = 0.05 # Расстояние между блоками
    scale_x_start = 0.665 # Начало шкалы (сдвиг влево)
    scale_y_pos = -0.1  # Позиция по Y (низ графика)



    # Добавляем блоки шкалы.ОЧЕНЬ НЕ ПОНЯТНАЯ ЧАСТЬ. ТУТ МНОГО КОСТЫЛЕЙ, ЧТОБЫ ЭТО РАБОТАЛО, НО ЭТО КАК БУДТО БЫ СТРЕЛОЧКИ АННОТАЦИИ
    for i, (color, label) in enumerate(zip(scale_colors, scale_labels)):
        fig.add_annotation(
            x=scale_x_start + (scale_width) + i*scale_spacing,
            y=scale_y_pos,
            xref="paper",
            yref="paper",
            text=label,
            font=dict(size=10, color="white"),  # Уменьшил размер шрифта
            bgcolor=color,
            bordercolor="rgb(39,41,49)",
            borderwidth=1,
            borderpad=2,  
            width=30,     
            height=15,     
            align="center"
        )

    # Обновляем отступы графика (оставляем место для шкалы)
    fig.update_layout(
        margin=dict(t=0, l=0, r=0, b=50)  # Уменьшил отступ снизу 
    )

    # ДОБАВЛЯЕМ ЛОГОТИП. СМОТРИ, ЧТОБЫ У ТЕБЯ ФОТО БЫЛО В НУЖНОЙ ДИРЕКТОРИИ
    img = Image.open("logo.png")
    fig.add_layout_image(
        dict(
            source=img,
            xref="paper", yref="paper",
            x=0.01, y=-0.075,
            sizex=0.1, sizey=0.1,
            xanchor="left", yanchor="bottom"
        )
    )


    # ДОБАВЛЯЕМ ТЕКСТ
    fig.add_annotation(
        x=0.075,  
        y=-0.065,  
        xref="paper",
        yref="paper",
        text=f"<b>Тепловая карта срочного рынка Московской биржи {stroca} мск </b><br>Отражает котировки фьючерсных контрактов и изменения цены последней сделки текущей торговой <br>сессии относительно предыдущей. Размер каждого блока пропорционален объему торгов по контракту.",  # Текст, который нужно отобразить
        showarrow=False,
        font=dict(
            family="Arial",
            size=7,  # Размер шрифта
            color="white",
            #style="italic"
        ),
        align="left",
        bgcolor="rgba(0,0,0,0)",  # Прозрачный фон
        bordercolor="rgba(0,0,0,0)"
    )
    fig.update_traces(
    insidetextfont=dict(color='white'),
    outsidetextfont=dict(color='white')
    )
    print('Save message...')
    # ОБРЕЗАЕМ КАРТИНКУ, Т.К. У ТЕБЯ СВЕРХУ БУДЕТ НАЗВАНИЕ КАРТЫ И СНИЗУ БУДУТ ВИДНЫ ХВОСТЫ ОТ ЛЕГЕНДЫ (-3% -2% -1%....)
    fig.write_image("daily_treemap.png", engine="kaleido", scale=5)
    def crop_image(image_path, output_path, top_crop=50, bottom_crop=50):
        img = Image.open(image_path)
        width, height = img.size
        # Обрезаем: left, upper, right, lower
        cropped_img = img.crop((0, top_crop, width, height - bottom_crop))
        cropped_img.save(output_path)

    print(33333333)
    crop_image("daily_treemap.png", "1.png", top_crop=100, bottom_crop=100)
    if os.path.exists("daily_treemap.png"):
        os.remove("daily_treemap.png")
    # ОБНОВЛЯЕМ, ЧТОБЫ ПРОГА НЕ СЛОМАЛАСЬ
    names = ['Карта срочного рынка',
            'Валютные фьючерсы', 'Товарные фьючерсы', 'Фьючерсы на акции', 'Индексные фьючерсы', 'Глобальные активы', 'Вечные фьючерсы']
    parents = ['',
            'Карта срочного рынка', 'Карта срочного рынка', 'Карта срочного рынка', 'Карта срочного рынка', 'Карта срочного рынка', 'Карта срочного рынка']
    persents = []
    changes = []
    lasts = []
    print('График успешно создан!')
