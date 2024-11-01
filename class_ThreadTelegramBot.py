#
from typing import Any
from PyQt5.QtCore import QThread
from PyQt5 import QtCore
from class_TelegramBot import TelegramBot
from telegram import error

# Класс запускает чат Бота в отдельном потоке.
class ThreadTelegramBot(QThread):
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
    signal_success = QtCore.pyqtSignal()

    def __init__(self, token:str, helper):
        QThread.__init__(self)
        self.is_stop_bot = False
        self.token = token
        # Созадаем экземпляр класса TelegramBot, которому передаем строку token и 
        # экземпляр класса helper - class telegram.utils.request.QtSignalHelper
        self.bot = TelegramBot(self.token, helper)
    
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
                    self.bot.updater.start_polling(bootstrap_retries=5) 
                    # Испускаем сигнал об успешном подключении
                    self.signal_success.emit()
                except (error.TimedOut, error.BadRequest, error.NetworkError) as err:
                    # Испускаем сигнал, передаем тип ошибки err
                    self.signal_error.emit(err)
                    # Останавливаем работу updater
                    self.bot.updater.stop()
                    # Возвращаем None
                    return None
                except (error.InvalidToken, error.Unauthorized) as err:
                    # Испускаем сигнал, передаем тип ошибки err
                    self.signal_error.emit(err)
                    # Останавливаем работу updater
                    self.bot.updater.stop()
                    # Что бы остановить цикл while используем return
                    return None
            if self.is_stop_bot:
                # Останавливаем работу чат Бота
                self.bot.updater.stop()
                # Переводим флаг в False, что бы цикл не выполнял эту ветку событий
                self.is_stop_bot = False
                # Что бы остановить цикл while используем return
                return None
            self.sleep(1)
            
    # Метод завершает работу чат Бота
    def disconnect(self) -> None:
        self.is_stop_bot = True
        
    # Метод проверяет запущен ли чат Бот
    def is_running(self) -> bool:
        return self.bot.updater.running
        

if __name__ == '__main__':

    token = '1727811223:AAF2FiV8XkXX2wErJxnsXX0xBg_JARNvJ4M'
    bot = ThreadTelegramBot(token)
    bot.start()