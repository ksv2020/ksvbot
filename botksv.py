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
# Задаю переменную со списком стран, которые поддерживает мой бот
supported = ['France', 'China', 'Italy', 'Russia']

# Команды

# Декоратор, который говорит, что функция, которую он декорирует, будет вызываться, когда пользователь
# напишет боту /start
@bot.message_handler(commands=['start'])
def show_start(message):
    # метод класса send_message берет два аргумента - кому отправляем сообщение и сообщение, которое отправляем.
    # объект message - это сообщение от пользователя, в этом классе есть атрибут с метадатой
    # из которого мы достаем id пользователя, который его отправил и отвечаем этому пользователю
    bot.send_message(message.from_user.id, "Добрый день. Я умею работать с сайтом https://www.worldometers.info/coronavirus/.\
Если вы введете название страны на английском языке я выведу вам статистику с 15 февраля: сколько было \
зафиксировано новых случаев и смертей за каждый из день. После того, как я соберу данные, я смогу вывести следующую информацию: \
ввывести среднее количество случаев или смертей (по запросу) за это время, вывести количество новых случаев или смертей за \
любую дату, вывести количество дней, в которые было зафиксировано больше случаев или смертей, чем в предыдущие. \
Чтобы посмотреть все команды нажмите /help. Для начала парсинга нажмите /parse. Для просмотра доступных стран для парсинга нажмите /parse_help.")

# все то же, что выше, только реагируем на команду /help
@bot.message_handler(commands=['help'])
def show_help(message):
    bot.send_message(message.from_user.id,"/parse - ввести страну и запустить парсинг\n/parse_help - вывести список поддерживаемых стран\
    \n/file - получить файл с данными\n/median - посчитать медиану для выбранной колонки\
    \n/mean - посчитать среднее для выбранной колонки\n/date - получить информацию по конкретному дню")

# реагируем на команду /parse. Тут уже будем обновлять переменную parse.
# если пользователь вызвал команду parse, будем задавать переменную parsed = False, чтобы считать, что парсинг еще не выполнен
@bot.message_handler(commands=['parse'])
def parse(message):
    global parsed
    parsed = False
    bot.send_message(message.from_user.id, "Введите название страны на английском языке: ") # запрашиваем название страны
    
# реагируем на команду /parse_help. Выводим страны из списка, для которых можем собрать информацию    
@bot.message_handler(commands=['parse_help'])
def show_parse_help(message):
    bot.send_message(message.from_user.id, f"Пока я могу собрать информацию только для этих стран:\n {' '.join(supported)}")
    
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

# реагируем на команду /median - возвращаем медианное значение смертей или новых случаев        
@bot.message_handler(commands=['median'])
def get_median(message):
    global parsed 
    if parsed: # проверяем, что парсинг произошел
        col = message.text.split() # парсим сообщение от пользователя, он может ввести команду и выбрать колонку - deaths или cases
        if len(col) == 2: # проверяем, было ли в команде название колонки (split() тогда вернет список из двух элементов)
            if col[1] == 'cases': # если пользователь ввел cases, то выбираем нужную колонку
                col = 'number of daily cases'
            else: # то же самое для deaths
                col = 'number of daily deaths'
        else: # если пользователь ввел только команду /median, то выбираем колонку по умолчанию (cases)
            col = 'number of daily cases'
# здесь мы не сделали обработку ошибок (что если пользователь ввел три слова, ввел неправильное название колонки и т.д.)
# можно такую обработку добавить
        data = pd.read_csv('data.csv', delimiter = ',') # считываем нашу таблицу с помощью pandas
        med = data[col].median() # методом колонки таблицы pandas находим медиану для выбранной колонки
        bot.send_message(message.from_user.id, "Медиана для колонки " + col + " = " + str(med)) # отправляем сообщение с найденой медианой
    else:
        # обрабатываем случай, если пользователь вызвал команду /median до того, как мы собрали информацию
        bot.send_message(message.from_user.id, "Парсинг не выполнен. Нажмите /parse чтобы это сделать")

# все то же самое, что выше только для арифметического среднего        
@bot.message_handler(commands=['mean'])
def get_mean(message):
    global parsed
    if parsed:
        col = message.text.split()
        if len(col) == 2:
            if col[1] == 'cases':
                col = 'number of daily cases'
            else:
                col = 'number of daily deaths'
        else:
            col = 'number of daily cases'
            
        data = pd.read_csv('data.csv', delimiter = ',')
        mea = data[col].mean()
        bot.send_message(message.from_user.id, "Среднее для колонки " + col + " = " + str(mea))
    else:
        bot.send_message(message.from_user.id, "Парсинг не выполнен. Нажмите /parse чтобы это сделать")

