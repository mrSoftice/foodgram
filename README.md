# Проект Foodgram

[![Foodgram Workflow](https://github.com/mrSoftice/foodgram/actions/workflows/main.yml/badge.svg?branch=main&event=push)](https://github.com/mrSoftice/foodgram/actions/workflows/main.yml)


## Описание
Проект «Фудграм» — это сайт, на котором пользователи будут публиковать свои рецепты, добавлять чужие рецепты в избранное и подписываться на публикации других авторов. Зарегистрированным пользователям также будет доступен сервис «Список покупок». Он позволит создавать список продуктов, которые нужно купить для приготовления выбранных блюд.

## Возможности


## Как запустить проект:

Клонировать репозиторий и перейти в него в командной строке:

```
git clone https://github.com/mrsoftice/foodgram.git
cd foodgram
```

Cоздать и активировать виртуальное окружение:

```
python3 -m venv env
```

```
source env/bin/activate
```

```
python3 -m pip install --upgrade pip
```

Установить зависимости из файла requirements.txt:

```
pip install -r requirements.txt
```

Выполнить миграции:

```
python3 manage.py migrate
```

Запустить проект:

```
python3 manage.py runserver
```

Подробную информацию по всем функциям API можно получить после запуска проекта в формате **Redoc** по адресу [ReDoc](http://localhost:8000/redoc/) или из файла [project folder\docs\openapi-schema.yml](./docs/openapi-schema.yml)


## Загрузка данных
Для загрузки готового списка ингредиентов и единиц измерений:
```
python manage.py load_ingredients --format=<file_format> --data-dir=<source directory>
```
  --file_format формат файла загрузки 'json' или 'csv'. По-умолчанию json
  --data-dir  каталог в котором лежат файлы с данными для загрузки. По-умолчанию ../data

Для загрузки полного комплекта демо-данных (пользователи, единицы измеренияб теги, ингредиенты, рецепты):
```
python manage.py load_demo_data --data-dir=<source directory>
```
  --data-dir  каталог в котором лежат файлы с данными для загрузки. По-умолчанию ../data
автоматически создаются пользователи:
	user1@example.com ("password123")
	user2@example.com ("password123")

## Примеры использования

##### Получение рецептов
Получить список всех рецептов. При указании параметров limit выдача должна работать с пагинацией. При указании параметра search выдает список публикаций где в тексте встречается указанный фрагмент. Для фильтрации по автору или тегу используются параметры "author" и "tags" (можно перечислять несколько параметров "tags"). Авторы фильтруются по полному совпадению, группы фильтруются по вхождению

| GET                                 |                                                                            |
| ----------------------------------- | -------------------------------------------------------------------------- |


## Технологический стек
	Python
	Django
	Django Rest Framework
    PostgreSQL


## Разработчики
* [Гончаренко Денис](https://github.com/mrSoftice)
