# FEXUM
_Framework for Exploring and Understanding Multivariate Correlations Edit_

This repository contains the backend of our big data framework for exploring and understanding:
- Feature selection
- Feature extraction
- Multivariate correlations
- Time series

The [frontend](https://github.com/KDD-OpenSource/predots-frontend) and
[correlation algorithm](https://github.com/KDD-OpenSource/python-hics)
are located in different repositories.

## Contributors
* [Louis Kirsch](https://github.com/timediv)
* [Niklas Riekenbrauck](https://github.com/nikriek)
* [Daniel Thevessen](https://github.com/danthe96)
* [Marcus Pappik](https://github.com/marcuspappik)
* [Axel Stebner](https://github.com/xasetl)
* [Julius Kunze](https://github.com/JuliusKunze)
* [Alexander Meißner](https://github.com/Lichtso)

## Getting Started
1. Run the [setup script](deployment/ubuntu-setup.sh). **Do not install docker.io using apt-get!**
2. Run `$ docker-compose build` to build all containers (do that when you are changing dependencies)
3. Run `$ docker-compose up` to start all containers. Put `-d` for headless mode
4. Run `$ docker-compose run web_wsgi python3 manage.py migrate` to apply migrations
5. Access the docker ip (mostly localhost) at port 80.

### Python Shell
```
$ docker-compose run web_wsgi python3 manage.py shell
```
This is useful when you want to test and create database objects, e.g.:
```
>> from features.tasks import *
>> from features.models import *
>> for feature in Feature.objects.all() 
   ... a_test_name.delay(feature.name)
```

### Task Monitoring
Open the docker host at port 5555



## Development & Contributing

### Testing
For testing simply run:
```
$ docker-compose run web_wsgi py.test
```

### Data Migrations
Create migrations after changing or creating models
```
$ docker-compose run web_wsgi python3 manage.py makemigrations
```
