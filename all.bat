@echo off

:: Commandes Docker
echo Lancement des commandes Docker...
docker ps
docker-compose down -v 
docker ps
docker-compose up -d --build 
docker ps

:: Scripts Python
echo Lancement des scripts Python...
docker-compose exec flask_model python -m app.startup


echo OK


