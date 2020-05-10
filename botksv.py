import telebot # библиотека для доступа к API бота телеграм
import bs4
import requests
import re
import pandas as pd

with open('token.txt') as fh: # в файле token.txt, который находится в одной папке с блокнотом, лежит строка токена и мы ее считываем
    token = fh.read().strip()
    
# создаем экземпляр класса Telebot от нашего токена. Наш код теперь станет бэкэндом бота телеграм с этим токеном
bot = telebot.TeleBot(token) 

# Задаю переменную, чтобы проверять произошел ли уже парсинг или нет
parsed = False
# Задаю переменную со списком валют, которые поддерживает мой бот
supported = ['USD', 'EUR']

# Команды

# Декоратор, который говорит, что функция, которую он декорирует, будет вызываться, когда пользователь
# напишет боту /start
@bot.message_handler(commands=['start'])
def show_start(message):
    # метод класса send_message берет два аргумента - кому отправляем сообщение и сообщение, которое отправляем.
    # объект message - это сообщение от пользователя, в этом классе есть атрибут с метадатой
    # из которого мы достаем id пользователя, который его отправил и отвечаем этому пользователю
    bot.send_message(message.from_user.id, "Добрый день. Я умею работать с сайтом https://www.cbr.ru/currency_base/\
Если вы введете валюту и дату я сообщу ее курс к рублю\
Чтобы посмотреть все команды нажмите /help. Для начала парсинга нажмите /parse. Для просмотра доступных валют для парсинга нажмите /parse_help.")

# все то же, что выше, только реагируем на команду /help
@bot.message_handler(commands=['help'])
def show_help(message):
    bot.send_message(message.from_user.id,"/parse - ввести валюту и запустить парсинг\n/parse_help - вывести список поддерживаемых валют\
    \n/file - получить файл с данными\n/median - посчитать медиану для выбранной колонки\
    \n/mean - посчитать среднее для выбранной колонки\n/date - получить информацию по конкретному дню")

# реагируем на команду /parse. Тут уже будем обновлять переменную parse.
# если пользователь вызвал команду parse, будем задавать переменную parsed = False, чтобы считать, что парсинг еще не выполнен
@bot.message_handler(commands=['parse'])
def parse(message):
    global parsed
    parsed = False
    bot.send_message(message.from_user.id, "Введите код валюты на английском языке и дату: ") # запрашиваем название валюты
    
# реагируем на команду /parse_help. Выводим валюты из списка, для которых можем собрать информацию    
@bot.message_handler(commands=['parse_help'])
def show_parse_help(message):
    bot.send_message(message.from_user.id, f"Пока я могу собрать информацию только для этих валют:\n {' '.join(supported)}")
    
# реагируем на команду /file, если parsed = True, т.е. парсинг завершен, то будем высылать пользователю файл с собранной информацией    
# реагируем на команду /date - выводим информацию о курсе валюты в определенный день, который вводит пользователь 
    
# Обабатываем все остальные сообщения от пользователя, которые не являются командами, прописанными выше
@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    global parsed
    if not parsed: # проверяем, что парсинг не произошел
        if message.text in supported: # проверяем, что введенное сообщение является наименованием валюты, для которой можем сделать парсинг
            try: # пытаемся выполнить парсинг
                bot.send_message(message.from_user.id, "Начинаю парсинг. Подождите...") # сообщаем пользователю, что начали работу
                if message.split()[0] == 'USD': cur = 'R01235'
                elif message.split()[0] == 'EUR': cur = 'R01239'
                date_cur = message.split()[1]

                url = f'http://www.cbr.ru/currency_base/dynamics/?UniDbQuery.Posted=True&UniDbQuery.mode=1&UniDbQuery.date_req1=&UniDbQuery.date_req2=&UniDbQuery.VAL_NM_RQ={cur.lower()}&UniDbQuery.From={date_cur}&UniDbQuery.To={date_cur}' # переходим по ссылке, для заданного

                html = requests.get(url).text
                soup = bs4.BeautifulSoup(html, 'lxml')
                soup.prettify()
                soup.find_all('table')
                soup.find_all('td')
                avr = []
                sum = 0
                for idx in soup.find_all('td'):
                    curs = re.findall(r'\d\d\,\d{4}', str(idx)[4:-5])
                    if curs != []: 
                        curs = ",".join(curs)
                        avr.append(float(curs.replace(",",".")))
                        sum += avr[-1]
                print('average:', sum/len(avr))               
                # ниже привычный нам парсинг, единственное, используем str(graph) вместо graph.text,
   
                parsed = True # меняем метку parsed, если парсинг успешно завершилася
                bot.send_message(message.from_user.id, "Парсинг успешно закончен. Выберите следующую команду:") # сообщаем об этом пользователю

            except Exception:
                # обрабатываем случай, что парсинг почему-то не завершился
                parsed = False # меняем метку на False (если ошибка произошла после того как в прошлом пункте поменяли на True)
                bot.send_message(message.from_user.id, "Произошла ошибка при парсинге. Попробуйте снова или смените страну.") # выдаем сообщение
        else:
            # сюда мы попадаем, если parsed == False
            # это else к тому if, где мы проверяли, что пользователь ввел название страны, для которой мы умеем собирать данные
            show_parse_help(message) 
            # показываем пользователю памятку со списком стран 
            # вызываем функцию parse (она попросит пользователя ввести название страны еще раз)
            parse(message) 
    else:
        # сюда мы попадаем, если parsed == True
        # на этом этапе мы умеем работать только с командами, поэтому говорим пользователю, что мы не распознали команду
        # и напомним, что он может сделать с данными
        bot.send_message(message.from_user.id, "Команда не распознана.")
        bot.send_message(message.from_user.id, "/file - Получить файл с данными\
                \n/median - Посчитать медиану. После команды через пробел напишите номер колонки для которой нужно найти медиану\
                \n/mean - Посчитать среднее. После команды через пробел напишите номер колонки для которой нужно найти медиану\
                \n/date - Получить информацию по конкретному дню. После команды через пробел месяц и день в формате Feb 15. Даты меньше 10 с ведушим нулем - 01,02\
                \nДля {message.text} доступны данные в интервале {dates[0]} - {dates[-1]}")

# этот метод класса постоянно запрашивает сервер Telegram, пришли ли нашему боту новые сообщения
# как только они приходят, бот начинает их обрабатывать и вызывает нужную функцию в зависимости от содержания сообщения
# если не написать эту строку, то ваш бот не сможет получать сообщения от пользователя
bot.polling(none_stop=True, interval=0)