#
import time
import logging
import sqlite3
from pathlib import Path
from snmp import Manager
#from snmp import exceptions
from snmp.exceptions import Timeout
from snmp.v1.exceptions import NoSuchName
# Импортируем классс QThread отвечающий за многопоточность в PYQT
from PyQt5.QtCore import QThread
from class_SqlLiteMain import ConnectSqlDB

class ThreadSNMPSwitch(QThread):
    def __init__(self):
        # Запускаем у класса QThread метод init
        QThread.__init__(self)

         # Настройка логирования
        self.path_logs = Path(Path.cwd(), "logs", "logs_snmp_switch.txt")
        self.logger_snmp = logging.getLogger('snm_switch')
        self.logger_snmp.setLevel(logging.INFO)
        fh_logs = logging.FileHandler(self.path_logs, 'w')
        formatter_logs = logging.Formatter('%(asctime)s %(name)s %(levelname)s: %(message)s', datefmt='%d-%m-%Y %H:%M:%S')
        fh_logs.setFormatter(formatter_logs)
        self.logger_snmp.addHandler(fh_logs)

        # Переменная определяет время между запросами цикла while
        self.interval_time = 5
        #
        self.snmp_switch_trap = []
        # Cisco
        self.ifOperStatus = '1.3.6.1.2.1.2.2.1.8.' # (up(1), down(2), testing(3))
        self.ifOutOctets = '1.3.6.1.2.1.2.2.1.16.' # ifOutOctets
        self.ifInOctets = '1.3.6.1.2.1.2.2.1.10.' # ifInOctets

    ''' 
    GetRequest - запрос к агенту от менеджера, используемый для получения значения одной или нескольких переменных.
    GetNextRequest - запрос к агенту от менеджера, используемый для получения следующего в иерархии значения переменной.
    '''
    # Метод делает запрос по протоколу SNMP, принимает на вход ip и набор oids для определенного типа устройства.
    def get_request(self, ip, oids, flag, timeout, next):
        if flag:
            self.manager = Manager(b'public', version=1, port=161)
        try:
            out = self.manager.get(ip, *oids, next=next, timeout=timeout)
            if flag:
                self.manager.close()
            return out
        except Timeout:
            # Подставляем дату(перепреобразовав в нужный формат) и ip адрес
            error = f"{time.strftime('%d-%m-%Y %H:%M:%S', time.localtime())} {ip} CISCO_SNMP:REQEST_ERROR"
            # Логирование, записывает в файл logs_snmp_ask.txt
            self.logger_snmp.info(f'Ошибка Timeout - не получен ответ от устройства {ip}')
           # Если flag истина, то закрываем SNMP поток. 
            if flag:
                self.manager.close()
            return error
        except NoSuchName as err:
            # Подставляем дату(перепреобразовав в нужный формат) и ip адрес
            error = f"{time.strftime('%d-%m-%Y %H:%M:%S', time.localtime())} {ip} SNMP:REQEST_ERROR"
            self.logger_snmp.info(f'Ошибка NoSuchName - не существующая переменная {err}: {ip}')
            # Если flag истина, то закрываем SNMP поток. 
            if flag:
                self.manager.close()
            return error
        except AttributeError as err:
            # Подставляем дату(перепреобразовав в нужный формат) и ip адрес
            error = f"{time.strftime('%d-%m-%Y %H:%M:%S', time.localtime())} {ip} SNMP:REQEST_ERROR"
            self.logger_snmp.info(f'Ошибка AttributeError - SNMP Manager не запущен, в запросе не передан flag=True: {ip}')
            # Если flag истина, то закрываем SNMP поток. 
            if flag:
                self.manager.close()
            return error
        except OSError as err:
            # Если flag истина, то закрываем SNMP поток. 
            if flag:
                self.manager.close()
            return str(err)

    def cisco(self, ip, port, timeout=10, next = True, flag = False):
        #
        items = []
        # Т.к. значение index которое необходимо передать для запроса на один меньше значения порта проводим корректировку 
        index =str(int(port)-1)
        # Формируем список запроса из OID
        oids = [self.ifOutOctets+index, self.ifInOctets+index, self.ifOperStatus+index]
        # Делаем запрос GETNEX получаем список данных типа snmp.types.VarBind
        out = self.get_request(ip, oids, flag, timeout, next)
        # Проверяем, что тип переменной out список
        if type(out) is list:
            for var_bind in out:
                # Используем метод values, получаем из VarBind данные типа snmp.types.OCTET_STRING, значение в байтах
                snmp_octet_string = var_bind.values
                # Если получили значение рано 1, значит статус порта UP
                if snmp_octet_string[-1].value == 1:
                    items.append('Up')
                # Если получили значение 2, значит статус порта DWN
                elif snmp_octet_string[-1].value == 2:
                    items.append('Down')
                else:
                    # Вызываем метод traffic_count, метод возвращает текущее количество трафика на порту 
                    traffic = self.traffic_count(ip, port, snmp_octet_string)
                    # Добавляем полученное значение в список items
                    items.append(traffic)
            # Подставляем дату(перепреобразовав в нужный формат) и ip адрес
            result = f"{time.strftime('%d-%m-%Y %H:%M:%S', time.localtime())} {ip} Port: {port}; OutOctets: {items[1]}; OperStatus: {items[2]}; OutOctets: {items[0]}" 
            return result
        else:
            return out
    
    # Метод вычисляет количество трафика на порту
    def traffic_count(self, ip_addr, port, snmp_octet_string):
        if self.ifInOctets in snmp_octet_string:
            # Преобразуем полученное байтовое значение snmp_octet_string в строковое
            in_octets = snmp_octet_string[-1].value
            with ConnectSqlDB() as sql:
                # Делаем запрос к БД получаем список кортежа из которого получаем количество трафика 
                in_octets_later = sql.get_db('traffic_in', ip=ip_addr, port=port, table='Ports')[0][0]
            if in_octets_later:
                # Вычисляем количества трафика на порту отняв текущее значение от предыдущего
                bit_sec = in_octets - in_octets_later
                # Делаем запрос к БД таблица Ports обновляем значение количества входящего трафика
                sql.add_traffic('traffic_in', ip=ip_addr, port=port, traffic=in_octets)
                traffic = self.pretty_out_counters(bit_sec) # -> int
                # Возвращаем значение количества трафика
                return traffic
            else:
                # Делаем запрос к БД таблица Ports добавляем значение количества трафика
                sql.add_traffic('traffic_in', ip=ip_addr, port=port, traffic=in_octets)
                return in_octets
        elif self.OutOctets in snmp_octet_string:
            # Преобразуем полученное байтовое значение snmp_octet_string в строковое
            out_octets = snmp_octet_string[-1].value
            with ConnectSqlDB() as sql:
                # Делаем запрос к БД получаем список кортежа из которого получаем количество трафика 
                out_octets_later = sql.get_db('traffic_out', ip=ip_addr, port=port, table='Ports')[0][0]
            if out_octets_later:
                # Вычисляем количества трафика на порту отняв текущее значение от предыдущего
                bit_sec = out_octets - out_octets_later
                # Делаем запрос к БД таблица Ports обновляем значение количества входящего трафика
                sql.add_traffic('traffic_out', ip=ip_addr, port=port, traffic=out_octets)
                traffic = self.pretty_out_counters(bit_sec) # -> int
                # Возвращаем значение количества трафика
                return traffic
            else:
                # Делаем запрос к БД таблица Ports добавляем значение количества трафика
                sql.add_traffic('traffic_out', ip=ip_addr, port=port, traffic=out_octets)
                return out_octets

    # Метод преобразует значение из бит/c в Кбит/c или Мбит/c 
    def pretty_out_counters(self, bit_sec):
        mbs = bit_sec // 10**6
        if mbs >=1:
            return f'{mbs} Mbs'
        kbs = bit_sec // 10**3
        if kbs >=1:
            return f'{kbs} Kbs'
        else:
            return f'{bit_sec} bs'




    # Метод запускает SNMP опрощик
    def run(self):
        while True:
            with Manager(b'public', version=1) as self.manager:
                # Создаем переменную в которую будем сохранять результаты snmp
                self.snmp_switch_trap = []
                try:
                    # Создаем экземпляр класса
                    with ConnectSqlDB() as sql:
                        # Делаем запрос к БД, получить список значений ip_addr и port из таблицы Ports
                        data_base = sql.get_values_list_db('ip_addr', 'port', table='Ports')
                    if data_base:
                        # Перебираем данные словаря по ключам
                        for ip, port in data_base:
                            # Вызываем метод forpost передавая ему ip адрес устройства
                            result = self.cisco(ip, port)
                            # Добавляем результат в список snmp_switch_trap
                            self.snmp_switch_trap.append(result)
                    #
                    self.sleep(self.interval_time)
                #
                except (sqlite3.IntegrityError, sqlite3.OperationalError):
                    self.logger_snmp.error("Ошибка запроса из БД: sql.get_values_list_db('key', 'ip', table='Devices')" )

    # Метод останавливает работу SNMP Manager-а
    def snmp_stop(self):
        try:
            self.manager.close()
        except AttributeError:
            pass

if __name__ == '__main__':
    snmp = ThreadSNMPSwitch()
    print(snmp.cisco('10.0.31.3', 4, flag=True))
    snmp.start()
