import telebot # библиотека для доступа к API бота телеграм
import bs4
import requests
import re
import pandas as pd
import datetime

with open('token.txt') as fh: # в файле token.txt, который находится в одной папке с блокнотом, лежит строка токена и мы ее считываем
    token = fh.read().strip()
    
# создаем экземпляр класса Telebot от нашего токена. Наш код теперь станет бэкэндом бота телеграм с этим токеном
bot = telebot.TeleBot(token) 

# Задаю переменную, чтобы проверять произошел ли уже парсинг или нет
parsed = False
# Задаю переменную со списком валют, которые поддерживает мой бот
supported = ['USD', 'EUR', 'GBP', 'JPY', 'CNY']

# Команды

# Декоратор, который говорит, что функция, которую он декорирует, будет вызываться, когда пользователь
# напишет боту /start
@bot.message_handler(commands=['start'])
def show_start(message):
    # метод класса send_message берет два аргумента - кому отправляем сообщение и сообщение, которое отправляем.
    # объект message - это сообщение от пользователя, в этом классе есть атрибут с метадатой
    # из которого мы достаем id пользователя, который его отправил и отвечаем этому пользователю
    bot.send_message(message.from_user.id, "Привет. Я умею работать с сайтом https://www.cbr.ru/currency_base/. \
Если вы введете название валюты, то я соберу данные по всей истории курсов данной валюты.\
После того, как я соберу данные, я смогу вывести следующую информацию: \
средний курс валюты за выбранный месяц, \
курс валюты на выбранную дату. \
 \
Чтобы посмотреть все команды нажмите /help. Для начала парсинга нажмите /parse. Для просмотра доступных валют введеите /parse_help.")

# все то же, что выше, только реагируем на команду /help
@bot.message_handler(commands=['help'])
def show_help(message):
    bot.send_message(message.from_user.id,"/parse - ввести валюту и запустить парсинг\n/parse_help - вывести список поддерживаемых валют\
    \n/file - получить файл с данными\n/mean - посчитать среднее значение для выбранной валюты за месяц. Введите последний день месяца в формате: yyyy.mm.\
    \n/date - получить курс валюты к рублю на дату. Формат ввода после команды: код_валюты dd.mm.yyyy")

# реагируем на команду /parse. Тут уже будем обновлять переменную parse.
# если пользователь вызвал команду parse, будем задавать переменную parsed = False, чтобы считать, что парсинг еще не выполнен
@bot.message_handler(commands=['parse'])
def parse(message):
    global parsed
    parsed = False
    bot.send_message(message.from_user.id, "Введите код валюты: ") # запрашиваем название валюты
    
# реагируем на команду /parse_help. Выводим валюты из списка, для которых можем собрать информацию    
@bot.message_handler(commands=['parse_help'])
def show_parse_help(message):
    bot.send_message(message.from_user.id, f"Пока я могу собрать информацию только для этих валют:\n {' '.join(supported)}")

# реагируем на команду /file, если parsed = True, т.е. парсинг завершен, то будем высылать пользователю файл с собранной информацией    
@bot.message_handler(commands=['file'])
def get_file(message):
    global parsed
    if parsed: # проверяем, что парсинг завершился
        fh = open('data.csv', 'rb') # наш файл, который после парсинга сохраняется локально или на сервере. Открываем его.
        bot.send_document(message.from_user.id, fh) # отправляем файл, с которым работаем, пользователю
        fh.close() # закрываем файл
    else:
        # если информация не собрана, то скажем об этом пользователю и подскажем, как запустить процесс
        bot.send_message(message.from_user.id, "Парсинг не выполнен. Нажмите /parse чтобы это сделать") 

# все то же самое, что выше только для арифметического среднего        
@bot.message_handler(commands=['mean'])
def get_mean(message):
    global parsed
    col = message.text.split()
    if parsed:
        data = pd.read_csv('data.csv', delimiter = ',')
        data['date'] = pd.to_datetime(data['date'], format='%d.%m.%Y')
        res = (data.groupby(pd.Grouper(key='date', freq='M'))['curs'].mean().reset_index(name='Avg'))
        period = col[1]
        mea = round(res.loc[res.date == period, 'Avg'].values[0], 4)

        bot.send_message(message.from_user.id, "Средний курс = " + str(mea))
    else:
        bot.send_message(message.from_user.id, "Парсинг не выполнен. Нажмите /parse чтобы это сделать")
    
