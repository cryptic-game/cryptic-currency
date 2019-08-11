cryptic-currency [![Build Status](https://travis-ci.org/cryptic-game/cryptic-currency.svg?branch=master)](https://travis-ci.org/cryptic-game/cryptic-currency) [![Coverage](https://sonarcloud.io/api/project_badges/measure?project=cryptic-game_cryptic-currency&metric=coverage)](https://sonarcloud.io/dashboard?id=cryptic-game_cryptic-currency)
============

The official currency microservice of Cryptic (https://cryptic-game.net/).

## Testing with Docker

You will need root permissons. To run all commands write `sudo` infront of them.

On Windows use the commandline with administrator permissions.

If you want to test this microservice you can simply build and run a 
container with docker-compose:

`pip install docker-compose`

`docker-compose up -d`

The microservice is available on port `1242`.

## Testing with pipenv

You can also test it without docker using pipenv:

`pipenv run dev` or `pipenv run prod`

To install the dependencies manually use:

`pipenv install`

If you only need a mysql-server you can bring it up with:

`docker-compose up -d db`

## Docker-Hub

This microservice is online on docker-hub (https://hub.docker.com/r/useto/cryptic-currency/).

## API 

[API Documentation](https://github.com/cryptic-game/cryptic-currency/wiki "Microservice API")
