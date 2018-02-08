# FEXUM [![Build Status](https://travis-ci.org/KDD-OpenSource/fexum.svg?branch=master)](https://travis-ci.org/KDD-OpenSource/fexum)
_Framework for Exploring and Understanding Multivariate Correlations_

This repository contains the backend of our big data framework for exploring and understanding:
- Feature selection
- Feature extraction
- Multivariate correlations
- Time series

The [frontend](https://github.com/KDD-OpenSource/fexum-frontend) and
[correlation algorithm](https://github.com/KDD-OpenSource/fexum-hics)
are located in different repositories.

The basis for this application has been made into a [paper](https://doi.org/10.1007/978-3-319-71273-4_40), which was submitted to and accepted by ECML PKDD 2017, and published as part of the conference proceedings in the "Lecture Notes in Computer Science" (LNCS) series.

## Contributors
* [Louis Kirsch](https://github.com/timediv)
* [Niklas Riekenbrauck](https://github.com/nikriek)
* [Daniel Thevessen](https://github.com/danthe96)
* [Marcus Pappik](https://github.com/marcuspappik)
* [Axel Stebner](https://github.com/xasetl)
* [Julius Kunze](https://github.com/JuliusKunze)
* [Alexander Meißner](https://github.com/Lichtso)

## Getting Started
1. Run `$ docker-compose build` to build all containers (do that when you are changing dependencies)
2. Run `$ docker-compose up` to start all containers. Put `-d` for headless mode
3. Run `$ docker-compose run web_wsgi python3 manage.py migrate` to apply migrations
4. Access the docker ip (mostly localhost) at port 80.

### Python Shell
```shell
$ docker-compose run web_wsgi python3 manage.py shell
```
This is useful when you want to test and create database objects, e.g.:
```python
>> from features.tasks import *
>> from features.models import *
>> for feature in Feature.objects.all() 
   ... a_test_name.delay(feature.name)
```

### Task Monitoring
Open the docker host at port 5555

### Running with docker in your own network environment

By default the network is configured for the docker containers as followed:
```
networks:
  fexum:
    ipam:
      driver: default
      config:
        - subnet: 10.151.100.0/24
```
If this does not work with your network setup, change the subnet.

## Development & Contributing

### Testing
For testing simply run:
```shell
$ docker-compose run web_wsgi py.test
```

### Data Migrations
Create migrations after changing or creating models
```shell
$ docker-compose run web_wsgi python3 manage.py makemigrations
```
