import re
import sqlite3
from pathlib import Path
import json

class ConnectSqlDB:

    def __init__(self):

        self.path_sql_db = Path(Path.cwd(), "Resources", "chatbot.db")
        # Первое что мы должны сделать создать соединение с БД:
        self.conn = sqlite3.connect(self.path_sql_db)
        self.cursor = self.conn.cursor()

        self.kwords = {"name":None, "chat_id":None}

    # Метод добавляет данные в БД
    def add_db(self, **kword):
        # Проверяем если обращаение идет к таблице Users 
        if kword['table'] == 'Users':
            # Формируем запрос: Добавить в таблицу Users значения user_name и description
            query = "INSERT INTO Users (user_name, description) VALUES (?, ?)"
            # Делаем запрос к БД
            self.cursor.execute(query, (kword['user_name'], kword['description']))
            self.conn.commit()
        # Проверяем если обращение идет к таблице Devices
        elif kword['table'] == 'Devices':
            # Формируем запрос: Добавить в таблицу Devices значения key, ip, description
            query = "INSERT INTO Devices (key, ip, description) VALUES (?, ?, ?)"
            # Делаем запрос к БД
            self.cursor.execute(query, (kword['key'], kword['ip'], kword['description']))
            self.conn.commit()

    # Метод добавляет chat_id для имени пользователя у которого ячейка чат id не заполнена
    def add_chat_id(self, **kword):
        # Добавить в таблицу Users chat_id ГДЕ user_name=user_name И chat_id=None 
        query = "UPDATE Users set chat_id = ? WHERE user_name = ? and chat_id ISNULL"
        # Делаем запрос к БД
        self.cursor.execute(query, (kword['chat_id'], kword['user_name']))
        # Подтверждаем действия
        self.conn.commit()

    # Метод удаляет пользователя из БД
    def del_db(self, **kword):
        # Проверяем если обращаение идет к таблице Users 
        if kword['table'] == 'Users':
            query = "DELETE FROM Users WHERE user_name = ? and description = ?"
            self.cursor.execute(query, (kword['user_name'], kword['description']))
            self.conn.commit()
        # Проверяем если обращение идет к таблице Devices
        elif kword['table'] == 'Devices':
           query = "DELETE FROM Devices WHERE ip = ?"
           self.cursor.execute(query, (kword['ip'],))
           self.conn.commit()

    # Метод делает запрос к БД, для получения конкретного значения из таблицы 
    #def get_db(self, name=None, chat_id=None, description=None) -> list:
    def get_db(self, **kword) -> tuple:
        if kword['table'] == 'Users':
        # Если мы получили user_name и chat_id:
            if kword.get('user_name') and kword.get('chat_id', 'null') == None:
                # Делаем запрос к БД получить имя пользователя ГДЕ имя пользователя = user_name и chat_id=None
                query = "SELECT user_name FROM Users WHERE user_name= ? and chat_id ISNULL"
                list_tuple_name = self.cursor.execute(query, (kword['user_name'],)).fetchall()# --> list[(),]
            #
            elif kword.get('user_name') and kword.get('chat_id', 'null') != 'null':
                # Делаем запрос к БД получить имя пользователя ГДЕ имя пользователя = user_name и chat_id=None
                query = "SELECT user_name FROM Users WHERE user_name= ? and chat_id = ?"
                list_tuple_name = self.cursor.execute(query, (kword['user_name'], kword['chat_id'])).fetchall()# --> list[(),]   
            #
            elif kword.get('user_name') and kword.get('description'):
                # Делаем запрос к БД получить имя пользователя ГДЕ имя пользователя = user_name и description
                query = "SELECT user_name FROM Users WHERE user_name= ? and description = ?"
                list_tuple_name = self.cursor.execute(query, (kword['user_name'], kword['description'])).fetchall()# --> list[(),]    
            # Если мы получили chat_id пользователя
            elif kword.get('chat_id'):
                # Формируем запрос: получить user_name и description ГДЕ имя пользователя= user_name
                query = "SELECT user_name, description FROM Users WHERE chat_id= ?" 
                # Делаем запрос к БД
                list_tuple_name = self.cursor.execute(query, (kword['chat_id'])).fetchall()# --> list[(),]
            # Если мы получили user_name пользователя
            elif kword.get('user_name'):
                # Делаем запрос к БД chat_id, description ГДЕ имя пользователя = user_name
                query = "SELECT chat_id, description FROM Users WHERE user_name= ?"
                list_tuple_name = self.cursor.execute(query, (kword['user_name'],)).fetchall()# --> list[(),()]
            # Если мы получили description пользователя
            elif kword.get('description'):
                query = "SELECT user_name, chat_id FROM Users WHERE description= ?"
                #
                list_tuple_name = self.cursor.execute(query, (kword['description'],)).fetchall()# --> list[(),()]
        elif kword['table'] == 'Devices':
            # Если мы получили key и description от пользователя
            if kword.get('ip') and kword.get('description'):
                # Формируем запрос
                query = "SELECT key FROM Devices WHERE ip = ? and description = ?"
                list_tuple_name = self.cursor.execute(query, (kword['ip'], kword['description'])).fetchall()
            # Если мы получили key от пользователя
            elif kword.get('key'):
                # Формируем запрос
                query = "SELECT ip, description FROM Devices WHERE key = ?"
                #
                list_tuple_name = self.cursor.execute(query, (kword['key'],)).fetchall()
            # Если мы получили ip пользователя
            elif kword.get('ip'):
                # Формируем запрос
                query = "SELECT key, description FROM Devices WHERE ip = ?"
                #
                list_tuple_name = self.cursor.execute(query, (kword['ip'],)).fetchall()
            # Если мы получили description пользователя    
            elif kword.get('description'):
                # Формируем запрос
                query = "SELECT key, ip FROM Devices WHERE description = ?"
                #
                list_tuple_name = self.cursor.execute(query, (kword['description'],)).fetchall()
        # Если в списке есть данные
        if list_tuple_name:
            # Возвращаем кортеж со значениями
            return list_tuple_name[0]
        # Попадаем в исключение, если не одно из условий не совпало
        #except (sqlite3.OperationalError, IndexError):
            #return False

     # Метод делает запрос к БД, возвращает список
    def get_values_list_db(self, *args, table) -> list:
        if table == 'Users':
            if 'user_name' in args and 'chat_id' in args and 'description' in args :
                # Формируем запрос: Показать столбцы таблицы user_name, chat_id, description из таблице Users
                query = "SELECT {}, {}, {} FROM Users".format(args[0], args[1], args[2])
                # Делаем запрос к БД
                self.cursor.execute(query)
                # Получаем список кортежей с именами пользователей и chat_id
                return self.cursor.fetchall() # --> list[(),()]
            elif 'user_name' in args and 'chat_id' in args or 'user_name' in args and 'description' in args \
                or 'chat_id' in args and 'description' in args:
                # Формируем запрос: Показать имя пользователя и их chat_id
                query = "SELECT {}, {} FROM Users".format(args[0], args[1])
                # Делаем запрос к БД
                self.cursor.execute(query)
                # Получаем список кортежей с именами пользователей и chat_id
                return self.cursor.fetchall() # --> list[(),()]
            # Если запрос по имени пользователя, то возвращаем список имен
            elif 'user_name' in args or 'chat_id' in args or 'description' in args:
                # Формируем запрос: Показать имена пользователей из таблице Users
                query = "SELECT {} FROM Users".format(args[0])
                # Делаем запрос к БД
                self.cursor.execute(query)
        elif table == 'Devices':
            if 'key' in args and 'ip' in args and 'description' in args:
                # Формируем запрос
                query = "SELECT {}, {}, {} FROM Devices".format(args[0], args[1], args[2])
                 # Делаем запрос к БД
                result = self.cursor.execute(query)
                return result.fetchall()
            elif 'key' in args and 'ip' in args or 'key' in args and 'description' in args or \
                'ip' in args and 'description' in args:
                # Формируем запрос
                query = "SELECT {}, {} FROM Devices".format(args[0], args[1])
                 # Делаем запрос к БД
                result = self.cursor.execute(query)
                return result.fetchall()
            elif 'key' in args or 'ip' in args or 'description' in args:
                # Формируем запрос
                query = "SELECT {} FROM Devices".format(args[0])
                # Делаем запрос к БД
                result = self.cursor.execute(query)
        elif table == 'Alarms':
            if 'data' in args:
                # Формируем запрос: получить из таблицы Alarm данные из столбца data
                query = "SELECT {} FROM Alarms".format(args[0])
                # Делаем запрос к БД и получаем список с авариями
                result = self.cursor.execute(query).fetchone() # ->list[({}),]
                #print(result)
                #for row in result:
                    #print(row)
                    # Получаем словарь с авариями
                dic = json.loads(result[0]) # -> dict{z:{}}, x:{}}
                return dic
        # Получаем список кортежей с запрошенными значениями
        list_tuple = self.cursor.fetchall() # --> list[(),()]
        # Создаем генератор списка перебираем список кортежей, если в кортеже есть значение chat_id, 
        # то добавляем в список list_name
        list_name = [name[0] for name in list_tuple if name[0]] # --> list[]
        return list_name

    # Метод добавляет chat_id для имени пользователя у которого ячейка чат id не заполнена
    #def add_chat_id(self, **kword):
        # Добавить в таблицу Users chat_id ГДЕ user_name=user_name И chat_id=None 
        #query = "UPDATE Users set chat_id = ? WHERE user_name = ? and chat_id ISNULL"
        # Делаем запрос к БД
        #self.cursor.execute(query, (kword['user_name'], kword['chat_id']))
        # Подтверждаем действия
        #self.conn.commit()
        #print('Добавил chat_id')

    # Метод удаляет пользователя из БД
    #def del_user_db(self, name, chat_id=None):
        if chat_id:
            query = "DELETE FROM Users WHERE user_name = ? and chat_id = ?"
            self.cursor.execute(query, (name, chat_id))
            self.conn.commit()
        else:
           query = "DELETE FROM Users WHERE user_name = ?"
           self.cursor.execute(query, (name,))
           self.conn.commit()

    #def add_device(self, method, ip_address, description):
        # Формируем запрос
        query = "INSERT INTO Devices (key, ip, description) VALUES (?, ?, ?)"
        # Делвем запрос к БД
        self.cursor.execute(query, (method, ip_address, description))
        # Подтверждаем операцию
        self.conn.commit()


    # Метод удаляет ip адрес устройства из таблицы БД
    #def del_device(self, ip_address) ->None:
        query = "DELETE FROM Devices WHERE ip = ?"
        self.cursor.execute(query, (ip_address,))
        self.conn.commit()

    # Метод добавляет в БД словарь с авариями формата json
    def add_alarm(self, data) ->None:
        # Формируем запрос: удалить из таблицы Alarms все данные
        query = "DELETE FROM Alarms "
        # Делаем запрос к БД
        self.cursor.execute(query)
        # Подтверждаем
        self.conn.commit()
        # Формируем запрос добавить в таблицу Alarms значение json
        query = "INSERT INTO Alarms VALUES (?)"
        # Преобразуем словарь в json 
        dict_json = json.dumps(data)
        # Делаем запрос к БД
        self.cursor.execute(query, (dict_json,))
        # Подтверждаем действия
        self.conn.commit()
        

    def get_table_db(self):
        result = self.cursor.execute("SELECT * FROM Users").fetchall()
        return result

    def add_column(self, column):
        query = "ALTER TABLE Users ADD COLUMN {} text".format(column)
        #query = "CREATE TABLE Alarms data json"
        self.cursor.execute(query)
        self.conn.commit()

    def add_table(self):
        query = "CREATE TABLE Devices (key text not NULL, ip primary key, description text)"
        self.cursor.execute(query)
        self.conn.commit()

    def del_table(self):
       query = "DROP TABLE Alarms"
       self.cursor.execute(query)
       self.conn.commit() 

    def get(self, **kword):
        query = "SELECT chat_id FROM Users WHERE user_name= ? and chat_id ISNULL"
        list_tuple_name = self.cursor.execute(query, (kword['user_name'],)).fetchall()# --> list[(),]
        print(list_tuple_name)


