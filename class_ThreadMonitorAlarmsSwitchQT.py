#
import re
#import os
import json
import time
import logging
import requests
import sqlite3
from pathlib import Path
from PyQt5.QtCore import QThread
from datetime import datetime
from class_SqlLiteMain import ConnectSqlDB

class ThreadMonitorAlarmsSwitch(QThread):
    def __init__(self):
        # Запускаем у класса QThread метод init
        QThread.__init__(self)
        # Настройка логирования
        self.path_logs = Path(Path.cwd(), "logs", "logs_monitor_alarm_switch.txt")
        self.logger_alarm_switch = logging.getLogger('monitor_alarm_switch')
        self.logger_alarm_switch.setLevel(logging.INFO)
        fh_alarm = logging.FileHandler(self.path_logs, 'w')
        formatter_alarm = logging.Formatter('%(asctime)s %(name)s: %(message)s', datefmt='%d-%m-%Y %H:%M:%S')
        fh_alarm.setFormatter(formatter_alarm)
        self.logger_err.addHandler(fh_alarm)

        # Создаем переменную в которой будем хранить адрес сервера Telegram переданное при запуске Бота.
        self.url = "https://api.telegram.org/bot"
        # Создаем переменную token в которой будем хранить токен нашего бота
        self.token = ""
        # Переменная определяет интервал между опросами метода run
        self.interval_time = 5
        # Значение количества проверок перед отправкой сообщения
        self.num = 3

        # Создаем экземпляр класса sql
        with ConnectSqlDB() as sql:
            try:
                # Делаем запрос к БД и получаем словарь с данными (дата и время возникновения аварий)
                self.dict_messages = sql.get_values_list_db('data', table='Switch')
            except (sqlite3.IntegrityError, sqlite3.OperationalError, TypeError):
                self.logger_err.error("Ошибка запроса из БД: sql.get_values_list_db('data', table='Switch')")
                # Записываем значения аврий в словарь
                self.dict_messages = {'power_alarm':{},
                                    'low_voltage':{},
                                    'limit_oil':{},
                                    'hight_temp':{},
                                    'low_temp':{},
                                    'low_signal_power':{},
                                    'date':{}
                                    }
    
