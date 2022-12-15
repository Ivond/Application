#
import pandas as pd
from pathlib import Path 
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from PyQt5.QtCore import QThread


class MashineLearningLoadLow(QThread):
    def __init__(self) -> None:
        # Запускаем у класса QThread метод init
        QThread.__init__(self)
        # Путь к каталогу где лежит файл Excel
        path = Path(Path.cwd(), "Resources", "Data_Frame_ML_Low_Load.xlsx")
        # Считываем данные из файла Excel и записываем в переменную data_frame
        data_frame = pd.read_excel(path)
        # Создаем экземпляр класса RandomForestClassifier
        self.rfc = RandomForestClassifier()
        # Формируем входные данные убираем из дата фрейма кколонку target
        self.X = data_frame.drop('target', axis=1)
        # Формируем целевые данные, те значения которые мы хотим получить, обращаемся к колонки target нашего df
        y = data_frame.target
        # Поделим данные на тренировочную (обучающую train) выборку и тестовую(проверочную test) выборку.
        # Для этого воспользуемся train_test_split
        # Во время обучения модель ищет связь между X_train и y_train
        X_train, X_test, y_train, y_test = train_test_split(self.X, y, test_size=0.30)
        # Во время проверки мы просим нашу модель предсказать передав ей X_test и затем сравниваем полученные значения с y_test 
        # Обучение
        self.rfc.fit(X_train, y_train)

    # Метод возращает строку со значением состояния канала, принимает на вход значения количества трафика на порту
    def predict(self, sample) -> str:
        # Преобразуем словарь sample в Data Frame
        sample_df = pd.DataFrame(data=sample, columns=self.X.columns)
        try:
            result = self.rfc.predict(sample_df)
            return result[0]
        except ValueError:
            pass

if __name__ == '__main__':

    sample = {'inbound': [1000], 
               'outbound': [20000]}
    ml = MashineLearningLoadLow()
    print(ml.predict(sample))