# Проект Foodgram

[![CI/CD](https://github.com/mrSoftice/foodgram/actions/workflows/main.yml/badge.svg?branch=main&event=push)](https://github.com/mrSoftice/foodgram/actions/workflows/main.yml)
[![Backend tests](https://github.com/mrSoftice/foodgram/actions/workflows/django-tests.yml/badge.svg)](https://github.com/mrSoftice/foodgram/actions/workflows/django-tests.yml)
![Ruff](https://img.shields.io/badge/lint-ruff-2d6cdf.svg)

[Foodgram](https://softice.redirectme.net)

---
## 1. Описание <a id=1></a>
Проект «Фудграм» — это сайт, на котором пользователи будут публиковать свои рецепты, добавлять чужие рецепты в избранное и подписываться на публикации других авторов. Зарегистрированным пользователям также будет доступен сервис «Список покупок». Он позволит создавать список продуктов, которые нужно купить для приготовления выбранных блюд.


## 2. Как запустить проект: <a id=2></a>

Перед запуском необходимо склонировать проект:
```bash
HTTPS: git clone https://github.com/mrSoftice/foodgram.git
```

Cоздать и активировать виртуальное окружение:
```bash
cd foodgram/backend
python -m venv venv
```
```bash
Linux: source venv/bin/activate
Windows: source venv/Scripts/activate
```

### 2.1 База данных и переменные окружения <a id=21></a>

Проект использует базу данных PostgreSQL.
Для подключения и выполненя запросов к базе данных необходимо в корне проекта создать и заполнить файл ".env" с переменными окружения в корне проекта.

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
### 2.2 Развертывание проекта в Docker <a id=22></a>


#### Установка Docker (на платформе Ubuntu)

Проект поставляется в четырех контейнерах Docker (db, frontend, backend, nginx).
Для запуска необходимо установить Docker и Docker Compose.
Подробнее об установке на других платформах можно узнать на [официальном сайте](https://docs.docker.com/engine/install/).


#### Команды для запуска

Далее необходимо собрать образы для фронтенда и бэкенда.

После создания образов можно создавать и запускать контейнеры.
Из папки "./infra/" выполнить команду:
```bash
docker-compose up -d
```

**При запуске контейнеров будет атоматически выполнен сбор статики и выполнены миграции**

Создать суперюзера (Администратора) и загрузить список продуктов и тегов:
```bash
docker-compose exec backend python manage.py createsuperuser
docker-compose exec backend python manage.py load_ingredients
docker-compose exec backend python manage.py load_tags
```

После запуска проекта будет доступены адреса
- [Сам сайт](http://localhost)
- [Админ-панель](http://localhost/admin)
- [Документация в формате **ReDoc**](http://localhost/api/docs/)


---
### 2.3 Локальный запуск проекта <a id=23></a>

Перед запуском необходимо склонировать проект:
```bash
HTTPS: git clone https://github.com/mrSoftice/foodgram.git
```

Установить зависимости из файла requirements.txt:

```
python3 -m pip install --upgrade pip
pip install -r requirements.txt
```

Выполнить миграции:

```
python3 manage.py migrate
```

Создать суперюзера (Администратора) и загрузить список продуктов и тегов:
```bash
python manage.py createsuperuser
python manage.py load_ingredients
python manage.py load_tags
```

Запустить проект:
```
python3 manage.py runserver
```

После запуска проекта будут доступны адреса
- [Сам сайт](http://localhost:8000)
- [Админ-панель](http://localhost:8000/admin)
- [Документация в формате **ReDoc**](http://localhost:8000/api/docs/)

---
Подробную информацию по всем функциям API можно получить после запуска проекта в формате **Redoc** по адресу [ReDoc](http://localhost:8000/api/docs/) или из файла [project folder\docs\openapi-schema.yml](./docs/openapi-schema.yml)


## 4. Технологический стек <a id=4></a>
- Python 3
- Django
- Django Rest Framework
- Djoser
- PostgreSQL
- React
- Docker


## 5. Разработчики <a id=5></a>

* [Гончаренко Денис](https://github.com/mrSoftice) (email: [denis.goncharenko@yandex.com](mailto:denis.goncharenko@yandex.com))
