Проект представляет собой онлайн-сервис и API для него. На этом сервисе пользователи могут публиковать рецепты, подписываться на публикации других пользователей, добавлять понравившиеся рецепты в список «Избранное», а перед походом в магазин скачивать сводный список продуктов, необходимых для приготовления одного или нескольких выбранных блюд.

Проект реализован на `Django` и `DjangoRestFramework`. Доступ к данным реализован через API-интерфейс. Документация к API написана с использованием `Redoc`.

- Проект был развернут на сервере: <https://f00dgram.ddns.net/>

Проект поставляется в четырех контейнерах Docker (db, frontend, backend, nginx).  
Для запуска необходимо установить Docker и Docker Compose.

# Установка Docker (на платформе Ubuntu)

- Скачайте и установите curl
```
sudo apt update
sudo apt install curl
```

 - С помощью утилиты curl скачайте и запустите официальный скрипт для установки докера
```
curl -fSL https://get.docker.com -o get-docker.sh
sudo sh ./get-docker.sh
```
- Установите последнюю версию docker compose
```
sudo apt-get install docker-compose-plugin 
```

### Развернуть проект на удаленном сервере:

- Клонировать репозиторий:
```
https://github.com/pa2ha/foodgram-project-react
```

- Перенести файл docker-compose.production.yml на сервер, из папки infra в текущем репозитории (на вашем ПК).
```
scp docker-compose.yml username@IP:/home/username/   # username - имя пользователя на сервере
                                                                # IP - публичный IP сервера
```

Проект использует базу данных PostgreSQL.  
Для подключения и выполненя запросов к базе данных необходимо создать и заполнить файл ".env" с переменными окружения в директории рядом с файлом
```
touch .env
```

Шаблон для заполнения файла ".env":
```
POSTGRES_DB='foodgram' # Задаем имя для БД.
POSTGRES_USER='User' # Задаем пользователя для БД.
POSTGRES_PASSWORD='u_pass' # Задаем пароль для БД.
DB_HOST='db'
DB_PORT='5432'
ALLOWED_HOSTS='127.0.0.1, backend' # Вставляем свой IP сервера.
EXTERNAL_PORT=8000 # порт на котором будет работать проект
```

- Создать и запустить контейнеры Docker, выполнить команду на сервере
```
sudo docker compose up -d
```

- После успешной сборки выполнить миграции:
```
sudo docker compose exec backend python manage.py migrate
```

- Создать суперпользователя:
```
sudo docker compose exec backend python manage.py createsuperuser
```

- Собрать статику:
```
sudo docker compose exec backend python manage.py collectstatic --noinput
sudo docker compose exec backend cp -r /app/collected_static/. /backend_static/static/
```

- Дополнительно можно наполнить DB ингредиентами
```
sudo docker compose exec backend python manage.py import_ingredients_from_csv
```

- Для остановки контейнеров Docker:
```
sudo docker compose down -v      # с их удалением
sudo docker compose stop         # без удаления
```

- Для запуска с использованием CI/CD и Docker необходимо в репозитории в разделе Secrets > Actions создать переменные окружения:
```
SECRET_KEY                # секретный ключ Django проекта
DOCKER_PASSWORD         # пароль от Docker Hub
DOCKER_USERNAME         # логин Docker Hub
HOST                    # публичный IP сервера
USER                    # имя пользователя на сервере
PASSPHRASE              # *если ssh-ключ защищен паролем
SSH_KEY                 # приватный ssh-ключ
TELEGRAM_TO             # ID телеграм-аккаунта для посылки сообщения
TELEGRAM_TOKEN          # токен бота, посылающего сообщение

DB_ENGINE               # django.db.backends.postgresql
POSTGRES_DB             # postgres
POSTGRES_USER           # postgres
POSTGRES_PASSWORD       # postgres
DB_HOST                 # db
DB_PORT                 # 5432 (порт по умолчанию)
```

После каждого обновления репозитория (push в ветку master) будет происходить:

1. Проверка кода на соответствие стандарту PEP8 (с помощью пакета flake8)
2. Сборка и доставка докер-образов frontend и backend на Docker Hub
3. Разворачивание проекта на удаленном сервере
4. Отправка сообщения в Telegram в случае успеха

### Запуск проекта на локальной машине:

- Клонировать репозиторий:
```
https://github.com/pa2ha/foodgram-project-react
```

- В директории infra создать файл .env и заполнить своими данными по аналогии с example.env:
```
DB_ENGINE=django.db.backends.postgresql
POSTGRES_DB=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432
SECRET_KEY='секретный ключ Django'
```

- Создать и запустить контейнеры Docker, последовательно выполнить команды по созданию миграций, сбору статики, 
созданию суперпользователя, как указано выше.
```
docker-compose -f docker-compose.yml up -d
```


- После запуска проект будут доступен по адресу: [http://localhost/](http://localhost/)


- Документация будет доступна по адресу: [http://localhost/api/docs/](http://localhost/api/docs/)


Стек технологий: Python, Django, Django Rest Framework, Docker, Gunicorn, NGINX, PostgreSQL, Yandex Cloud, Continuous Integration, Continuous Deployment

Автор: [Дроздов Даниил](https://github.com/pa2ha)
