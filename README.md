![example workflow](https://github.com/dmitriizh/foodgram-project-react/actions/workflows/foodgram_workflow.yml/badge.svg)

## Проект Foodgram

## Описание проекта
Foodgram «Продуктовый помощник» представляет собой онлайн-сервис с API. На сервисе пользователи смогут публиковать рецепты, подписываться на публикации других пользователей, добавлять понравившиеся рецепты в список «Избранное», а перед походом в магазин скачивать список продуктов необходимых для приготовления.

## Использованные при реализации проекта технологии
1. Python
2. Django
3. PostgreSQL
4. DRF
5. NGINX
6. Gunicorn
7. Docker
8. DockerHub Actions

## Описание команд для запуска проекта локально.
* Клонировать репозиторий и перейти в него в командной строке:

+ git clone git@github.com:dmitriizh/foodgram-project-react.git
+ cd foodgram-project-react
* Cоздать и активировать виртуальное окружение:

+ python3 -m venv venv
+ source venv/bin/activate
* Установить зависимости из файла requirements.txt:

+ python3 -m pip install --upgrade pip
+ cd backend/foodgram
+ pip install -r requirements.txt
* Выполнить миграции:

+ python3 manage.py migrate
* Запустить проект:

+ python3 manage.py runserver
* Создание суперпользователя
* Для создания superuser выполните команду:

+ python3 manage.py createsuperuser
* Описание команды для заполнения базы данными.
* После выполнения миграций:

+ python3 manage.py loaddata fixtures.json
* Для подключения frontend
* Перейти в директорию:

+ cd ../../infra
* Выполнить команду:

+ docker-compose up
* Описание команд для запуска приложения в контейнерах.
* Перейдите в раздел infra/ и выполните команду:

+ docker-compose up -d --build
* Выполните миграции:

+ sudo docker-compose exec backend python manage.py migrate
* Для создания superuser выполните команду:

+ sudo docker-compose exec backend python manage.py createsuperuser
* Для сбора статики выполните команду:

+ sudo docker-compose exec backend python manage.py collectstatic --no-input


## Примеры запросов к API
* Получение и удаление токена

+ POST /api/auth/token/login/
+ POST /api/auth/token/logout/
* Регистрация нового пользователя:

+ POST /api/users/
* Получение данных своей учетной записи:

+ GET /api/users/me/
* Получение страницы пользователя и списка всех пользователей

+ GET /api/users/:id/
+ GET /api/users/?page=1&limit=3
* Подписка на пользователя и отписка

+ POST /api/users/:id/subscribe/?recipes_limit=3
+ DELETE /api/users/:id/subscribe/
* Подписки пользователя

+ GET /api/users/subscriptions/
* Получение рецепта и списка рецептов

+ GET /api/recipes/:id/
+ GET /api/recipes/
* Создание, обновление и удаление рецепта

+ POST /api/recipes/
+ PATCH /api/recipes/:id/
+ DELETE /api/recipes/:id/
* Добавление рецепта в избранное и удаление из избранного

+ POST /api/recipes/:id/favorite/
+ DELETE /api/recipes/:id/favorite/
* Добавление рецепта в список покупок и удаление из списка покупок

+ POST /api/recipes/:id/shopping_cart/
+ DELETE /api/recipes/:id/shopping_cart/
* Скачать список покупок

+ GET /api/recipes/download_shopping_cart/

## Проект доступен на сайте

* http://foodgramproject.myvnc.com/

## Автор проекта:  
+ Дмитрий Жадаев 
+ zhadaev1992@yandex.ru