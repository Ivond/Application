#
import sys
from PyQt5.QtCore import QThread
from class_TelegramBot import TelegramBot
from telegram import error

# Класс запускает чат Бота в отдельном потоке.
class ThreadTelegramBot(QThread):

    def __init__(self, token, line):
        QThread.__init__(self)
        self.token = token
        # Созадаем экземпляр класса TelegramBot
        self.bot = TelegramBot(self.token)
        # Переменная line, которой передаем экземпляр класса Queue( обработчик очередей)
        self.line = line
        ''' 
        self.line.put(sys.exc_info())
        Вызываем у экземпляра класса line метод put, который помещает элемен в очередь.
        Этот метод никогда не блокируется и всегда завершается успешно.
        В качестве элемента передаем метод exc_info модуль sys, который возвращает информацию 
        о самом последнем исключении, перехваченном в текущем фрейме стека или в более раннем фрейме стека.

        '''

    # Метод запускает чат Бот в отдельном потоке
    def run(self):
        # Переводим флаг в True - бот запущен
        self.is_running_bot = True
        # Переводим флаг в False - бот отстановлен
        self.is_stop_bot = False
        # Start the Bot
        while True:
            if self.is_running_bot:
                try:
                    self.bot.updater.start_polling(timeout=10) # Запускает опрос обновлений из Telegram.
                    # Отправляем данные на сделанный запрос get экземпляра line класса Queue из класса Aplication
                    self.line.put(sys.exc_info())
                    # Переводим флаг в False, что бы цикл не выполнял эту ветку событий
                    self.is_running_bot = False
                except (error.TimedOut, error.BadRequest, error.NetworkError, error.Conflict):
                    # Отправляем данные на сделанный get запрос экземпляра line класса Queue из класса Aplication
                    self.line.put(sys.exc_info())
                    # Останавливаем работу updater
                    self.bot.updater.stop()
                    # Переводим флаг в False, что бы цикл не выполнял эту ветку событий
                    self.is_running_bot = False
                except (error.InvalidToken, error.Unauthorized):
                    # Отправляем данные на сделанный запрос get экземпляра line класса Queue из класса Aplication
                    self.line.put(sys.exc_info())
                    # Останавливаем работу updater
                    self.bot.updater.stop()
                    # Переводим флаг в False, что бы цикл не выполнял эту ветку событий
                    self.is_running_bot = False
            if self.is_stop_bot:
                # Останавливаем работу чат Бота
                self.bot.updater.stop()
                # Переводим флаг в False, что бы цикл не выполнял эту ветку событий
                self.is_stop_bot = False
            self.sleep(1)
            
    # Метод завершает работу чат Бота
    def disconnect(self):
        self.is_stop_bot = True

    # Метод проверяет запущен ли чат Бот
    def is_running(self):
        return self.bot.updater.running
        

if __name__ == '__main__':

    token = '1727811223:AAF2FiV8XkXX2wErJxnsXX0xBg_JARNvJ4M'
    bot = ThreadTelegramBot(token)
    bot.start()