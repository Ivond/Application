#
import sqlite3
from pathlib import Path
import json
import time

class ConnectSqlDB:

    def __init__(self):

        self.path_sql_db = Path(Path.cwd(), "Resources", "chatbot.db")
        # Указываем где расположен файл с БД
        #self.path_sql_db = r'C:\inetpub\wwwroot\ApplicationWeb\Resources\chatbot.db'
        # Первое что мы должны сделать создать соединение с БД, указав путь к файлу:
        self.conn = sqlite3.connect(self.path_sql_db)
        #
        self.cursor = self.conn.cursor()
        command = 'PRAGMA foreign_keys=on'
        # Включаем внешние ключи в базе данных SQLite командой PRAGMA
        self.cursor.execute(command)
        # Подтверждаем действие
        self.conn.commit()
    
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.conn.close() 

    # Метод добавляет данные в БД
    def add_db(self, **kword):
        # Проверяем если ключивой аргумент table равен Users - имя таблицы в БД
        if kword['table'] == 'Users':
            # Формируем запрос: Добавить в таблицу данные user_name и description
            query = "INSERT INTO Users (user_name, description) VALUES (?, ?)"
            # Делаем запрос к БД на добавление данных в таблицу Users, передаем запрос query в который подставляем kword аргументы 
            self.cursor.execute(query, (kword['user_name'], kword['description']))
            # Подтверждаем действие
            self.conn.commit()
        # Проверяем если ключивой аргумент table равен Devices - имя таблицы в БД
        elif kword['table'] == 'Devices':
            # Формируем запрос: Добавить в таблицу Devices значения key, ip, description
            query = "INSERT INTO Devices (model, ip, description) VALUES (?, ?, ?)"
            # Делаем запрос к БД на добавление данных в таблицу Devices, передаем запрос query в который подставляем kword аргументы 
            self.cursor.execute(query, (kword['model'], kword['ip'], kword['description']))
            # Подтверждаем действие
            self.conn.commit()
        # Проверяем если ключивой аргумент table равен Ports - имя таблицы в БД
        elif kword['table'] == 'Ports':
            # Формируем запрос: Добавить в таблицу Ports значения ip_addr, port, description, provider
            query = "INSERT INTO Ports (ip_addr, port, description, provider) VALUES (?, ?, ?, ?)"
            # Делаем запрос к БД на добавление данных в таблицу Ports, передаем запрос query в который подставляем kword аргументы 
            self.cursor.execute(query, (kword['ip'], kword['port'], kword['description'], kword['provider']))
            # Подтверждаем действие
            self.conn.commit()

        # Проверяем если ключивой аргумент table равен Pid - имя таблицы в БД
        elif kword['table'] == 'Pid':
            # Формируем запрос: Добавить в таблицу Pid значения process_name, process_id
            query = "Replace INTO Pid (process_name, process_id) VALUES (?, ?)"
            # Делаем запрос к БД на добавление данных в таблицу Pid, передаем запрос query в который подставляем kword аргументы 
            self.cursor.execute(query, (kword['process_name'], kword['process_id']))
            # Подтверждаем действие
            self.conn.commit()
        # Проверяем если ключивой аргумент table равен Settings - имя таблицы в БД
        elif  kword['table'] == 'Settings':
            # Если в запросе передано имя столбца таблицы alarms
            if kword.get('alarms'):
                # Формируем запрос: Добавить/Заменить данные в столбцах alarms и num таблицы Settings на полученные значения
                query = "Replace INTO Settings (alarms, num) VALUES (?, ?)"
                # Делаем запрос к БД на добавление данных в таблицу Settings, передаем запрос query в который подставляем kword аргументы 
                self.cursor.execute(query, (kword['alarms'], kword['num']))
                # Подтверждаем действие
                self.conn.commit()
        # Проверяем если ключивой аргумент table равен Bot - имя таблицы в БД
        elif  kword['table'] == 'Bot':
            # Если в запросе передано имя столбца таблицы alarms
            if kword.get('title'):
                # Формируем запрос: Добавить/Заменить данные в столбцах title и value таблицы Bot на полученные значения
                query = "Replace INTO Bot (title, value) VALUES (?, ?)"
                # Делаем запрос к БД на добавление данных в таблицу Bot, передаем запрос query в который подставляем kword аргументы 
                self.cursor.execute(query, (kword['title'], kword['value']))
                # Подтверждаем действие
                self.conn.commit()

    # Метод добавляет chat_id для имени пользователя у которого ячейка чат id не заполнена
    def add_chat_id(self, **kword):
        # Добавить значение chat_id в таблицу "Users" ГДЕ user_name = kword['user_name'] И chat_id = None 
        query = "UPDATE Users set chat_id = ? WHERE user_name = ? and chat_id ISNULL"
        # Делаем запрос к БД на обнавление данных в таблице Users, передаем запрос query в который подставляем kword аргументы 
        self.cursor.execute(query, (kword['chat_id'], kword['user_name']))
        # Подтверждаем действия
        self.conn.commit()

    def add_traffic(self, value, **kword):
        # Добавить значение traffic в таблицу "Ports" ГДЕ ip_addr= kword['ip'] И port = kword['port'] 
        query = "UPDATE Ports set {} = ? WHERE ip_addr = ? and port = ?".format(value)
        # Делаем запрос к БД на обнавление данных в таблице Ports, передаем запрос query в который подставляем kword аргументы 
        self.cursor.execute(query, (kword['traffic'], kword['ip'], kword['port']))
        # Подтверждаем действия
        self.conn.commit()

    def get_join_data(self, *args):
        # Формируем запрос, получить данные из таблиц Devices И Ports ip адрес которых равен значению
        query = "SELECT * FROM Devices join Ports ON Devices.ip = ? AND Ports.ip_addr = ?"
        # Делаем запрос к БД на получение данных передав запрос query в который подставляем kword аргументы
        list_tuple_data = self.cursor.execute(query, (args[0],args[0])).fetchall()# --> list[(),]
        return list_tuple_data


    # Метод удаляет пользователя из БД
    def del_db(self, **kword):
        # Проверяем если ключивой аргумент table равен Users 
        if kword['table'] == 'Users':
            # Формируем запрос: Удалить из таблицы данные ГДЕ user_name = kword['user_name'] И description = kword['description']
            query = "DELETE FROM Users WHERE user_name = ? and description = ?"
            # Делаем запрос к БД на удаление данных из таблицы Users, передаем запрос query в который подставляем kword аргументы 
            self.cursor.execute(query, (kword['user_name'], kword['description']))
            # Подтверждаем действие
            self.conn.commit()
        # Проверяем если ключивой аргумент table равен Devices
        elif kword['table'] == 'Devices':
           # Формируем запрос: Удалить из таблицы данные ГДЕ ip = kword['ip']
           query = "DELETE FROM Devices WHERE ip = ?"
           # Делаем запрос к БД на удаление данных из таблицы Devices, передаем запрос query в который подставляем kword аргументы 
           self.cursor.execute(query, (kword['ip'],))
           # Подтверждаем действие
           self.conn.commit()
        # Проверяем если ключивой аргумент table равен Ports
        elif kword['table'] == 'Ports':
            if kword.get('ip') and kword.get('port'):  
                # Формируем запрос: Удалить из таблицы данные ГДЕ port = kword['port'] И ip_addr = kword['ip']
                query = "DELETE FROM Ports WHERE port = ? AND ip_addr = ?"
                # Делаем запрос к БД на удаление данных из таблицы Ports, передаем запрос query в который подставляем kword аргументы 
                self.cursor.execute(query, (kword['port'], kword['ip']))
                # Подтверждаем действие
                self.conn.commit()
            elif kword.get('ip'):
                # Формируем запрос: Удалить из таблицы данные ГДЕ ip_addr = kword['ip']
                query = "DELETE FROM Ports WHERE ip_addr = ?"
                # Делаем запрос к БД на удаление данных из таблицы Ports, передаем запрос query в который подставляем kword аргументы 
                self.cursor.execute(query, (kword['ip'],))
                # Подтверждаем действие
                self.conn.commit()
        # Проверяем если ключивой аргумент table равен Pid
        elif kword['table'] == 'Pid':
            # Формируем запрос: Удалить из таблицы данные ГДЕ process_name = kword['process_name']
            query = "DELETE FROM Pid WHERE process_name = ?"
            # Делаем запрос к БД на удаление данных из таблицы Pid, передаем запрос query в который подставляем kword аргументы 
            self.cursor.execute(query, (kword['process_name'],))
            # Подтверждаем действие
            self.conn.commit()
        # Проверяем если ключивой аргумент table равен Bot
        elif kword['table'] == 'Bot':
            # Формируем запрос: Удалить из таблицы данные ГДЕ title = kword['title']
            query = "DELETE FROM Bot WHERE title = ?"
            # Делаем запрос к БД на удаление данных из таблицы Bot, передаем запрос query в который подставляем kword аргументы 
            self.cursor.execute(query, (kword['title'],))
            # Подтверждаем действие
            self.conn.commit()
        
    # Метод делает запрос к БД, для получения конкретного значения из таблицы 
    def get_db(self, *args, **kword) -> list:
        line = ''
        for arg in args:
            line += arg +','
        line = line.rstrip(',')
        # Проверяем если ключивой аргумент table равен Users 
        if kword['table'] == 'Users':
        # Если мы получили ключевые аргументы user_name и chat_id:
            if kword.get('name') and kword.get('chat') == None:
                # Формируем запрос: Получить args ГДЕ user_name = kword['name'] и chat=None
                query = "SELECT {} FROM Users WHERE user_name= ? and chat_id ISNULL".format(line)
                # Делаем запрос к БД на получение данных передав запрос query в который подставляем kword аргументы
                list_tuple_name = self.cursor.execute(query, (kword['name'],)).fetchall()# --> list[(),]
            # Если мы получили ключевые аргументы user_name и chat_id
            elif kword.get('name') and kword.get('chat'):
                # Формируем запрос: Получить user_name ГДЕ user_name = kword['user_name'] и chat_id=kword['chat_id']
                query = "SELECT {} FROM Users WHERE user_name= ? and chat_id = ?".format(line)
                # Делаем запрос к БД на получение данных передав запрос query в который подставляем kword аргументы
                list_tuple_name = self.cursor.execute(query, (kword['name'], kword['chat'])).fetchall()# --> list[(),]   
            # Если мы получили ключевые аргументы user_name и description
            #elif kword.get('user_name') and kword.get('description'):
                # Формируем запрос: Получить user_name ГДЕ user_name = kword['user_name'] и description=kword['description']
                #query = "SELECT user_name FROM Users WHERE user_name= ? and description = ?"
                # Делаем запрос к БД на получение данных передав запрос query в который подставляем kword аргументы
                #list_tuple_name = self.cursor.execute(query, (kword['user_name'], kword['description'])).fetchall()# --> list[(),]    
            # Если мы получили ключевые аргументы chat_id
            #elif kword.get('chat_id'):
                # Формируем запрос: Получить user_name, description ГДЕ chat_id = kword['chat_id']
                #query = "SELECT user_name, description FROM Users WHERE chat_id= ?" 
                # Делаем запрос к БД на получение данных передав запрос query в который подставляем kword аргументы
                #list_tuple_name = self.cursor.execute(query, (kword['chat_id'])).fetchall()# --> list[(),]
            # Если мы получили ключевые аргументы user_name
            #elif kword.get('user_name'):
                # Формируем запрос: Получить chat_id, description ГДЕ user_name = kword['user_name']
                #query = "SELECT chat_id, description FROM Users WHERE user_name= ?"
                # Делаем запрос к БД на получение данных передав запрос query в который подставляем kword аргументы
                #list_tuple_name = self.cursor.execute(query, (kword['user_name'],)).fetchall()# --> list[(),()]
            # Если мы получили ключевые аргументы description
            #elif kword.get('description'):
                # Формируем запрос: Получить user_name, chat_id ГДЕ description = kword['description
                #query = "SELECT user_name, chat_id FROM Users WHERE description= ?"
                # Делаем запрос к БД на получение данных передав запрос query в который подставляем kword аргументы
                #list_tuple_name = self.cursor.execute(query, (kword['description'],)).fetchall()# --> list[(),()]
        # Проверяем если ключивой аргумент table равен Devices
        elif kword['table'] == 'Devices':
            # Если мы получили ключевые аргументы model
            if kword.get('model'):
                # Формируем запрос: Получить args, ГДЕ model = kword['model']
                query = "SELECT {} FROM Devices WHERE model = ?".format(line)
                # Делаем запрос к БД на получение данных передав строку запроса в которую подставляем kword аргументы
                list_tuple_name = self.cursor.execute(query, (kword['model'],)).fetchall()
            # Если мы получили ключевые аргументы ip
            elif kword.get('ip'):
                # Формируем запрос: Получить args ГДЕ ip = kword['ip']
                query = "SELECT {} FROM Devices WHERE ip = ?".format(line)
                # Делаем запрос к БД на получение данных передав запрос query в который подставляем kword аргументы
                list_tuple_name = self.cursor.execute(query, (kword['ip'],)).fetchone()
        # Проверяем если ключивой аргумент table равен Ports
        elif kword['table'] == 'Ports':
            # Если мы получили ключевые аргументы key и description
            if kword.get('ip') and kword.get('port'):
                # Формируем запрос: Получить args ГДЕ ip_addr = kword['ip'] И port = kword['port']
                query = "SELECT {} FROM Ports WHERE ip_addr = ? and port = ?".format(line)
                # Делаем запрос к БД на получение данных передав запрос query в который подставляем kword аргументы
                list_tuple_name = self.cursor.execute(query, (kword['ip'], kword['port'])).fetchall()
            # Если мы получили ключевые аргументы key
            #elif kword.get('port'):
                # Формируем запрос: Получить ip, description ГДЕ port = kword['port']
                #query = "SELECT ip_addr, description FROM Devices WHERE port = ?"
                # Делаем запрос к БД на получение данных передав запрос query в который подставляем kword аргументы
                #list_tuple_name = self.cursor.execute(query, (kword['port'],)).fetchall()
            # Если мы получили ключевые аргументы ip
            #elif kword.get('ip'):
                # Формируем запрос: Получить port, description ГДЕ ip = kword['ip']
                #query = "SELECT port, description FROM Devices WHERE ip_addr = ?"
                # Делаем запрос к БД на получение данных передав запрос query в который подставляем kword аргументы
                #list_tuple_name = self.cursor.execute(query, (kword['ip'],)).fetchall()
            # Если мы получили ключевые аргументы description   
            #elif kword.get('description'):
                # Формируем запрос: Получить key, ip ГДЕ description = kword['description']
                #query = "SELECT ip_addr, port FROM Devices WHERE description = ?"
                # Делаем запрос к БД на получение данных передав запрос query в который подставляем kword аргументы
                #list_tuple_name = self.cursor.execute(query, (kword['description'],)).fetchall()
        # Проверяем если ключивой аргумент table равен Pid
        elif kword['table'] == 'Pid':
            # Если мы получили ключевые аргументы process_name
            if kword.get('process_name'):
                # Формируем запрос: Получить process_id ГДЕ process_id = kword['process_id']
                query = "SELECT process_id FROM Pid WHERE process_name = ?"
                # Делаем запрос к БД на получение данных передав запрос query в который подставляем kword аргументы
                list_tuple_name = self.cursor.execute(query, (kword['process_name'],)).fetchall()
        # Проверяем если ключивой аргумент table равен Settings
        elif kword['table'] == 'Settings':
            # Если мы получили ключевые аргументы alarms
            if kword.get('alarms'):
                # Формируем запрос: Получить num ГДЕ alarms = kword['alarms']
                query = "SELECT num FROM Settings WHERE alarms = ?"
                # Делаем запрос к БД на получение данных передав запрос query в который подставляем kword аргументы
                list_tuple_name = self.cursor.execute(query, (kword['alarms'],)).fetchall()
        # Проверяем если ключивой аргумент table равен Bot
        elif kword['table'] == 'Bot':
            # Если мы получили ключевые аргументы title
            if kword.get('title'):
                # Формируем запрос: Получить value ГДЕ title = kword['title']
                query = "SELECT value FROM Bot WHERE title = ?"
                #
                list_tuple_name = self.cursor.execute(query, (kword['title'],)).fetchall()
        # Возвращаем кортеж со значениями
        return list_tuple_name

    # Метод делает запрос к БД, возвращает список со значениями
    def get_values_list_db(self, *args, table) -> list:
        # Проверяем если ключивой аргумент table равен Users
        if table == 'Users':
            # Если мы получили позиционные аргументы user_name и chat_id и description
            if 'user_name' in args and 'chat_id' in args and 'description' in args :
                # Формируем запрос: Получить user_name и chat_id и description из таблицы Users, подставляя в запрос позиционные ars аргументы
                query = "SELECT {}, {}, {} FROM Users".format(args[0], args[1], args[2])
                # Делаем запрос к БД на получение данных передав запрос query
                self.cursor.execute(query)
                # Получаем список кортежей с именами пользователей, chat_id и описанием
                return self.cursor.fetchall() # --> list[(),()]
            # Если мы получили позиционные аргументы user_name и chat_id и description
            elif 'user_name' in args and 'chat_id' in args or 'user_name' in args and 'description' in args \
                or 'chat_id' in args and 'description' in args:
                # Формируем запрос: Получить user_name и chat_id ИЛИ user_name, description ИЛИ chat_id, description из таблицы Users, подставляя в запрос позиционные args аргументы
                query = "SELECT {}, {} FROM Users".format(args[0], args[1])
                # Делаем запрос к БД на получение данных передав запрос query
                self.cursor.execute(query)
                # Получаем список кортежей с именами пользователей и chat_id
                return self.cursor.fetchall() # --> list[(),()] 
            # Если мы получили позиционные аргументы user_name или chat_id или description
            elif 'user_name' in args or 'chat_id' in args or 'description' in args:
                # Формируем запрос: Получить user_name ИЛИ chat_id ИЛИ description из таблицы Users, подставляя в запрос позиционные args аргументы
                query = "SELECT {} FROM Users".format(args[0])
                # Делаем запрос к БД на получение данных передав запрос query
                self.cursor.execute(query)
        # Проверяем если ключивой аргумент table равен Devices
        elif table == 'Devices':
            # Если мы получили позиционные аргументы model и ip и description
            if 'model' in args and 'ip' in args and 'description' in args:
               # Формируем запрос: Получить model, ip, description из таблицы Devices, подставляя в запрос позиционные args аргументы
                query = "SELECT {}, {}, {} FROM Devices".format(args[0], args[1], args[2])
                 # Делаем запрос к БД на получение данных передав запрос query
                result = self.cursor.execute(query)
                return result.fetchall()
            # Если мы получили позиционные аргументы model и ip и description
            elif 'model' in args and 'ip' in args or 'key' in args and 'description' in args or \
                'ip' in args and 'description' in args:
                # Формируем запрос: Получить model, ip ИЛИ key, description ИЛИ ip, description из таблицы Devices, подставляя в запрос позиционные args аргументы
                query = "SELECT {}, {} FROM Devices".format(args[0], args[1])
                 # Делаем запрос к БД на получение данных передав запрос query
                result = self.cursor.execute(query)
                return result.fetchall()
            # Если мы получили позиционные аргументы model или ip или description
            elif 'model' in args or 'ip' in args or 'description' in args:
                # Формируем запрос: Получить model ИЛИ ip ИЛИ description из таблицы Devices, подставляя в запрос позиционные args аргументы
                query = "SELECT {} FROM Devices".format(args[0])
                # Делаем запрос к БД на получение данных передав запрос query
                result = self.cursor.execute(query)
        # Проверяем если ключивой аргумент table равен Ports
        elif table == 'Ports':
            # Если мы получили позиционные аргументы port и ip и description
            if 'port' in args and 'ip_addr' in args and 'description' in args:
               # Формируем запрос: Получить key, ip, description из таблицы Devices, подставляя в запрос позиционные args аргументы
                query = "SELECT {}, {}, {} FROM Ports".format(args[0], args[1], args[2])
                 # Делаем запрос к БД на получение данных передав запрос query
                result = self.cursor.execute(query)
                return result.fetchall()
            # Если мы получили позиционные аргументы port и ip и description
            elif ('port' in args and 'ip_addr') in args or ('port' in args and 'description') in args or \
                ('ip_addr' in args and 'description') in args:
                # Формируем запрос: Получить port, ip_addr ИЛИ port, description ИЛИ ip_addr, description из таблицы Ports, подставляя в запрос позиционные args аргументы
                query = "SELECT {}, {} FROM Ports".format(args[0], args[1])
                 # Делаем запрос к БД на получение данных передав запрос query
                result = self.cursor.execute(query)
                return result.fetchall()
            # Если мы получили позиционные аргументы port или ip_addr или description
            elif 'port' in args or 'ip_addr' in args or 'description' in args:
                # Формируем запрос: Получить port ИЛИ ip_addr ИЛИ description из таблицы Devices, подставляя в запрос позиционные args аргументы
                query = "SELECT {} FROM Ports".format(args[0])
                # Делаем запрос к БД на получение данных передав запрос query
                result = self.cursor.execute(query)
        # Проверяем если ключивой аргумент table равен Alarms
        elif table == 'Alarms':
            # Если мы получили позиционные аргументы data
            if 'data' in args:
                # Формируем запрос: Получить data - это словарь json из таблицы Alarms, подставляя в запрос позиционные args аргументы
                query = "SELECT {} FROM Alarms".format(args[0])
                # Делаем запрос к БД на получение данных передав запрос query
                result = self.cursor.execute(query).fetchone() # ->list[({}),]
                # Считываем json данные и записываем в переменную dic
                dic = json.loads(result[0]) # -> dict{z:{}}, x:{}}
                return dic
        # Проверяем если ключивой аргумент table равен Date(таблица в которой хранятся данные дата и время начала аварий)
        elif table == 'Duration':
            # Если мы получили позиционные аргументы data
            if 'data' in args:
                # Формируем запрос: Получить data - это словарь json из таблицы Date, подставляя в запрос позиционные args аргументы
                query = "SELECT {} FROM Duration".format(args[0])
                # Делаем запрос к БД на получение данных передав запрос query
                result = self.cursor.execute(query).fetchone() # ->list[({}),]
                # Считываем json данные и записываем в переменную dic
                dic = json.loads(result[0]) # -> dict{z:{}}, x:{}}
                return dic
        # Проверяем если ключивой аргумент table равен Date(таблица в которой хранятся данные дата и время начала аварий)
        elif table == 'Interim':
            # Если мы получили позиционные аргументы data
            if 'data' in args:
                # Формируем запрос: Получить data - это словарь json из таблицы Date, подставляя в запрос позиционные args аргументы
                query = "SELECT {} FROM Interim".format(args[0])
                # Делаем запрос к БД на получение данных передав запрос query
                result = self.cursor.execute(query).fetchone() # ->list[({}),]
                # Считываем json данные и записываем в переменную dic
                dic = json.loads(result[0]) # -> dict{z:{}}, x:{}}
                return dic
        # Проверяем если ключивой аргумент table равен Settings
        elif table == 'Settings':
             # Формируем запрос: Получить alarms, num из таблицы Settings, подставляя в запрос позиционные args аргументы
            query = "SELECT {}, {} FROM Settings".format(args[0], args[1])
            # Делаем запрос к БД на получение данных передав запрос query
            result = self.cursor.execute(query)
            return result.fetchall()
        # Получаем список кортежей с запрошенными значениями
        list_tuple = self.cursor.fetchall() # --> list[(),()]
        # Создаем генератор списка перебираем список кортежей, если в кортеже есть значение chat_id, 
        # то добавляем в список list_name
        list_name = [name[0] for name in list_tuple if name[0]] # --> list[]
        return list_name

    # Метод добавляет в БД словарь с датой и временем возникновения аварии формата json
    def add_date_time(self, data) ->None:
        # Формируем запрос: удалить из таблицы Date все данные
        query = "DELETE FROM Duration "
        # Делаем запрос к БД
        self.cursor.execute(query)
        # Подтверждаем
        self.conn.commit()
        # Формируем запрос добавить в таблицу Date значение json
        query = "INSERT INTO Duration VALUES (?)"
        # Преобразуем словарь в json 
        dict_json = json.dumps(data)
        # Делаем запрос к БД
        self.cursor.execute(query, (dict_json,))
        # Подтверждаем действия
        self.conn.commit()

    # Метод добавляет в БД словарь промежуточные аварии в формате json
    def add_interim_alarm(self, data) ->None:
        # Формируем запрос: удалить из таблицы Date все данные
        query = "DELETE FROM Interim "
        # Делаем запрос к БД
        self.cursor.execute(query)
        # Подтверждаем
        self.conn.commit()
        # Формируем запрос добавить в таблицу Date значение json
        query = "INSERT INTO Interim VALUES (?)"
        # Преобразуем словарь в json 
        dict_json = json.dumps(data)
        # Делаем запрос к БД
        self.cursor.execute(query, (dict_json,))
        # Подтверждаем действия
        self.conn.commit()

    # Метод добавляет в БД словарь с авариями формата json
    def add_alarm(self, data) ->None:
        # Формируем запрос Удалить из таблицы Alarms все данные
        query = "DELETE FROM Alarms"
        # Сначала делаем запрос к БД на удаление данных передав запрос query
        self.cursor.execute(query)
        # Подтверждаем действие
        self.conn.commit()
        # Формируем запрос:  Добавить данные в таблицу Alarms
        query = "INSERT INTO Alarms VALUES (?)"
        # Преобразуем данные (словарь) в json 
        dict_json = json.dumps(data)
        # Затем делаем запрос к БД на добавление данных json в таблицу передав запрос query и сами данные
        self.cursor.execute(query, (dict_json,))
        # Подтверждаем действия
        self.conn.commit()    

    def _get_table_db(self):
        result = self.cursor.execute("SELECT * FROM Users").fetchall()
        return result

    def _add_column(self, column):
        query = "ALTER TABLE Ports ADD COLUMN {} text not NULL".format(column)
        #query = "CREATE TABLE Alarms data json"
        self.cursor.execute(query)
        self.conn.commit()
    
    # Метод создает таблицу в БД
    def _add_table(self):
        #query = "CREATE TABLE Ports (ip_addr not NULL, port integer not NULL, description text not NULL, FOREIGN KEY  (ip_addr) REFERENCES Devices(ip))"
        query = "CREAT TABLE Switch (data json)"
        self.cursor.execute(query)
        self.conn.commit()

    def _del_table(self):
       query = "DROP TABLE Settings"
       self.cursor.execute(query)
       self.conn.commit() 

    def _get(self, **kword):
        query = "SELECT chat_id FROM Users WHERE user_name= ? and chat_id ISNULL"
        list_tuple_name = self.cursor.execute(query, (kword['user_name'],)).fetchall()# --> list[(),]

if __name__ == "__main__":
    sql = ConnectSqlDB()

    #sql.add_db(alarms='low_oil', num=35, table='Settings')
    #sql.get_values_list_db('data', table='Duration')
    #sql.add_chat_id(user_name='Кузьмин Иван', chat_id='7777777')
    #sql.del_db(table='Settings')
    #sql.get(user_name='Кузьмин Иван')
    #print(sql.get_values_list_db('ip_addr','port', table='Ports'))
    #print(sql.get_db('traffic_in', ip='10.0.31.3', port='4', table='Ports'))
    sql.add_traffic('traffic_in', traffic = '1232312', ip='10.0.31.3', port='4')
    #sql._add_column('provider')
    #print(sql.get_table_db())
    #sql._add_table()
    #print(sql.get_join_data('10.0.31.10'))
    #sql.add_alarm(data)
    #print(sql.get_alarm())
    #print(type(sql.get_alarm()))
    #sql._del_table()
    #sql.add_device('forpost','10.12.12.12', 'KPP-FORPOST')
    #print(sql.get_device('10.192.50.2'))
    #sql.del_device('10.192.50.2')
    time.sleep(10)

    
