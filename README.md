cryptic-currency
===============

The offical currency microservice of Cryptic (https://cryptic-game.net/)

## Testing with Docker

If you want to test this microservice you can simply build and run a container with docker-compose:

`docker-compose up -d`

The microservice is available on port `1242`.

## Testing with pipenv

You can also test it without docker using pipenv:

`pipenv run dev` or `pipenv run prod`

To install the dependencies manually use:

`pipenv install`

If you need a mysql-server you can bring it up with:

`docker-compose up -d db`

## Docker-Hub

This microservice is online on docker-hub (https://hub.docker.com/r/useto/cryptic-currency/).
