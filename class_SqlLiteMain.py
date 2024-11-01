#
from __future__ import annotations
from typing import Tuple, Union, Dict, Any, List, Optional
import sqlite3
from pathlib import Path
import json
import time

class ConnectSqlDB:

    def __init__(self) -> None:
        self.path_sql_db = Path(Path.cwd(), "Resources", "chatbot.db")
        # Указываем где расположен файл с БД
        #self.path_sql_db = r'C:\inetpub\wwwroot\ApplicationWeb\Resources\chatbot.db'
        # Первое что мы должны сделать создать соединение с БД, указав путь к файлу:
        # timeout - сколько секунд соединение должно ждать, прежде чем поднять сигнал OperationalError, 
        # когда таблица заблокирована, по умолчанию 5 сек.
        self.conn = sqlite3.connect(self.path_sql_db, timeout=10)
        #
        self.cursor = self.conn.cursor()
        # Включаем внешние ключи в базе данных SQLite командой PRAGMA
        command = 'PRAGMA foreign_keys=on'
        self.cursor.execute(command)
        # Подтверждаем действие
        self.conn.commit()
    
    def __enter__(self) -> ConnectSqlDB:
        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        self.conn.close() 

    # Метод добавляет данные в БД
    def add_db(self, **kword: Union[str, int]) -> None:
        # Строка для добавления параметров (ключ словаря)
        key_string = ''
        # Строка для добавления ? знаков 
        line = ''
        # Кортеж для добавления значений (значения в словаре)
        tuple_values: Tuple[Union[str, int], ...] = ()
        for key, value in kword.items():
            # Если ключ не равен table
            if key != 'table':
                    key_string += f'{key},'
                    line += '?, '
                    tuple_values += (value,)
        # Удаляем в конце строки запятую и перезаписываем значение
        key_string = key_string.rstrip(',')
        # Удалеям в конце строки запятую и перезаписываем значение
        line = line.rstrip(', ')
        # Формируем запрос: Добавить в таблицу Ports значения ip_addr, port, description, provider
        query = "INSERT INTO {} ( {} ) VALUES ( {} )".format(kword['table'], key_string, line)
        # Делаем запрос к БД на добавление данных в таблицу Ports, передаем запрос query в который подставляем kword аргументы 
        self.cursor.execute(query, tuple_values)
        # Подтверждаем действие
        self.conn.commit()
        
    # Метод заменяет значения в таблице на полученные от пользователя
    def replace_val_db(self, **kword: Union[str, int, float]) -> None:
        # Строка для добавления параметров (ключ словаря)
        key_string = ''
        # Строка для добавления ? знаков 
        line = ''
        # Кортеж для добавления значений (значения в словаре)
        tuple_values: Tuple[Union[str, int, float], ...] = ()
        for key, value in kword.items():
            # Если ключ не равен table
            if key != 'table':
                    key_string += f'{key},'
                    line += '?, '
                    tuple_values += (value,)
        # Удаляем в конце строки запятую и перезаписываем значение
        key_string = key_string.rstrip(',')
        # Удалеям в конце строки запятую и перезаписываем значение
        line = line.rstrip(', ')
        # Формируем запрос: Заменить данные в таблице, подставляя в запрос значение: 
        # строку key_string и line из ключевых аргументов, которые передал пользователь
        query = "Replace INTO {} ( {} ) VALUES ( {} )".format(kword['table'], key_string, line)
        # Делаем запрос к БД на замену значений в таблице, передаем запрос query и кортеж со значениями 
        self.cursor.execute(query, tuple_values)
        # Подтверждаем действие
        self.conn.commit()

    # Метод добавляет chat_id для имени пользователя у которого ячейка чат id не заполнена
    def add_chat_id(self, **kword: Union[str, int]) -> None:
        # Добавить значение chat_id в таблицу "Users" ГДЕ user_name = kword['user_name'] И chat_id = None 
        query = "UPDATE Users set chat_id = ? WHERE user_name = ? and chat_id ISNULL"
        # Делаем запрос к БД на обнавление данных в таблице Users, передаем запрос query в который подставляем kword аргументы 
        self.cursor.execute(query, (kword['chat_id'], kword['user_name']))
        # Подтверждаем действия
        self.conn.commit()
    
    # Метод добавляет количество трафика в таблицу Ports 
    def add_traffic(self, value: str, **kword: Union[str, int]) -> None:
        # Добавить значение traffic в таблицу "Ports" ГДЕ ip_addr= kword['ip'] И port = kword['port'] 
        query = "UPDATE Ports set {} = ? WHERE ip_addr = ? and port = ?".format(value)
        # Делаем запрос к БД на обнавление данных в таблице Ports, передаем запрос query в который подставляем kword аргументы 
        self.cursor.execute(query, (kword['traffic'], kword['ip'], kword['port']))
        # Подтверждаем действия
        self.conn.commit()

    def get_join_data(self, *args: str) -> List[Tuple[str, Optional[int], Optional[int]]]:
        # Формируем запрос, получить данные из таблиц Devices И Ports ip адрес которых равен значению
        query = "SELECT ip_addr, port, sla FROM Devices join Ports ON Devices.ip = ? AND Ports.ip_addr = ?"
        # Делаем запрос к БД на получение данных передав запрос query в который подставляем kword аргументы
        list_tuple_data = self.cursor.execute(query, (args[0],args[0])).fetchall()# --> list[(),]
        return list_tuple_data

    # Метод удаляет пользователя из БД
    def del_db(self, **kword: Union[str, int]) -> None:
        # Строка для добавления параметров (ключ словаря)
        key_string = ''
        # Кортеж для добавления значений (значения в словаре)
        tuple_values: Tuple[Union[str, int], ...] = ()
        for key, value in kword.items():
            # Если ключ не равен table
            if key != 'table':
                    key_string += f'{key} = ? and '
                    tuple_values += (value,)
        # Удаляем в конце строки запятую и перезаписываем значение
        key_string = key_string.rstrip('and ')
        # Формируем запрос: Удалить значение из таблицы,  подставляя в запрос строку key_string из 
        # ключевых аргументов и кортеж значений, которые передал пользователь
        query = "DELETE FROM {} WHERE {}".format(kword['table'], key_string)
        # Делаем запрос к БД на удаление данных из таблицы, передаем запрос query и кортеж  
        self.cursor.execute(query, tuple_values)
        # Подтверждаем действие
        self.conn.commit()

    # Метод делает запрос к БД, возвращает кортеж со значением  
    def get_db(self, *args: str, **kword: Union[str, int]) -> Tuple[Union[str, int, None], ...]:
        # Формируем пустую строку и запсываем ее в переменную line
        line = ''
        for arg in args:
            line += f"{arg},"
        line = line.rstrip(',')
        string = ''
        tuple_values: Tuple[Union[str, int], ...] = ()
        #
        for key, value in kword.items():
            if key != 'table':
                if value == 'ISNULL':
                    string += f'{key} {value} and '
                else:
                    string += f'{key} = ? and '
                    tuple_values += (value,)
        string = string.rstrip('and ')
        # Формируем запрос: Получить значение из таблицы, подставляя в запрос строку line из 
        # позиционных аргументов (args) и строку string из ключевых аргументов, которые передал пользователь
        query = "SELECT {} FROM {} WHERE {}".format(line, kword['table'], string)
        # Делаем запрос к БД на получение данных передав строку запроса в которую подставляем kword аргументы
        answer: Tuple[Union[str, int, None]] = self.cursor.execute(query, tuple_values).fetchone() # --> tuple(values,)
        return answer
    
    # Метод делает запрос к БД, возвращает список со значениями
    def get_values_list_db(self, *args: str, **kword: Union[str, int]) -> List[Tuple[Union[str, int, None], ...]]:
        # Формируем пустую строку и запсываем ее в переменную line
        line = ''
        # Перебираем позиционные аргументы (args) переданные пользователем и добавляем их в строку через запятую
        for arg in args:
            line += f"{arg},"
        # Удаляем запятую в конце строки 
        line = line.rstrip(',')
        # Если получили ключевые аргументы
        if kword and len(kword) > 1:
            # Формируем пустую строку в которую будем добавлять значения
            values = ''
            # Пернбираем через цикл ключ и значения в словаре
            for key, value in kword.items():
                # Если key не равен значению table
                if key != 'table':
                    if value == 'IS not null':
                        # Добавляем полученные значения key, value в строку 
                        values += f'{key} {value} and '
                    else:
                       values += f'{key} = "{value}" and ' 
            # Удаляем в конце строки значение and
            values = values.rstrip('and ')
            # Формируем запрос: Получить значение из таблицы, подставляя в запрос строку line из 
            # позиционных аргументов (args) и строку values из ключевых аргументов, которые передал пользователь
            query = "SELECT {} FROM {} WHERE {}".format(line, kword['table'], values)
        else:
            # Формируем запрос: Получить данные из таблицы, подставляя в запрос строку line из 
            # позиционных (args) аргументов, которые передал пользователь
            query = "SELECT {} FROM {}".format(line, kword['table'])
        # Делаем запрос к БД на получение данных передав запрос query
        self.cursor.execute(query)
        # Получаем список кортежей с данными, которые нам нужны
        return self.cursor.fetchall() # --> list[(),()]
        
    # Метод делает запрос к БД на получение данных, возвращает словарь
    def get_values_dict_db(self, *args: str, **kword: str) -> Dict[str, Any]:
        # Формируем пустую строку и запсываем ее в переменную line
        line = ''
        # Перебираем позиционные аргументы (args) переданные пользователем и добавляем их в строку через запятую
        for arg in args:
            line += f"{arg},"
        # Удаляем запятую в конце строки 
        line = line.rstrip(',')
        # Формируем запрос: Получить data - это словарь json из таблицы в БД,
        # подставляя в запрос позиционные args аргументы и ключевые аргументы kword
        query = "SELECT {} FROM {}".format(line, kword['table'])
        # Делаем запрос к БД на получение данных передав запрос query
        result = self.cursor.execute(query).fetchone() # ->list[({}),]
        try:
            # Считываем json данные и записываем в переменную dic
            dic: Dict[str, Any] = json.loads(result[0]) # -> dict{z:{}, x:{}}
            return dic
        except TypeError:
            return {}

    # Метод добавляет в БД словарь формата json
    def add_data_json_db(self, dic_data: Dict[str, Dict[str, Any]], **kword: str) -> None:
        # Формируем запрос: удалить из таблицы данные
        query = "DELETE FROM {}".format(kword['table'])
        # Делаем запрос к БД
        self.cursor.execute(query)
        # Подтверждаем
        self.conn.commit()
        # Формируем запрос добавить в таблицу словарь с данными в формате json
        query = "INSERT INTO {} VALUES (?)".format(kword['table'])
        # Преобразуем словарь в json 
        dict_json = json.dumps(dic_data)
        # Делаем запрос к БД передаем запрос query и кортеж с данными
        self.cursor.execute(query, (dict_json,))
        # Подтверждаем действия
        self.conn.commit()

    def _add_column(self, column: str) -> None:
        query = "ALTER TABLE Ports ADD COLUMN {} text not NULL".format(column)
        #query = "CREATE TABLE Alarms data json"
        self.cursor.execute(query)
        self.conn.commit()
    
    # Метод создает таблицу в БД
    def _add_table(self) -> None:
        #query = "CREATE TABLE Ports (ip_addr not NULL, port integer not NULL, description text not NULL, FOREIGN KEY  (ip_addr) REFERENCES Devices(ip))"
        query = "CREAT TABLE Switch (data json)"
        self.cursor.execute(query)
        self.conn.commit()

    def _del_table(self) -> None:
       query = "DROP TABLE Settings"
       self.cursor.execute(query)
       self.conn.commit() 

    #def _get_table_db(self):
        #result = self.cursor.execute("SELECT * FROM Users").fetchall()
        #return result

    #def _get(self, **kword):
        #query = "SELECT chat_id FROM Users WHERE user_name= ? and chat_id ISNULL"
        #list_tuple_name = self.cursor.execute(query, (kword['user_name'],)).fetchall()# --> list[(),]

