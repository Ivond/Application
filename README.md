СИСТЕМА МОНИТОРИНГА

Desktop приложение для мониторинга параметров Источника Бесперебойного питания (ИБП) и состояние каналов(портов) телеком оборудования.

Для мониторинга ИБП программа выполняет опрос устройств по протоколу SNMP или MODBUS, обробатывает полученые данные(Входное напряжение, температура, напряжение АКБ), если один из параметров не соответствует пороговому значению, отправляется сообщение пользователю с уведомлением.

Для мониторинга каналов связи программа выполняет опрос устройства по протоколу SNMP, обробатывает полученые данные: Статус порта(Up/Down), количетсво трафика на порту (нужно для определения состояния канала если порт физически в Up) и статус IP SLA(если настроен на коммутаторе), если один из параметров не соответствует целевому, отправляется сообщение с уведомлением.

Запускаем приложение файл Application.exe. Интерфейс программы поделен на заклдаки(разделы), у каждого раздела свои функции.

Закладка "Запуск SNMP": Запускаем опрос устройств по SNMP-протоколу, предварительно выставляем интервал опроса(с какой периодичность отправлять запрос на устройства) в секундах

Закладка "Запуск Bot": Запускаем Телеграм бота, для этого вводит token. В этой же закладки настраиваем пороговые значения параметров, при которых будут отправляться уведомления пользователям. Запускаем мониторинг, который обрабатывает полученные данные от SNMP-опросчика. 
В чате Telegram-бота реализованы две кнопки Alarm - получаем сообщения с текущими авариями Status - Получаем сообщение с актуальными значениями параметров ИБП из списка текущих аварий

Закладка "Пользователи": Добавляет пользователя, кому будут приходить уведомления. Для этого вводим NikName пользователя зарегистрированного в Телеграм и ФИО(это как один из вариантов, ограничений нет, лишь бы можно было точно идентиифицировать пользователей с одинаковыми NikName).

Закладка "Устройства": Добавляет устройства для мониторинга. Для этого необходимо ввести ip-адрес, Описание объекта, выбрать модель устройства и номер окна в которое будет выводится строка с параметрами устройства.

Закладка "Каналы": Добавляем порт коммутатора для мониторинга. Для этого необходимо ввести индекса порта(значение ), Описание канала (Начальная и конечная точки), выбрать ip-адрес коммутатора(сам коммутатор добавляется в разделе "Устройства")

Закладка "Окно мониторинга": Визуальный мониторинг параметров устройств. Выставляем пороговые значения при которых строка с параметрами будет подсвечивться цветом(в зависимости от серьезности). Открывется отдельная вкладка на весь экран, разделенная на четыре части.