if __name__ == "__main__":
    sql = ConnectSqlDB()

    data = {'power_alarm':{'10,12,12,12': "high_temperature"},
            'low_voltage':{'10,12,12,11': "high_temperature"},
            'limit_oil':{},
            'hight_temp':{},
            'low_temp':{},
            'date':{}
            }
    #sql.add_user_db('Кузьмин Иван', 'Ведущий инженер по ЭТС')
    #sql.add_chat_id(user_name='Кузьмин Иван', chat_id='7777777')
    #sql.del_user_db('Vera')
    #sql.get(user_name='Кузьмин Иван')
    #print(sql.get_values_list_db('data', table='Alarms'))
    #ass = sql.get_values_list_db('data', table='Alarms')
    #if ass['date']:
       # print(1)
    print(sql.get_db(user_name='Кузьмин Иван', chat_id='489848468', table='Users'))
    #sql.add_column('description')
    #print(sql.get_table_db())
    #sql.add_table()
    #sql.add_alarm(data)
    #print(sql.get_alarm())
    #print(type(sql.get_alarm()))
    #sql.del_table()
    #sql.add_device('forpost','10.12.12.12', 'KPP-FORPOST')
    #print(sql.get_device('10.192.50.2'))
    #sql.del_device('10.192.50.2')