if __name__ == "__main__":
    sql = ConnectSqlDB()

    #sql.add_db(alarms='low_oil', num=35, table='Settings')
    #print(sql.get_values_list_db('data', table='Duration'))
    #print(sql.get_values_dict_db('json_extract(data, "$.power_alarm", "$.hight_temp")', table='Alarms'))
    #print(sql.get_values_dict_db('data', table='Alarms'))
    #sql.add_chat_id(user_name='Кузьмин Иван', chat_id='7777777')
    #sql.del_db(table='Settings')
    #sql.get(user_name='Кузьмин Иван')
    #print(type(sql.get_values_list_db('chat_id', chat_id='IS not null', table='Users')[0][0]))
    #print(sql.get_values_list_db('chat_id', chat_id='IS not null', table='Users')[0][0])
    print(sql.get_db('num', alarms='monitor_count', table='Settings'))
    #sql.add_traffic('traffic_in', traffic = '1232312', ip='10.0.31.3', port='4')
    #sql._add_column('provider')
    #print(sql.get_table_db())
    #sql._add_table()
    #print(sql.get_join_data('10.0.31.3'))
    #print(sql.get_db('model', 'description', ip='10.31.178.2', table='Devices'))
    #sql.add_alarm(data)
    #print(sql.get_values_dict_db('data', table='Interim'))
    #print(type(sql.get_alarm()))
    #sql._del_table()
    #sql.add_device('forpost','10.12.12.12', 'KPP-FORPOST')
    #print(sql.get_device('10.192.50.2'))
    #sql.del_device('10.192.50.2')
    time.sleep(10)

    
