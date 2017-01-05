# PreDOTS


## Get started
## Development
1. Install Docker and docker-compose
2. Run `$ docker-machine ip default` to get IP of Docker machine
3. Run `$ docker-compose build` to build all containers (do that when you are changing dependencies
4. Run `$ docker-compose up` to start all containers. Put `-d` headless mode
5. Access the docker ip at port 8000.

## Testing
For testing simply run:

```
$ docker-compose run web py.test
```
## Useful things
### Work on Python shell
```
$ docker-compose run web python3 manage.py shell
```
This is useful when you want to test and create database objects

### Task execution
```
$ docker-compose run web python3 manage.py shell
>> from features.tasks import *
>> a_test_name.delay(a_task_parameter)
```

### Task monitoring
Open the docker host at port 5555
