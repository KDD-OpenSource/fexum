# PreDOTS


## Get started
## Development
1. Install Docker and docker-compose
2. Run `$ docker-machine ip default` to get IP of Docker machine
3. Run `$ docker-compose build` to build all containers (do that when you are changing dependencies
4. Run `$ docker-compose up` to start all containers. Put `-d` for headless mode
5. Run `$ docker-compose run web python3 manage.py migrate` to apply migrations
6. Access the docker ip at port 8000.

## Testing
For testing simply run:

```
$ docker-compose run web py.test
```
## Useful things
## Create migrations
Create migrations after changing or creating models
```
$ docker-compose run web python3 manage.py makemigrations
```
### Work on Python shell
```
$ docker-compose run web python3 manage.py shell
```
This is useful when you want to test and create database objects

### Task execution
```
$ docker-compose run web python3 manage.py shell
>> from features.tasks import *
>> from features.models import *
>> for feature in Feature.objects.all() 
   ... a_test_name.delay(feature.name)
```

### Task monitoring
Open the docker host at port 5555
