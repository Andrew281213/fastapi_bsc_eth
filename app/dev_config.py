import os

HOST = "0.0.0.0"
PORT = 80  # Порт на котором работает api
SSL_KEYFILE = None  # Путь к файлу ключей
SSL_CERTFILE = None  # Путь к файлу сертификата
MAX_ATTEMPTS = 3  # Максимальное количество попыток для получения ответа
MAX_ACTIVE_COMPOUNDS = 200  # Максимальное количество активных соединение (чем больше соединений, тем больше нагрузка
# на сервер)
TIMEOUT = 20  # Время ожидания ответа страницы в секундах
REPEAT_LOAD_COINS_LIST = 60 * 60  # Время через которое выполняется загрузка списка монет в секундах
REPEAT_PARSE_COINGECKO = 60 * 60 * 6  # Время через которое выполняется парсинг coingecko в сукундах
REPEAT_PARSE_COINMARKETCAP = 60 * 60 * 6  # Время через которое выполяется парсинг coinmarketcap в секундах
FILE_WITH_PROXIES = "proxies.txt"  # Путь к файлу прокси
PROXY_TYPE = "socks5"  # Тип прокси (поддерживаются http(его же указывать для https), socks4, socks5)
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))  # Путь к директории проекта
DATA_DIR = os.path.join(PROJECT_DIR, "data")    # Путь к директории с данными
