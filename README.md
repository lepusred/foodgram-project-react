
![foodgram-project-react](https://github.com/lepusred/yamdb_final/actions/workflows/yamdb_workflow.yml/badge.svg)
  
##### Проект доступен по адресу: http://84.201.139.124/

### Описание:

Проект **foodgram-project-react** это  сайт, на котором вы можете выложит свой рецепт, найти подходящий рецепт другого автора, а также скачать список необходимых покупок 

 **foodgram-project-react** дает возможность передавать данные с помощью **REST API** интерфейса, доступные действия:

- регистрация пользователя

- получение или обновление токена

- получение полного списка рецептов

- просмотр уже имеющихся рецептов или добавление своего

- добавление рецепта в избранное и список покупок

  и т.д

### Как запустить проект: 

В консоли bash:

Клонируйте репозиторий в командной строке в нужную вам папку:

```
git clone https://github.com/lepusred/foodgram-project-react.git
```

Перейдите в папку foodgram-project-react:

```
cd /foodgram-project-react
```

Cоберите контейнеры и запустите их внутри этой папки

```
docker-compose up
```

Выполните миграции:

```
docker-compose exec web python manage.py migrate
```

Создайте суперпользователя:

```
docker-compose exec web python manage.py createsuperuser
```

Подгрузите статику:

```
docker-compose exec web python manage.py collectstatic --no-input
```

Можно посмотреть список эндпоинов по ссылке

[http://84.201.139.124/api/docs/](http://84.201.139.124/api/docs/)
