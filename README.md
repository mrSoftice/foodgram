# Проект Foodgram

[![Foodgram Workflow](https://github.com/mrSoftice/foodgram/actions/workflows/main.yml/badge.svg?branch=main&event=push)](https://github.com/mrSoftice/foodgram/actions/workflows/main.yml)

[Foodgram](https://softice.redirectme.net)

---
## 1. Описание
Проект «Фудграм» — это сайт, на котором пользователи будут публиковать свои рецепты, добавлять чужие рецепты в избранное и подписываться на публикации других авторов. Зарегистрированным пользователям также будет доступен сервис «Список покупок». Он позволит создавать список продуктов, которые нужно купить для приготовления выбранных блюд.


## Как запустить проект:

---
### 2. Установка Docker (на платформе Ubuntu) <a id=2></a>

Проект поставляется в четырех контейнерах Docker (db, frontend, backend, nginx).
Для запуска необходимо установить Docker и Docker Compose.
Подробнее об установке на других платформах можно узнать на [официальном сайте](https://docs.docker.com/engine/install/).

Для начала необходимо скачать и выполнить официальный скрипт:
```bash
apt install curl
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
```

При необходимости удалить старые версии Docker:
```bash
apt remove docker docker-engine docker.io containerd runc
```

Установить пакеты для работы через протокол https:
```bash
apt update
```
```bash
apt install \
  apt-transport-https \
  ca-certificates \
  curl \
  gnupg-agent \
  software-properties-common -y
```

Добавить ключ GPG для подтверждения подлинности в процессе установки:
```bash
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
```

Добавить репозиторий Docker в пакеты apt и обновить индекс пакетов:
```bash
add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
```
```bash
apt update
```

Установить Docker(CE) и Docker Compose:
```bash
apt install docker-ce docker-compose -y
```

Проверить что  Docker работает можно командой:
```bash
systemctl status docker
```

Подробнее об установке можно узнать по [ссылке](https://docs.docker.com/engine/install/ubuntu/).

---
### 3. База данных и переменные окружения <a id=3></a>

Проект использует базу данных PostgreSQL.
Для подключения и выполненя запросов к базе данных необходимо создать и заполнить файл ".env" с переменными окружения в корне проекта.

Шаблон для заполнения файла ".env":
```python
COMPOSE_PROJECT_NAME=foodgram
DEBUG=False
ECRET_KEY='Здесь указать секретный ключ'
ALLOWED_HOSTS='Здесь указать имя или IP хоста' (Для локального запуска - 127.0.0.1)
CSRF_TRUSTED='Здесь указать имя или IP хоста',http://127.0.0.1

# DB Engine used: postgres, sqlite
DB_ENGINE=postgres

POSTGRES_DB=foodgram_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

DB_HOST=db
DB_PORT=5432
```

---
### 4. Команды для запуска <a id=4></a>

Перед запуском необходимо склонировать проект:
```bash
HTTPS: git clone https://github.com/mrSoftice/foodgram.git
SSH: git clone git@github.com:mrSoftice/foodgram.git
```

Cоздать и активировать виртуальное окружение:
```bash
python -m venv venv
```
```bash
Linux: source venv/bin/activate
Windows: source venv/Scripts/activate
```

Далее необходимо собрать образы для фронтенда и бэкенда.
Из папки "./backend/" выполнить команду:
```bash
docker build -t foodgram-backend .
```

Из папки "./frontend/" выполнить команду:
```bash
docker build -t foodgram-frontend .
```

Из папки "./nginx/" выполнить команду:
```bash
docker build -t foodgram-proxy .
```

После создания образов можно создавать и запускать контейнеры.
Из папки "./infra/" выполнить команду:
```bash
docker-compose up -d
```

**При запуске контейнеров будет атоматически выполнен сбор статики и выполнены миграции**

Создать суперюзера (Администратора):
```bash
docker-compose exec backend python manage.py createsuperuser
```

---
### 5. Заполнение базы данных <a id=5></a>

С проектом поставляются данные об ингредиентах.
А также полный комплект демо-данных (пользователи, единицы измерения, теги, ингредиенты, рецепты)

Заполнить базу данных ингредиентами можно выполнив следующую команду из папки "./infra/":
Для загрузки готового списка ингредиентов и единиц измерений:
```
docker-compose exec backend python manage.py load_ingredients --format=<file_format> --data-dir=<source directory>
```
  --file_format формат файла загрузки 'json' или 'csv'. По-умолчанию json
  --data-dir  каталог в котором лежат файлы с данными для загрузки. По-умолчанию ./data

Для загрузки полного комплекта демо-данных (пользователи, единицы измерения, теги, ингредиенты, рецепты):
```
docker-compose exec backend python manage.py load_demo_data --data-dir=<source directory>
```
  --data-dir  каталог в котором лежат файлы с данными для загрузки. По-умолчанию ./data
автоматически создаются пользователи:
	user1@example.com ("password123")
	user2@example.com ("password123")


Также необходимо заполнить базу данных тегами (или другими данными).
Для этого требуется войти в [админ-зону](http://localhost/admin/)
проекта под логином и паролем администратора (пользователя, созданного командой createsuperuser).


Подробную информацию по всем функциям API можно получить после запуска проекта в формате **Redoc** по адресу [ReDoc](http://localhost/api/docs/) или из файла [project folder\docs\openapi-schema.yml](./docs/openapi-schema.yml)


## Технологический стек
	Python 3
	Django
	Django Rest Framework
  PostgreSQL
	React
	Docker


## Разработчики
* [Гончаренко Денис](https://github.com/mrSoftice)
