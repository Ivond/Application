# coding: utf-8

import requests
import netmiko
import subprocess
import re
import logging
import sqlite3
#from queue import Queue, Empty
from pathlib import Path
from operator import itemgetter
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, error, ParseMode, Bot
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from class_TelegrambotAlarm import TelegramBotAlarmStatus
from class_ThreadSNMPAsc import ThreadSNMPAsk
from class_SqlLiteMain import ConnectSqlDB

class TelegramBot():
    def __init__(self, token):
        self.path_logs = Path(Path.cwd(), "logs", "logs_chat_bot.txt")
        # Настройка логирования
        self.logger_bot = logging.getLogger('chat_bot')
        self.logger_bot.setLevel(logging.INFO)
        fh_bot = logging.FileHandler(self.path_logs, 'w')
        formatter_bot = logging.Formatter('%(asctime)s %(name)s: %(message)s', datefmt='%d-%m-%Y %H:%M:%S')
        fh_bot.setFormatter(formatter_bot)
        self.logger_bot.addHandler(fh_bot)
        
        """Start the bot."""
        # Создаем экземпляр класса Queue(очередь)
        #self.queu = Queue()
        # Создаем экземпляр класса TelegramBotAlarmStatus передав аргумент self.queu он нужен для класса ThreadSNMPAsc,
        # который наследуется классом TelegramBotAlarmStatus
        #self.bot_status_alarm = TelegramBotAlarmStatus(self.queu)
        self.bot_status_alarm = TelegramBotAlarmStatus()
        # Переменная в которую записывается сколько пакетов было отправленно
        self.send = 0
        # Переменная в которую записывается сколько пакетов было принято
        self.recive = 0 
        # Переменная в которую записывается сколько пакетов было потеряно
        self.lost = 0
        # Переменная в которую записывается сколько пакетов было потеряно в процентном соотношении
        self.lost_percent = 0
        # Создаем переменную в которую будем записывать статистику по отправленным и полученным пакетам
        self.report = 'Данных нет'
        # Создаем переменную token в которой будем хранить токен нашего бота
        self.token = token
        # Создаем переменную в которой будем хранить адрес сервера Telegram переданное при запуске Бота.
        self.url = "https://api.telegram.org/bot"
        # Cоздадаем экземпляр класса Updater
        self.updater = Updater(self.token, use_context=True, request_kwargs={'read_timeout': 5, 'connect_timeout': 5})
        # Создаем диспетчер который будет регистрировать наши обработчики(handlers)
        self.dispatcher = self.updater.dispatcher
        # Вызываем метод add_handler, который добавляет команды, которые будет обрабатывать CommandHandler
        self.dispatcher.add_handler(CommandHandler(["start", "Help", 'close', 'Clear', 'Show', 'Status', 'ping', \
        'Alarm', 'Avtobus'], self._check_user_command))
        # Создаем структуру клавиатуры, как у нас будут располагаться кнопки
        self.reply_keyboard = [['/Alarm'], ['/Help'], ['/Status'], ['/Avtobus']]
        # Обработчик MessageHandler, который первым аргументом примет фильтры Filter.text и ~Filters.command, 
        # где символ ~ означает "не", то есть в нашем случае разрешай текст и не разрешай реагировать на команды. 
        # Вторым аргументом принимается коллбэк функция, у нас это функция echo().
        #self.dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, self.echo))
        # Start the Bot
        #try:
            #self.updater.start_polling(bootstrap_retries=5) # Запускает опрос обновлений из Telegram.
            #self.updater.idle()# Что бы код после запуска сразу не отключилс
        #except error.NetworkError:
            #raise error.NetworkError ('Отсутствует подключение к интернету')
        #except (error.Unauthorized, error.Invalidtoken):
            #raise error.Unauthorized ('Ошибка авторизации')
    
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.updater.stop()  
 
    # Метод отправляет Ботом сообщение пользователю в ответ на принятое сообщение от него.
    def echo(self, update: Update, context: CallbackContext) -> None:
        """Echo the user message."""
        update.message.reply_text(update.message.text, ParseMode.HTML)
        # Создаем атрибут question, бот получает вопрос от пользователей и записываем в атрибут question, 
        # который мы передадим на вход нашей функции по обработке ответов. 
        self.question = update.message.text
        try:
            # Создаем атрибут answer Вызываем метод reply_text передаем  полученный ответ answer
            self.answer = update.message.reply_text()
        except error.TimedOut:
            self.logger_bot.error('TelegramBot: echo Ошибка подключения к сети интерет, вышло время ожидания TimedOut')
    
    # Метод отправляет ботом сообщение пользователю
    def send_message(self, chat_id, text):
        # Создаем метод для post запроса 
        method = self.url + self.token + "/sendMessage"
        # Формируем параметры которые мы будем передавать при post запросе на url API
        data={"chat_id":chat_id, "text":text, "parse_mode":ParseMode.HTML}
        try:
            result = requests.post(method, json=data)
            return result.status_code
        except:
            self.logger_bot.error('TelegramBot: send_message Ошибка передачи сообщения, метод send_message')

    # Метод собирает статистику по количеству отправленных/полученных пакетов и сохраняет в переменную report
    def status_ping(self, data):
        self.send += int(data[0])
        self.recive += int(data[1])
        self.lost += int(data[0]) - int(data[1])
        self.lost_percent = self.lost*100/self.send
        stat = f''' 
            Отправленно: {str(self.send)},
            Получено: {str(self.recive)},
            Потери: {str(self.lost)},
            Потери в %: {str(self.lost_percent)}
            '''  
        self.report = stat

    # Метод осуществляет подключение к устройству (коммутатор), если ip адрес и команда не были переданы, то при вызове метода
    # происходит подключение и отправка команды заранее прописанные в методе.
    def _connect_device(self, ip=None, commands=None):
        if ip and commands:
            device_params = {'device_type': 'cisco_ios',
                  'ip': ip,
                  'password': '<hbcnjkm63',
                  'username': 'irkoil',
                  'secret': 'byr8ktn'}  
            try:
               ssh = netmiko.ConnectHandler(**device_params)
               show = ssh.send_command(commands)
               return show
            except:
                return 'Подключиться не удалось'
        else:
            device_params = {'device_type': 'cisco_ios',
                  'ip': '192.168.136.150',
                  'password': 'cisco',
                  'username': 'cisco',
                  'secret': 'byr8ktn'}
            try:
               ssh = netmiko.ConnectHandler(**device_params)
               show = ssh.send_command('sho inter des')
               return show
            except:
                return 'Подключиться не удалось' 

    # Метод проверяет доступность устройства посредством команды ping, ожидает ip адрес устройства
    def _ping_device(self, text):
        if len(text.split()) > 1:
            # Получаем отправленную команду, достаем ip адрес
            ip = text.split()[1]
        else: 
            return 'Команда передана не корректно'
        try:
            # Выполнить комманду Ping и записать результат в переменную result
            result = subprocess.run(['ping', ip, '-n', '5', '-l', '16'], shell=True, stdout = subprocess.PIPE, encoding = 'cp866')
            result_stat = result.stdout.split('\n')[9].strip()
            match = re.match(r'Пакетов: отправлено = (?P<send>\d+), получено = (?P<receive>\d+),', result_stat)
            report = f"Пакетов: отправлено = {match.group('send')}, получено = {match.group('receive')}"
            return report
        except:
            return 'Выполнить команду не удалось'

    # Метод проверяет если у пользователя отправившего команду /start разрешение на доступ к Боту
    def _check_user_command(self, update: Update, context: CallbackContext):
        # Получаем Имя и Фамилию
        first_name = update.message.chat.first_name
        last_name = update.message.chat.last_name
        # Если в имени пользователя присутствует фамилия в поле фамилия, то
        if last_name:
            name_user = f"{first_name} {last_name}"
        else:
            name_user = first_name
        # Получаем chat id пользователя отправившего команду
        id = update.message.chat.id
        # Подключаемся к БД
        with ConnectSqlDB() as sql_db:
            # Делаем запрос к БД на получение имени пользователя из таблицы Users
            name = sql_db.get_db('user_name', name=name_user, chat=id, table='Users')
        # Проверяем, если мы получили имя пользователя 
        if name:
            if update.message.text.lower() == '/start':
                self.star(update, context)
            elif update.message.text.lower() == '/help':
                self.help_command(update, context)
            elif update.message.text.lower() == '/close':
                self.close_keyboard(update, context)
            elif update.message.text.lower() == '/clear':
                self.clear(update, context) 
            elif update.message.text.lower() == '/status':
                self.status_alarm(update, context)
            elif update.message.text.lower().startswith('/show'):
                self.show(update, context)
            elif update.message.text.lower().startswith('/ping'):
                self.ping(update, context)
            elif update.message.text.lower() == '/alarm':
                self.active_alarms(update, context)
            elif update.message.text.lower() == '/avtobus':
                self.avtobus(update, context)
        # Иначе, если в БД нет пользователя с user_name и chat_id
        else:
            try:
                # Создаем экземпляр класса, для подключения к БД
                with ConnectSqlDB() as sql_db:
                    # Делаем запрос к БД получить никнейм пользователя ГДЕ никнейм и chat_id=None из таблицы Users
                    name = sql_db.get_db('user_name', name=name_user, chat=None, table='Users') # -> list[()]
                    # Если получили имя пользователя и отправленная команда пользователем равна /start
                    if name and update.message.text.lower() == '/start':
                        # Делаем запрос к БД на добавление chat_id пользователя в таблицу Users.
                        sql_db.add_chat_id(user_name=name[0][0], chat_id=id)
                        # Вызываем функцию кторая отвечает за команду /start
                        self.star(update, context)
            except (sqlite3.IntegrityError,sqlite3.OperationalError, sqlite3.InterfaceError):
                # TODO logging.error ошибка запроса к БД
                self.logger_bot.error('TelegramBot: _check_user_command Ошибка запроса к БД, на добаления chat_id пользователя')
              
    # Метод получает из БД аварии и возвращает список активных аварий 
    def _get_alarms(self):
        list_alarms = []
        try:
            # Создаем экземпляр класса sql_db
            with ConnectSqlDB() as sql_db:
                # Делаем запрос к БД вызываем метод get_values_list_db
                db_alarm = sql_db.get_values_list_db('data', table='Alarms') # -> dict{}
            # Проверяем, если запрос нам вернул данные
            if db_alarm:
                if db_alarm['limit_oil']:
                    # Создаем список с именем переменной list_alarms, куда добавляем аварии
                    list_alarms += list(db_alarm['limit_oil'].values())
                if db_alarm['low_voltage']:
                    # Создаем список с именем переменной list_alarms, куда добавляем аварии
                    list_alarms += list(db_alarm['low_voltage'].values())
                if db_alarm['power_alarm']:
                    # Создаем список с именем переменной list_alarms, куда добавляем аварии
                    list_alarms += list(db_alarm['power_alarm'].values())
                if db_alarm['hight_temp']:
                    # Создаем список с именем переменной list_alarms, куда добавляем аварии
                    list_alarms += list(db_alarm['hight_temp'].values())
                if db_alarm['low_temp']:
                    # Создаем список с именем переменной list_alarms, куда добавляем аварии
                    list_alarms += list(db_alarm['low_temp'].values())
                if db_alarm['low_signal_power']:
                    # Создаем список с именем переменной list_alarms, куда добавляем аварии
                    list_alarms += list(db_alarm['low_signal_power'].values())
                if db_alarm['channel']:
                    # Обращаемся к словарю словарей по ключу channel, получаем список словарей со значениями
                    # такого формата [{port:description, port:description}, {port:description,},]
                    list_dict = list(db_alarm['channel'].values())
                    for dict_item in list_dict:
                        for item in dict_item.values():
                            # Добавляем описание аварий в созданный список list_alarms
                            list_alarms.append(item)
                if db_alarm['dgu']:
                    # Обращаемся к словарю словарей по ключу dgu, получаем список словарей со значениями
                    # такого формата [{key:description, key:description}, {key:description,},]
                    list_dict = list(db_alarm['dgu'].values())
                    for dict_item in list_dict:
                        for item in dict_item.values():
                            # Добавляем описание аварий в созданный список list_alarms
                            list_alarms.append(item)
                if db_alarm['error']:
                    # Создаем список с именем переменной list_alarms, куда добавляем аварии
                    list_alarms += list(db_alarm['error'].values())
                # Вызываем метод который отсортировавывает список аварий по дате и возвращает кортеж
                string_alarms, lengh = self._sorted_alarms(list_alarms) # --> tuple()
                # Возвращаем строку с отсортированными авриями и длину списка аварий
                return string_alarms, lengh
        except (sqlite3.IntegrityError, sqlite3.OperationalError) as err:
            self.logger_bot.error(f'TelegramBot: _get_alarms Ошибка запроса к БД на получение аварий\n{err}')

    # Метод сортирует список аварии по дате и времени, принимает на вход список аварий
    def _sorted_alarms(self, list_alarms) ->tuple:
        string_alarms = ''
        for line in sorted(list_alarms, reverse=True, key=itemgetter(3,4,0,1,11,12,14,15)):
            string_alarms += f'{line}\n\n'
        return string_alarms, len(list_alarms)
    
    def star(self, update: Update, context: CallbackContext) -> None:
        """Send a message when the command /start is issued."""
        text = '''Приветсвую! Это чат Бот по мониторингу аварий. 
        Для помощи по работе с чат Ботом нажми клавишу /Help
        '''
        try:
            # Активация клавиатуры 
            update.message.reply_text(text, reply_markup=ReplyKeyboardMarkup(self.reply_keyboard, one_time_keyboard=True, resize_keyboard=True))
        except (error.TimedOut, error.BadRequest, error.InvalidToken, error.Unauthorized, error.NetworkError, error.Conflict) as err:
            self.logger_bot.error(f'TelegramBot: star Ошибка подключения к сети интерет: {err}')

    def help_command(self, update: Update, context: CallbackContext) -> None:
        """Send a message when the command /help is issued."""
        text = '''У чат Бота реализован следующий функционал:
    /Alarm - <b>получить список текущих аварий</b>
    /Status - <b>получение актуальных параметров по текущим авариям.</b>'''

        """
        /ping проверяем доступность оборудования, текст сообщения выглядит так: /ping пробел ip-адрес устройства.
        /show - если команда используется через кнопку, то предварительно настраивается ip-адрес устройства, прописывается команда, 
        вывод которой Бот будет присылать. Можно отправить эту команду без использования кнопки, текст сообщения вышлядит так:
        /show пробел ip-адрес коммутатора пробел команда show run, тогда Бот пришлет вывод этой команды
        /status - получение данных об отправленных, полученных пакетах, Бот должен использоваться совместно с функцией которая 
        мониторит доступность оборудования, т.к. данные он получает от нее.
        /clear - очистить накопленную статистику (должна использоваться совместно с функцией которая мониторит доступность оборудования)
        /close - отключить клавиатуру
        """
        try:
            update.message.reply_text(text, parse_mode = ParseMode.HTML)
        except (error.TimedOut, error.BadRequest, error.InvalidToken, error.Unauthorized, error.NetworkError, error.Conflict) as err:
            self.logger_bot.error(f'TelegramBot: help_command Ошибка подключения к сети интерет: {err}')

    # Метод убирает клавиатуру.
    def close_keyboard(self, update: Update, context: CallbackContext):
        """Send a message when the command /close is issued."""
        try:
            update.message.reply_text('Ok', reply_markup=ReplyKeyboardRemove())  
        except (error.TimedOut, error.BadRequest, error.InvalidToken, error.Unauthorized, error.NetworkError, error.Conflict) as err:
            self.logger_bot.error(f'TelegramBot: close_keyboard Ошибка подключения к сети интерет: {err}')
    
    # Метод отправляет команду show на коммутатор и возвращает результат вывода команды
    def show(self, update: Update, context: CallbackContext):
        """Send a message when the command /show is issued."""
        text = update.message.text
        if len(text.split()) > 2:
            match = re.match(r'/show +(?P<ip>[\d+\.]+) +(?P<command>.+)', text)
            ip, command = match.group('ip', 'command')
            output = self._connect_device(ip, command)
        else:
            output = self._connect_device()
        try:
            update.message.reply_text(output, ParseMode.HTML)
        # Попадаем в исключение откуда получаем код ошибки, который говорит, что запрошено слишком длинное сообщение для отправки
        except error.BadRequest as err:
            # Отправляем пользователю
            update.message.reply_text(err.message, ParseMode.HTML)
        except (error.TimedOut, error.InvalidToken, error.Unauthorized, error.NetworkError, error.Conflict) as err:
            self.logger_bot.error(f'TelegramBot: show Ошибка подключения к сети интерет: {err}')

    # Метод отправляет команду ping и возвращает результат
    def ping(self, update: Update, context: CallbackContext):
        """Send a message when the command /ping is issued."""
        text = update.message.text
        # Вызываем функцию _ping_device передаем ей ip адрес, получаем результат 
        result = self._ping_device(text)
        try:
            # Отправляем боту результат
            update.message.reply_text(result, ParseMode.HTML)
        except (error.TimedOut, error.BadRequest, error.InvalidToken, error.Unauthorized, error.NetworkError, error.Conflict) as err:
            self.logger_bot.error(f'TelegramBot: ping Ошибка подключения к сети интерет: {err}')

    # Метод отправляет пользователю статистику по доступности оборудования
    def status(self, update: Update, context: CallbackContext):
        """Send a message when the command /Status is issued."""
        try:
            update.message.reply_text(self.report, ParseMode.HTML)
        except (error.TimedOut, error.BadRequest, error.InvalidToken, error.Unauthorized, error.NetworkError, error.Conflict) as err:
            self.logger_bot.error(f'TelegramBot: status Ошибка подключения к сети интерет: {err}') 

    # Метод отправляет пользователю актуальную информацию по текущим авариям
    def status_alarm(self, update: Update, context: CallbackContext):
        """Send a message when the command /Status is issued."""
        # Отправляем сообщение что выполняется snmp опрос оборудования 
        update.message.reply_text('Выполняется...', ParseMode.HTML)
        try:
            # Вызываем у экземпляра классса bot_status_alarm метод get_active_alarms, делаем запрос активных аварий
            list_alarms = self.bot_status_alarm.get_active_alarms() # --> List[] | None
            # Если список аварий не пустой, то
            if list_alarms:
                # Вызываем метод _sorted_alarms, который сортирует список аврий по дате и возращает кортеж из строки с авариями и длины списка
                string_alarms, lenght = self._sorted_alarms(list_alarms) # -> tuple()
                # Если длина списка аварий меньше 21
                if lenght < 21:
                    # Отправляем отсортированный список аварий пользователю полностью ввиде строки 
                    update.message.reply_text(string_alarms, ParseMode.HTML) 
                else:
                    # Преобразуем отсортированную строку с авариями в список
                    alarms = string_alarms.split('\n\n') # --> list[]
                    # Отправляем список аварий по частям предварительно перепреобразовав в строку 
                    update.message.reply_text('\n\n'.join(alarms[:21]), ParseMode.HTML)
                    update.message.reply_text('\n\n'.join(alarms[21:]), ParseMode.HTML)
            else:
                message = 'Текущие аварии отсутствуют'
                update.message.reply_text(message, ParseMode.HTML)
        except (error.TimedOut, error.BadRequest, error.InvalidToken, error.Unauthorized, error.NetworkError, error.Conflict) as err:
            self.logger_bot.error(f'TelegramBot: status_alarm Ошибка подключения к сети интерет: {err}') 
    
    # Метод опрашивает по протоколу SNMP устройство и отправляет результат сообщение пользователю
    def avtobus(self, update: Update, context: CallbackContext):
        """Send a message when the command /Avtobus is issued."""
        # Отправляем сообщение что выполняется snmp опрос оборудования 
        update.message.reply_text('Выполняется...', ParseMode.HTML)
        # Создаем экземпляр класса avtobus
        avtobus = ThreadSNMPAsk()
        # Вызываем у экземпляра класса avtobus метод sc200, который опрашивает устройство и 
        # возвращает результат, который записываем в переменную result
        result = avtobus.sc200('10.184.50.201', timeout=10, flag=True)
        # Отправляем результат запроса пользователю предварительно сделав замену ip адреса на имя устройства
        update.message.reply_text(result.replace('10.184.50.201', 'ААУС Б.Тира (КП2)'), ParseMode.HTML)

    # Метод отправляет пользователю список текщих аварий
    def active_alarms(self, update: Update, context: CallbackContext):
        """Send a message when the command /Alarm is issued."""
        # Вызываем метод _get_alarms(), который возвращает кортеж из строки с отсорироваными по дате авариями и длину списка
        string_alarms, lenght = self._get_alarms() # --> tuple()
        try:
            # Проверяем если в строке есть аварии
            if string_alarms:
                # Если длина списка меньше 21
                if lenght < 21:
                    # Отправляем аварий полностью одной строкой
                    update.message.reply_text(string_alarms, ParseMode.HTML)
                # Иначе, отправляем аварий по частям
                else:
                    # Преобразуем строку с авариями в список
                    list_alarms = string_alarms.split('\n\n')
                    # Отправляем список аварий по частям предварительно перепреобразовав список в строку 
                    update.message.reply_text('\n\n'.join(list_alarms[:21]), ParseMode.HTML)
                    update.message.reply_text('\n\n'.join(list_alarms[21:]), ParseMode.HTML)
            else:
                message = 'Текущие аварии отсутствуют'
                update.message.reply_text(message, ParseMode.HTML)
        except (error.TimedOut, error.BadRequest, error.InvalidToken, error.Unauthorized, error.NetworkError, error.Conflict) as err:
            self.logger_bot.error(f'TelegramBot: active_alarms Ошибка подключения к сети интерет: {err}') 
        # Попадаем в исключение откуда получаем код ошибки, который говорит, что запрошено слишком длинное сообщение для отправки
        except error.BadRequest as err:
            # Отправляем пользователю
            update.message.reply_text(err.message)
    
    # Метод очищает накопленную статистику
    def clear(self, update: Update, context: CallbackContext):
        """Send a message when the command /clear is issued."""
        self.send=0 
        self.recive=0 
        self.lost_percent=0
        self.lost_percent=0
        try:
            update.message.reply_text('Статистика очищена', ParseMode.HTML)
        except (error.TimedOut, error.BadRequest, error.InvalidToken, error.Unauthorized, error.NetworkError, error.Conflict) as err:
            self.logger_bot.error(f'TelegramBot: clear Ошибка подключения к сети интерет: {err}') 
    
    # Метод останавливает работу экземпляр класса updater и dispatcher и возвращает True
    def disconnect(self):
        self.updater.stop()
        self.dispatcher.stop()
        return True

    # Метод проверяет запущен Бот или нет возвращает bool
    def is_running(self):
        return self.updater.running
        

if __name__ == '__main__':

    bot = TelegramBot("5412146072:AAF8TW4mDK_N7folBpjVmN1sAGG6fDlV_iU")
    bot.send_message('489848468', f'*Привет*')
    #bot.send_message(update.effective_message.chat_id, *args, **kwargs)
    #bot.run()
    #print('HJHJJHh')
    #print(bot._read_file( r'D:\Users\Ivond\Documents\Python\Application\SNMP Ask\db_alarm.json'))

    
