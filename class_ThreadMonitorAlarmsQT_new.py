#
from typing import Optional, Any, List, Dict
import logging
import requests
import sqlite3
import backoff
from PyQt5.QtCore import QThread
from class_SqlLiteMain import ConnectSqlDB
from telegram import ParseMode
from class_UPSAlarmHandler import UPSAlarmHandler
from class_ThreePhaseUPSAlarmHandler import ThreePhaseUPSAlarmHandler
from class_MACCAlarmHandler import MACCAlarmHandler
from class_DGUAlarmHandler import DGUAlarmHandler
from class_PortSwitchHandler import PortSwitchHandler
from class_SLASwitchHandler import SLASwitchHandler
from class_ERRORHandler import ERRORHandler
from class_ValueHandler import ValueHandler
from dictionaryAlarms import dict_interim_alarms, dict_alarms

class ThreadMonitorAlarms(QThread, ValueHandler):

    def __init__(self) -> None:
        # Запускаем у класса QThread метод init
        super().__init__()
        # Создаем переменную в которой будем хранить адрес сервера Telegram переданное при запуске Бота.
        self.url = "https://api.telegram.org/bot"
        # Создаем переменную token в которой будем хранить токен нашего бота
        self.token = ""
        # Переменная определяет интервал между опросами метода run
        self.interval_time = 10
        # Создаем экземпдяр класса UPSAlarmHandler
        self.ups_handler_alarm = UPSAlarmHandler()
        self.three_phase_ups_alarm_handler = ThreePhaseUPSAlarmHandler()
        # Создаем экземпдяр класса MACCAlarmHandler
        self.macc_handler = MACCAlarmHandler()
        self.dgu_handler = DGUAlarmHandler()
        self.switchport_handler = PortSwitchHandler()
        self.switchsla_handler = SLASwitchHandler()
        self.handler_error = ERRORHandler()

        # Записываем результат snmp опроса оборудования в список 
        self.snmp_traps: List[str] = []

    # Функция отправляет сообщение чат Ботом 
    def _sender(self, message: str) -> Optional[int]:
        try:
            with ConnectSqlDB() as sql:
                # Делаем запрос к БД получаем список chat_id пользователей
                chat_ids = sql.get_values_list_db('chat_id', chat_id='IS not null', table='Users')
        except sqlite3.IntegrityError as err:
            self.logger = logging.getLogger('class_ThreadMonitorAlarmQt')
            self.logger.exception(err)
            return None
        else:
            # Если список не пустой 
            if chat_ids:
                for id in chat_ids:
                    if isinstance(id[0], int):
                        # отправляем сообщенние вызывав метод send_message, результат записываем в переменную code_status
                        code_status = self.send_message(id[0], message) # --> int
                return code_status
        return None
    
    # Декоратор on_exception используется для повторной попытки при возникновении указанного исключения
    @backoff.on_exception(backoff.expo, 
                        (requests.exceptions.ConnectionError, 
                        requests.exceptions.Timeout),
                        raise_on_giveup = False, 
                        max_time=30,
                        #max_tries=3, 
                        logger= 'class_ThreadMonitorAlarmQt')
    # Метод отправляет ботом сообщение пользователю, принимая на вход id пользователя и текс сообщения
    def send_message(self, chat_id: int, text: str) -> Optional[int]:
        # Создаем метод для post запроса 
        method = f'{self.url}{self.token}/sendMessage'
        # Формируем параметры которые мы будем передавать при post запросе на url API
        data={"chat_id":chat_id, "text":text, "parse_mode": ParseMode.HTML}
        #
        result = requests.post(method, json=data)
        return result.status_code

    # Функция обрабатывает входящие значения из файла.
    def run(self) -> None:
        while True:
            # Если в переменной snmp_traps есть данные, то
            if self.snmp_traps:
                # Перебираем список с данными по строкам
                for line in self.snmp_traps:
                    # Вылавливаем исключение, когда при запущенном приложение мы удаляем устройство из БД
                    try:
                        # Получаем значение ip адреса вызвав метод _parse_ip
                        ip = self._parse_ip(line)
                    # Попали в исключение, значит ip адрес устройство уже удален, пропускаем все действия ниже
                    except (TypeError,AttributeError):
                        continue
                  
                # ПРОВЕРКА АВАРИЙ НА MAC&C

                    if 'TxFiber2' in line or 'TxFiber3' in line:
                        # Вызываем метод, который обрабатывает строку с параметрами MAC&C
                        message = self.macc_handler.alarm_handler(line)
                        if isinstance(message, str):
                            # Вызываем метод, который отправляет сообщение пользователю
                            code_status = self._sender(message)

                # ПРОВЕРКА НА ОШИБКИ CISCO
                    # 
                    elif 'CISCO_SNMP:REQEST_ERROR' in line:
                        message = self.handler_error.handler_sw_error(line)
                        if isinstance(message, str):
                            status_code = self._sender(message)   
                    
                    # ПРОВЕРКА НА ОШИБКИ ИБЭП

                    elif 'SNMP:REQEST_ERROR' in line:
                        message = self.handler_error.handler_ups_error(line)
                        if isinstance(message, str):
                            status_code = self._sender(message)       
                
                # ПРОВЕРКА ПАРАМЕТРОВ ДГУ

                    elif 'ДГУ' in line:
                        message = self.dgu_handler.alarm_handler(line)
                        if isinstance(message, str):
                            status_code = self._sender(message)
        
                # CISCO

                    elif 'Sla' in line:
                        message = self.switchsla_handler.alarm_handler(line)
                        if isinstance(message, str):
                           status_code = self._sender(message)
                        # Проверяем если ip адрес есть в switcherror_handler.dict_alarms['error']
                        if ip in dict_alarms['error']:
                            # Вызываем метод который принимает на вход строку с параметрами Коммутатора, возвращает сообщение
                            message = self.handler_error.inservice_handler(line)
                            if isinstance(message, str):
                                status_code = self._sender(message)

                    elif 'Port' in line:
                        message = self.switchport_handler.alarm_handler(line)
                        if isinstance(message, str):
                            # Отправляем сообщение
                            status_code = self._sender(message)
                        # Проверяем если ip адрес есть в switcherror_handler.dict_alarms['error']
                        if ip in dict_alarms['error']:
                            # Вызываем метод который принимает на вход строку с параметрами Коммутатора, возвращает сообщение
                            message = self.handler_error.inservice_handler(line)
                            if isinstance(message, str):
                                status_code = self._sender(message)

                    # ПРОВЕРКА ПАРАМЕТРОВ ТРЕХФАЗНОГО ИБП

                    elif 'Phase' in line:
                        message = self.three_phase_ups_alarm_handler.alarm_handler(line)
                        if isinstance(message, str):
                            # Отправляем сообщение
                            status_code = self._sender(message)

                # ПРОВЕРКА НА ОСТАЛЬНЫЕ АВАРИИ

                    else:
                        message = self.ups_handler_alarm.alarm_handler(line)
                        if isinstance(message, str):
                            # Отправляем сообщение
                            status_code = self._sender(message)
                        
            # Иначе, если в переменной snmp_traps нет данных, то заснуть на interval_time секунд и пропустить все операции ниже
            else:
                self.sleep(self.interval_time)
                continue
            # Создаем экземпляр класса sql
            with ConnectSqlDB() as sql:
                try:
                    # Делаем запрос к БД, Добавляем в таблицу Alarms словарь с авариями
                    sql.add_data_json_db(dict_alarms, table='Alarms')
                    sql.add_data_json_db(dict_interim_alarms, table='Interim')
                except (sqlite3.IntegrityError, sqlite3.OperationalError):
                    self.logger = logging.getLogger('class_ThreadMonitorAlarmQt')
                    self.logger.error('ThreadMonitorAlarm: функция "run". Ошибка добавления данных в БД') 
            # Устанавливаем интервал времени на который нужно заснуть 
            self.sleep(self.interval_time)

if __name__ == '__main__':
    monitor = ThreadMonitorAlarms()
    text = '16-10-2022 21:11:08 БЛП-25 (MAC&C): Низкая температура транспондера MAC&C: TxFiber2: +03 dBm; RxFiber2: -09 dBm; TempFiber2: -006 *C; TxFiber3: +02 dBm; RxFiber3: -08 dBm; TempFiber3: +008 *C.'
    print(monitor.send_message(489848468, 'Проверка'))
    #time.sleep(5)
    