# реагируем на команду /date - выводим информацию о курсе валюты в определенный день, который вводит пользователь 
@bot.message_handler(commands=['date'])
def get_date(message):
    col = message.text.split() # мы ожидаем сообщение в формате '/date USD 20.03.2020', разбиваем по пробелам
    if len(col) != 3: # топорно обрабатываем ошибку, если в разбитом сообщение не три элемента (команда, месяц и дата)
        bot.send_message(message.from_user.id, "Дата не указана.")

    if col[1] in supported:
        try: # пытаемся выполнить парсинг
            date_cur = col[2]
            url = f'http://www.cbr.ru/currency_base/daily/?UniDbQuery.Posted=True&UniDbQuery.To={date_cur}'
            html = requests.get(url).text
            soup = bs4.BeautifulSoup(html, 'lxml')
            soup.find_all('table')
            soup.find_all('td')
            exch = []
            for idx in soup.find_all('td'):
                if str(idx)[4:-5] == col[1]:
                    exch.append(str(idx)[4:-5])
                if  len(exch) != 0:
                    exch.append(str(idx)[4:-5])
                if  len(exch) == 5: break
            print(f'Курс {col[1]}/RUB на {date_cur}: {exch[4]}')
            # выводим сообщение с информацией
            bot.send_message(message.from_user.id, f'Курс {col[1]}/RUB на {date_cur}: {exch[4]}')
        except Exception:
            # выводим информацию об ошибке в дате
            bot.send_message(message.from_user.id, "Ошибка в дате или дата не доступна, попробуйте еще раз.")
    else:
        # это else к тому if, где мы проверяли, что пользователь ввел код валюты, для которой мы умеем собирать данные
        show_parse_help(message) 
        # показываем пользователю памятку со списком валют 
    
# Обабатываем все остальные сообщения от пользователя, которые не являются командами, прописанными выше
@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    global parsed
    if not parsed: # проверяем, что парсинг не произошел
        if message.text.split()[0] in supported: # проверяем, что введенное сообщение является наименованием валюты, для которой можем сделать парсинг
            try: # пытаемся выполнить парсинг
                bot.send_message(message.from_user.id, "Начинаю парсинг. Подождите...") # сообщаем пользователю, что начали работу
                if message.text.split()[0] == 'USD': cur = 'R01235'
                elif message.text.split()[0] == 'EUR': cur = 'R01239'
                elif message.text.split()[0] == 'GBP': cur = 'R01035'
                elif message.text.split()[0] == 'JPY': cur = 'R01820'
                elif message.text.split()[0] == 'CNY': cur = 'R01375'
                
                now = str(datetime.datetime.now()).split()[0].split('-')
                date_cur = f'{now[2]}.{now[1]}.{now[0]}'

                url = f'http://www.cbr.ru/currency_base/dynamics/?UniDbQuery.Posted=True&UniDbQuery.mode=1&UniDbQuery.date_req1=&UniDbQuery.date_req2=&UniDbQuery.VAL_NM_RQ={cur}&UniDbQuery.From=01.07.2000&UniDbQuery.To={date_cur}' # переходим по ссылке, для заданного
                        
                html = requests.get(url).text
                soup = bs4.BeautifulSoup(html, 'lxml')
                soup.find_all('table')
                soup.find_all('td')
                dates_curs = []
                curs = []
                nominal = []

                for idx in soup.find_all('td'):
                    ex_cur = re.findall(r'\d\d\,\d{4}', str(idx)[4:-5])
                    dates = re.findall(r'\d\d\.\d\d\.\d{4}', str(idx)[4:-5])
                    if ex_cur != []: 
                        ex_cur = ",".join(ex_cur)
                        curs.append(float(ex_cur.replace(",",".")))
                    if dates != []: 
                        dates = ",".join(dates)
                        dates_curs.append(dates)
                    if (str(idx)[4:-5]).isdigit():
                        nominal.append(str(idx)[4:-5])

                with open('data.csv', 'w') as fh: # открываем файл, чтобы сохранить в него собранную информацию
                    fh.write('date,curs,nominal\n') # записываем название колонок
#                    bot.send_message(message.from_user.id, f'Test 3: не разберусь где ошибка, но сайт парсится до ошибки: {dates_curs}') # сообщаем об этом пользователю

                    for i in range(len(dates_curs)):
                        fh.write(f'{dates_curs[i]},{curs[i]},{nominal[i]}\n') # записываем строки с данными для каждого ряда

                parsed = True # меняем метку parsed, если парсинг успешно завершилася
                bot.send_message(message.from_user.id, "Парсинг успешно закончен. Выберите следующую команду:") # сообщаем об этом пользователю
                bot.send_message(message.from_user.id, f'''/file - Получить файл с данными\ 
                \n/mean - Посчитать среднее за месяц. После команды пробел напишите последний день нужного месяца в формате yyyy-mm-dd: например, 2020-04-30)''')

            except Exception:
                # обрабатываем случай, что парсинг почему-то не завершился
                parsed = True # меняем метку на False (если ошибка произошла после того как в прошлом пункте поменяли на True)
        else:
            # сюда мы попадаем, если parsed == False
            # это else к тому if, где мы проверяли, что пользователь ввел название валюты, для которой мы умеем собирать данные
            show_parse_help(message) 
            # показываем пользователю памятку со списком стран 
            # вызываем функцию parse (она попросит пользователя ввести название страны еще раз)
            parse(message) 
    else:
        # сюда мы попадаем, если parsed == True
        # на этом этапе мы умеем работать только с командами, поэтому говорим пользователю, что мы не распознали команду
        # и напомним, что он может сделать с данными
        bot.send_message(message.from_user.id, "Команда не распознана.")

# этот метод класса постоянно запрашивает сервер Telegram, пришли ли нашему боту новые сообщения
# как только они приходят, бот начинает их обрабатывать и вызывает нужную функцию в зависимости от содержания сообщения
# если не написать эту строку, то ваш бот не сможет получать сообщения от пользователя
bot.polling(none_stop=True, interval=0)