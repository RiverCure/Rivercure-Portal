# Script made for Mac OS
brew services start rabbitmq;
# Make sure you have venv activated first
celery -A rivercureproject worker -l INFO;