# реагируем на команду /date - выводим информацию о новых случаях в определенный день, который вводит пользователь 
@bot.message_handler(commands=['date'])
def get_date(message):
    global parsed
    if parsed: # проверяем, что парсинг состоялся
        col = message.text.split() # мы ожидаем сообщение в формате '/date Feb 02', разбиваем по пробелам
        if len(col) != 3: # топорно обрабатываем ошибку, если в разбитом сообщение не три элемента (команда, месяц и дата)
            # тут, конечно же, можно сделать более тонкую обработку случаев с помощью регулярных выражений
            bot.send_message(message.from_user.id, "Дата не указана.")
        mon = col[1] # сохраняем месяц в переменную
        day = col[2] # сохраняем день
        try:
            data = pd.read_csv('data.csv', delimiter = ',') # считываем таблицу с помощью pandas
            # выводим сообщение с информацией
            bot.send_message(message.from_user.id, f'{mon + " " + day} было зарегестрировано {data[data.date == mon + " " + day]["number of daily cases"].values[0]} случаев')
        except Exception:
            # выводим информацию об ошибке в дате
            bot.send_message(message.from_user.id, "Ошибка в дате или дата не доступна, попробуйте еще раз.")
    else:
        bot.send_message(message.from_user.id, "Парсинг не выполнен. Нажмите /parse чтобы это сделать")
    
# Обабатываем все остальные сообщения от пользователя, которые не являются командами, прописанными выше
@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    global parsed
    if not parsed: # проверяем, что парсинг не произошел
        if message.text in supported: # проверяем, что введенное сообщение является названием страны, для которой можем сделать парсинг
            try: # пытаемся выполнить парсинг
                bot.send_message(message.from_user.id, "Начинаю парсинг. Подождите...") # сообщаем пользователю, что начали работу
                
                url = f'https://www.worldometers.info/coronavirus/country/{message.text.lower()}' # переходим по ссылке, для заданной страны

                html = requests.get(url).text
                soup = bs4.BeautifulSoup(html, 'lxml')

                dates_cases = []
                cases = []
                
                # ниже привычный нам парсинг, единственное, используем str(graph) вместо graph.text,
                # почему-то heroku воспринимает атрибут объекта beautiful soup пустым
                for graph in soup.find_all('script', {'type': "text/javascript"}): # достаем информацию о новых случаях из графика
                    if 'Daily New Cases' in str(graph): 
                        dates_cases = re.findall(r'categories: \[([\w\s",]+)', str(graph))[0]
                        cases = re.findall(r'data: \[([\w,]+)', str(graph))[0]

                dates_deaths = []
                deaths = []
                # то же самое для новых зарегистрированных смертей
                for graph in soup.find_all('script', {'type': "text/javascript"}):
                    if 'Daily Deaths' in str(graph):
                        dates_deaths = re.findall(r'categories: \[([\w\s",]+)', str(graph))[0]
                        deaths = re.findall(r'data: \[([\w,]+)', str(graph))[0]
                 
                # избавляемся от "" в датах и делаем список
                dates = [date.strip('"') for date in dates_cases.split(',')]
                # заменяем возможные вхождения null на '0'
                cases = cases.replace('null', '0')
                deaths = deaths.replace('null', '0')
                cases = [int(x) for x in cases.split(',')] # генерируем списки из целых значений
                deaths = [int(x) for x in deaths.split(',')]

                with open('data.csv', 'w') as fh: # открываем файл, чтобы сохранить в него собранную информацию
                    fh.write('date,number of daily cases,number of daily deaths\n') # записываем название колонок
                    for i in range(len(dates)):
                        fh.write(f'{dates[i]},{cases[i]},{deaths[i]}\n') # записываем строки с данными для каждого ряда
                        
                parsed = True # меняем метку parsed, если парсинг успешно завершилася
                bot.send_message(message.from_user.id, "Парсинг успешно закончен. Выберите следующую команду:") # сообщаем об этом пользователю
                # рассказываем пользователю, что умеем делать с собранными данными
                bot.send_message(message.from_user.id, f'''/file - Получить файл с данными\ 
                \n/median - Посчитать медиану. После команды через пробел напишите название колонки, для которой нужно найти медиану (cases или deaths)\
                \n/mean - Посчитать среднее. После команды через пробел напишите название колонки, для которой нужно найти среднее (cases или deaths)\
                \n/date - Получить информацию по конкретному дню. После команды через пробел месяц и день в формате Feb 15. Даты меньше 10 с ведушим нулем - 01,02\
                \nДля {message.text} доступны данные в интервале {dates[0]} - {dates[-1]}''')

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