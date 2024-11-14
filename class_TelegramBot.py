# coding: utf-8
from __future__ import annotations
from typing import Optional, Any, List, Tuple, Dict
from unicodedata import name
from unittest import result
from PyQt5 import QtCore
from PyQt5.QtCore import QThread
import requests
import re
import logging
import sqlite3
from pathlib import Path
from operator import itemgetter
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, error, ParseMode, Bot
#from telegram.utils import request as req
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from class_TelegrambotAlarm import TelegramBotAlarmStatus
from class_ThreadSNMPAsc import ThreadSNMPAsk
from class_ClientModbus import ClientModbus
from class_SqlLiteMain import ConnectSqlDB
from dictionaryAlarms import dict_alarms, dict_interim_alarms

class TelegramBot(QThread):
    ''' 
    Для передачи данных (исключений exception) между классами ThreadTelegramBot и классом Application
    будем использовать Сигналы PyQt для связи между объектами(классами)  
    '''
    # Определяем сигнал с именем signal_error, принимает на вход исключение(Exception), которое возникло при запуске чат Бота.
    signal_error = QtCore.pyqtSignal(Exception)
    
    ''' 
    Для передачи информации об успешном подключении Чат Бота классу Application будем использовать Сигнал PyQt 
    для связи между объектами (классами) 
    '''
    # Определяем сигнал, который будет испускаться при успешном запуске Бота
    #signal_success = QtCore.pyqtSignal()
    signal_to_bot_run_successes = QtCore.pyqtSignal()

    ''''
    Для передачи информации об успешной остановке работы Чат Бота классу Application будем использовать Сигнал PyQt 
    для связи между объектами (классами)
    '''
    # Определяем сигнал, который будет испускаться при успешной остановке Бота
    signal_to_bot_stop_successes = QtCore.pyqtSignal()

    def __init__(self, token: str, helper) -> None:
        QThread.__init__(self)
        self.is_stop_bot = False

        self.path_logs = Path(Path.cwd(), "logs", "logs_chat_bot.txt")
        # Настройка логирования
        self.logger_bot = logging.getLogger('chat_bot')
        self.logger_bot.setLevel(logging.INFO)
        fh_bot = logging.FileHandler(self.path_logs, 'w')
        formatter_bot = logging.Formatter('%(asctime)s %(name)s: %(message)s', datefmt='%d-%m-%Y %H:%M:%S')
        fh_bot.setFormatter(formatter_bot)
        self.logger_bot.addHandler(fh_bot)
        
        """Start the bot."""
        # Создаем экземпляр класса TelegramBotAlarmStatus передав аргумент self.queu он нужен для класса ThreadSNMPAsc,
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
        # Переменная в которой будем хранить экземпляр класса helper class telegram.requests.QtSignalHelper (класс для работы с сигналами PyQt)
        self.helper = helper
        # Создаем переменную в которой будем хранить адрес сервера Telegram переданное при запуске Бота.
        self.url = "https://api.telegram.org/bot"
        # Cоздадаем экземпляр класса Updater
        self.updater = Updater(self.token, use_context=True, request_kwargs={'read_timeout': 5, 'connect_timeout': 5, 'helper': self.helper})
        # Создаем диспетчер который будет регистрировать наши обработчики(handlers)
        self.dispatcher = self.updater.dispatcher
        # Вызываем метод add_handler, который добавляет команды, которые будет обрабатывать CommandHandler
        self.dispatcher.add_handler(CommandHandler(["start", "Help", 'close', 'Clear', 'Show', 'Status', 'ping', \
        'Alarm', 'Avtobus', 'delete'], self._check_user_command))
        # Создаем структуру клавиатуры, как у нас будут располагаться кнопки
        self.reply_keyboard = [['/Alarm'], ['/Help'], ['/Status'], ['/Avtobus']]
        # Обработчик MessageHandler, который первым аргументом примет фильтры Filter.text и ~Filters.command, 
        # где символ ~ означает "не", то есть в нашем случае разрешай текст и не разрешай реагировать на команды. 
        # Вторым аргументом принимается коллбэк функция, у нас это функция echo().
        #self.dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, self.echo))
        #try:
        #self.updater.start_polling(bootstrap_retries=5) # Запускает опрос обновлений из Telegram.
            #self.updater.idle()# Что бы код после запуска сразу не отключилс
        #except error.NetworkError:
            #raise error.NetworkError ('Отсутствует подключение к интернету')
        #except (error.Unauthorized, error.Invalidtoken):
            #raise error.Unauthorized ('Ошибка авторизации')
        
    
    def __enter__(self) -> TelegramBot:
        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        self.updater.stop() 

    # Start the Bot
    # Метод запускает чат Бот в отдельном потоке
    def run(self) -> None:
        # Переводим флаг в False - бот отстановлен
        self.is_stop_bot = False
        # Start the Bot
        while True:
            # Если updater не запущен
            if not self.is_running():
                try:
                    # Запускает опрос обновлений из Telegram.
                    self.updater.start_polling(bootstrap_retries=5) 
                    # Испускаем сигнал об успешном подключении
                    self.signal_to_bot_run_successes.emit()
                except (error.TimedOut, error.BadRequest, error.NetworkError) as err:
                    # Испускаем сигнал, передаем тип ошибки err
                    self.signal_error.emit(err)
                    # Останавливаем работу updater
                    self.disconnect()
                    # Возвращаем None
                    return None
                except (error.InvalidToken, error.Unauthorized) as err:
                    # Испускаем сигнал, передаем тип ошибки err
                    self.signal_error.emit(err)
                    # Останавливаем работу updater
                    self.disconnect()
                    # Что бы остановить цикл while используем return
                    return None
            if self.is_stop_bot:
                # Останавливаем работу чат Бота
                self.disconnect()
                # Переводим флаг в False, что бы цикл не выполнял эту ветку событий
                self.is_stop_bot = False
                # Испускаем сигнал об успешной остановке бота
                self.signal_to_bot_stop_successes.emit()
                # Что бы остановить цикл while используем return
                return None
            self.sleep(1) 

    # Метод отправляет Ботом сообщение пользователю в ответ на принятое сообщение от него.
    #def echo(self, update: Update, context: CallbackContext[List[str]]) -> None:
        #"""Echo the user message."""
       #update.message.reply_text(update.message.text, ParseMode.HTML)
        # Создаем атрибут question, бот получает вопрос от пользователей и записываем в атрибут question, 
        # который мы передадим на вход нашей функции по обработке ответов. 
        #self.question = update.message.text
        #try:
            # Создаем атрибут answer Вызываем метод reply_text передаем  полученный ответ answer
            #self.answer = update.message.reply_text()
        #except error.TimedOut:
            #self.logger_bot.error('TelegramBot: echo Ошибка подключения к сети интерет, вышло время ожидания TimedOut')
        #return None
    
    # Метод отправляет ботом сообщение пользователю
    def send_message(self, chat_id: int, text: str) -> Optional[int]:
        # Создаем метод для post запроса 
        method = f'{self.url}{self.token}/sendMessage'
        # Формируем параметры которые мы будем передавать при post запросе на url API
        data={"chat_id":chat_id, "text":text, "parse_mode":ParseMode.HTML}
        try:
            result = requests.post(method, json=data)
        except requests.exceptions.ConnectionError as err:
            self.logger_bot.exception(err)
            self.logger_bot.error('TelegramBot: send_message Ошибка передачи сообщения')
        else:
            return result.status_code
        return None

    # Метод проверяет если у пользователя отправившего команду /start разрешение на доступ к Боту
    def _check_user_command(self, update: Update, context: CallbackContext) -> None:
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
            name = sql_db.get_db('user_name', user_name=name_user, chat_id=id, table='Users')
        # Проверяем, если мы получили имя пользователя 
        if name:
            if update.message.text.lower() == '/start':
                self.star(update, context)
            elif update.message.text.lower() == '/help':
                self.help_command(update, context)
            elif update.message.text.lower() == '/close':
                self.close_keyboard(update, context)
            #elif update.message.text.lower() == '/clear':
                #self.clear(update, context) 
            elif update.message.text.lower() == '/status':
                self.status_alarm(update, context)
            #elif update.message.text.lower().startswith('/show'):
                #self.show(update, context)
            #elif update.message.text.lower().startswith('/ping'):
                #self.ping(update, context)
            elif update.message.text.lower() == '/alarm':
                self.active_alarms(update, context)
            elif update.message.text.lower() == '/avtobus':
                self.avtobus(update, context)
            elif update.message.text.lower().startswith('/delete'):
                self.delete(update, context)
        # Иначе, если в БД нет пользователя с user_name и chat_id
        else:
            try:
                # Создаем экземпляр класса, для подключения к БД
                with ConnectSqlDB() as sql_db:
                    # Делаем запрос к БД получить никнейм пользователя ГДЕ никнейм и chat_id=ISNULL из таблицы Users
                    name = sql_db.get_db('user_name', user_name=name_user, chat_id='ISNULL', table='Users') # -> list[()]
                    # Если получили имя пользователя и отправленная команда пользователем равна /start
                    if name and update.message.text.lower() == '/start':
                        # Делаем запрос к БД на добавление chat_id пользователя в таблицу Users.
                        sql_db.add_chat_id(user_name=name[0], chat_id=id)
                        # Вызываем функцию кторая отвечает за команду /start
                        self.star(update, context)
            except (sqlite3.IntegrityError,sqlite3.OperationalError, sqlite3.InterfaceError):
                # TODO logging.error ошибка запроса к БД
                self.logger_bot.error('TelegramBot: _check_user_command Ошибка запроса к БД, на добаления chat_id пользователя')
        return None
          
    # Метод получает из БД аварии и возвращает список активных аварий 
    def _get_alarms(self) -> Optional[Tuple[str, int]]:
        list_alarms: List[str] = []
        # Создаем экземпляр класса sql_db
        with ConnectSqlDB() as sql_db:
            # Делаем запрос к БД вызываем метод get_values_dict_db
            db_alarm = sql_db.get_values_dict_db('data', table='Alarms') # -> dict{}
        # Проверяем, если запрос нам вернул данные
        if db_alarm:
            # Генератор списков аварий
            ls = [list(dic.values()) for name_alarm, dic in db_alarm.items() if list(dic.values()) and (name_alarm != 'date' and name_alarm != 'channel')]
            # Перебираем вложенный список списков
            for line in ls:
                # Объединяем списки в один список с авариями
                list_alarms += line
            if db_alarm['channel']:
                # Обращаемся к словарю словарей по ключу channel, получаем список словарей со значениями
                # такого формата [{port:description, port:description}, {port:description,},]
                list_dict = list(db_alarm['channel'].values())
                for dict_item in list_dict:
                    for item in dict_item.values():
                        # Добавляем описание аварий в созданный список list_alarms
                        list_alarms.append(item)
            # Вызываем метод который отсортировавывает список аварий по дате и возвращает кортеж
            string_alarms, lengh = self._sorted_alarms(list_alarms) # --> tuple()
            # Возвращаем строку с отсортированными авриями и длину списка
            return string_alarms, lengh
        return None

    # Метод сортирует список аварии по дате и времени, принимает на вход список аварий
    def _sorted_alarms(self, list_alarms: List[str]) -> Tuple[str, int]:
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
        return None

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
        return None

    # Метод убирает клавиатуру.
    def close_keyboard(self, update: Update, context: CallbackContext) -> None:
        """Send a message when the command /close is issued."""
        try:
            update.message.reply_text('Ok', reply_markup=ReplyKeyboardRemove())  
        except (error.TimedOut, error.BadRequest, error.InvalidToken, error.Unauthorized, error.NetworkError, error.Conflict) as err:
            self.logger_bot.error(f'TelegramBot: close_keyboard Ошибка подключения к сети интерет: {err}')
        return None

    # Метод отправляет пользователю актуальную информацию по текущим авариям
    def status_alarm(self, update: Update, context: CallbackContext) -> None:
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
        return None
    
    # Метод опрашивает по протоколу SNMP устройство и отправляет результат сообщение пользователю
    def avtobus(self, update: Update, context: CallbackContext) -> None:
        """Send a message when the command /Avtobus is issued."""
        # Отправляем сообщение что выполняется snmp опрос оборудования 
        #update.message.reply_text('Выполняется...', ParseMode.HTML)
        # Создаем экземпляр класса avtobus
        snmp = ThreadSNMPAsk()
        client_modbus = ClientModbus()
        # Вызываем у экземпляра класса avtobus метод sc200, который опрашивает устройство и 
        # возвращает результат, который записываем в переменную result
        result_snmp = snmp.sc200('10.184.50.201', timeout=10, block=True).split()
        result = f'''
<b>Входное напряжение:</b> {result_snmp[6]} V
<b>Напряжение АКБ:</b> {result_snmp[9]} V 
                '''.strip()
        result_modbus = client_modbus.get_params('10.184.50.200')



        message = f'''
    {result} {result_modbus}
    '''
        if isinstance(message, str):
            # Отправляем результат запроса пользователю предварительно сделав замену ip адреса на имя устройства
            #update.message.reply_text(result.replace('10.184.50.201', 'ААУС Б.Тира (КП2)'), ParseMode.HTML)
            update.message.reply_text(message, ParseMode.HTML)
        return None

    # Метод отправляет пользователю список текщих аварий
    def active_alarms(self, update: Update, context: CallbackContext) -> None:
        """Send a message when the command /Alarm is issued."""
        # Вызываем метод _get_alarms(), который возвращает кортеж из строки с отсорироваными по дате авариями и длину списка
        params = self._get_alarms() # --> tuple()
        if isinstance(params, tuple):
            string_alarms, lenght = params
        try:
            # Если строка аврий не пустая
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
        return None
    
    # Метод получает id (индентификатор сообщения) из строки
    def _parse_id(self, line: str) -> Optional[str]:
        match = re.match(r'.+ ID:(?P<id>\d*)', line)
        if match:
            id = match.group('id')
            return id
        return None
    
    # Метод удаляет из списка запись об аварии, которая уже не актуальна по тем или иным причинам  
    def delete(self, update: Update, context: CallbackContext) -> None:
        """Send a message when the command /delete is issued."""
        # Получаем номер ID сообщения 
        id = update.message.text.lstrip('/delete ')
        if int(id) <= 4000:
            # Если метод вернул нам True, значит запись удалена из словаря аварий
            if self._remove_note_from_dict(id):
                # Отправляем сообщение, что запись с аварией успешно удалена
                update.message.reply_text('Запись удалена')
            else:
                # Отправляем сообщение, что запись с аварией успешно удалена
                update.message.reply_text(f'Записи c ID:{id} нет в списке')
        else:
            # Если метод вернул нам True, значит запись удалена из словаря аварий
            if self._remove_switch_note_from_dict(id):
                # Отправляем сообщение, что запись с аварией успешно удалена
                update.message.reply_text('Запись удалена')
            else:
                # Отправляем сообщение, что запись с аварией успешно удалена
                update.message.reply_text(f'Записи c ID:{id} нет в списке')

    # Метод удаляет запись из словаря аварий
    def _remove_note_from_dict(self, id: str):
        for name_alarm, dic in dict_alarms.items():
            for ip, line in dic.items():
                if isinstance(line, str):
                    # Вызываем метод, который возвращает номер id из сообщения
                    id_message = self._parse_id(line) 
                    # Если значение переменной строка
                    if isinstance(id_message, str) and id_message == id:
                        # Подключаемся к БД
                        with ConnectSqlDB() as sql:
                            # Удаляем запись из словаря
                            del dict_alarms[name_alarm][ip]
                            if name_alarm == 'power_alarm':
                                del dict_alarms['date'][ip]
                            # Делаем запрос к БД, добавляем словарь с обновленными данными
                            sql.add_data_json_db(dict_alarms, table='Alarms')
                            # если метод get вернет нам значение
                            if dict_interim_alarms[name_alarm].get(ip):
                                # Удаляем запись из словаря
                                del dict_interim_alarms[name_alarm][ip]
                                # Делаем запрос к БД, добавляем словарь с обновленными данными
                                sql.add_data_json_db(dict_interim_alarms, table='Interim')
                        return True
        return False
                                      
    # Метод удаляет запись из словаря аварий
    def _remove_switch_note_from_dict(self, id: str):
        for name_alarm, dic in dict_alarms.items():
            for ip, line in dic.items():
                # Если название аварии равно channel ИЛИ sla
                if name_alarm == 'channel' or name_alarm == 'sla':
                    for port, note in line.items():
                        # Вызываем метод, который возвращает номер id из сообщения
                        id_message = self._parse_id(note)
                        # Если значение переменной строка
                        if isinstance(id_message, str) and id_message == id:
                            # Удаляем запись из словаря
                            del dict_alarms[name_alarm][ip][port]
                            return True
        return False

    # Метод останавливает работу экземпляр класса updater и dispatcher и возвращает True
    def disconnect(self) -> bool:
        self.updater.stop()
        self.dispatcher.stop()
        return True

    # Метод проверяет запущен Бот или нет возвращает bool
    def is_running(self) -> bool:
        isrunning: bool = self.updater.running
        return isrunning
        

if __name__ == '__main__':
    pass


    
