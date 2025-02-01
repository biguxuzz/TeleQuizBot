from telebot.storage import StateMemoryStorage

# Создаем глобальное хранилище состояний
state_storage = StateMemoryStorage()

# Добавляем глобальное хранилище данных
class DataStorage:
    def __init__(self):
        self.data = {}

data_storage = DataStorage() 