# elasticsearch_testcase
1) Установить библиотеки python из requirements.txt
2) Запустить docker-compose.yml из ./elasticDocker
3) Выполнить команду 'uvicorn main:app' в корневой папке проекта
4) Опционально поместить в директорию ./data файл "posts.csv" и перейти на <ваш адресс>:8000/init.csv 

В env проекта опционально можно передавать переменные:

ES_TITLE - название индекса elastic search
ES_ADDRESS - адресс elastic search
ES_PORT - порт elastic search

PSQL_TITLE - название таблицы в postgres
PSQL_ADDRESS - адрес postrgess
PSQL_PORT - порт postgres
PSQL_USER - имя пользователя postgres
PSQL_PASSWORD - пароль пользователя postgres
