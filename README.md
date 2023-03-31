[![FOODGRAM_Status](https://github.com/MarinaChernykh/foodgram-project-react/actions/workflows/yamdb_workflow.yml/badge.svg)](https://github.com/MarinaChernykh/foodgram-project-react/actions/workflows/yamdb_workflow.yml)
# Проект Foodgram 

Проект доступен по адресу:
<http://foodgram-recipes.hopto.org/>

## Описание
Сервис **Foodgram** позволяет публиковать рецепты, подписываться на публикации других пользователей, добавлять понравившиеся рецепты в список «Избранное», а перед походом в магазин скачивать список продуктов, необходимых для приготовления одного или нескольких выбранных блюд.

## Пользовательские роли
В рамках проекта предусмотрены следующие пользовательские роли:

**Аноним** — может просматривать рецепты, страницы пользователей, а также может зарегистрироваться на сайте.

**Аутентифицированный пользователь (user)** — может публиковать свои рецепты, подписываться на других авторов, добавлять рецепты в список избранного и в список того, что они планируют приготовить, а также скачивать список необходимых ингредиентов в PDF формате для удобного шоппинга.

**Администратор (admin)** — полные права на управление контентом проекта. Может удалять любые рецепты, блокировать пользователей, добавлять новые теги и ингредиенты.


## Технологии
* Python 3.7
* Django 3.2
* DjangoRestFramework 3.14
* PostgreSQL 13.0


## Как запустить проект на удаленном сервере

1. Сделайте форк и склонируйте репозиторий
```
git clone <адрес-форка-репозитория>
```
2. В папке infra создайте файл .env и заполните его переменными окружения. Ниже указан пример заполнения:
```
DB_ENGINE=django.db.backends.postgresql
DB_NAME=databasename
POSTGRES_USER=superuser
POSTGRES_PASSWORD=mypassword
DB_HOST=db
DB_PORT=5432
SECRET_KEY='generate-new-django-secret-key'
```
3. Занесите все указанные выше переменные окружения в раздел Secrets and variables -> actions Настроек вашего репозитория на GitHub.
Также внесите туда следующие переменные и их значения:

* Данные для подключения к вашему аккаунту DockerHub:
```
DOCKER_USERNAME
DOCKER_PASSWORD
```
* Данные для подключения к вашему удаленному серверу:
```
HOST
USER
SSH_KEY
PASSPHRASE
```
* Данные для оповещений в телеграм (опционально. Если оповещения не нужны, удалите блок "send_message" в файле yamdb_workflow.yml данного проекта):
```
TELEGRAM_TO
TELEGRAM_TOKEN
```
4. Cкопируйте на свой удаленный сервер файлы:
* infra/docker-compose.yml
* infra/nginx.conf
* папку docs/
```
scp infra/docker-compose.yml hostname@ip-adress:/home/username/
scp infra/nginx.conf hostname@ip-adress:/home/username/
scp -r docs hostname@ip-adress:/home/username/
```
5. Сделайте коммит проекта и push на github - это запустит процесс создания необходимых образов, их отправку на ваш DockerHub и развертывание на сервере всех необходимых контейнеров, а также запуск проекта 
```
git add .
git commit -m 'комментарий'
git push
```
6. Зайдя на сервер, создайте суперпользователя
```
docker-compose exec backend python manage.py createsuperuser
```
7. Для работы сайта необходимо создать несколько тегов. Авторизуйтесь в админке сайта и создайте 3-4 в разделе "Теги":
```
<http://foodgram-recipes.hopto.org/admin/>
```
6. Сайт готов к работе и доступен по адресу:
<http://foodgram-recipes.hopto.org/admin/>


## Как запустить проект на локальном компьютере

1. Склонируйте репозиторий на локальный компьютер
```
git clone git@github.com:MarinaChernykh/foodgram-project-react.git
```
2. В папке infra создайте файл .env и заполните его переменными окружения. Ниже указан приведен пример заполнения:
```
DB_ENGINE=django.db.backends.postgresql
DB_NAME=databasename
POSTGRES_USER=superuser
POSTGRES_PASSWORD=mypassword
DB_HOST=db
DB_PORT=5432
SECRET_KEY='generate-new-django-secret-key'
```
3. Перейдите в папку infra и запустите контейнеры (frontend, backend, postgres, nginx): 
```
cd infra/
docker-compose-local up
```
4. После завершения запуска контейнеров выполните миграции, создайте суперпользователя, соберите статику
```
docker-compose exec backend python manage.py makemigrations
docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py createsuperuser
docker-compose exec backend python manage.py collectstatic --no-input 
```
5. Для заполнения базы ингредиентов воспользуйтесь командой ниже. Через админку создайте несколько тегов:
```
docker-compose exec backend python manage.py load_ingredients
```
6. Сайт готов к работе и доступен по адресу:
<http://localhost/>




## Документация и примеры запросов к API
Для запуска и просмотра документации по проекту запустите проект либо на удаленном сервере, либо на локально, как описано выше:
После запуска контейнеров документация станет доступна по адресу: 
```
http://foodgram-recipes.hopto.org/api/docs/ - для удаленного сервера
http://localhost/api/docs/ - для локального компьютера
```

