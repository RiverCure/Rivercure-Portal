# Start virtual environment
alias venv=". venv/bin/activate";

# Starts development server
alias runserver="python manage.py runserver";

# Makes migrations
function makeMigrationsFunc {
    python manage.py makemigrations "$1";
}
alias makemigrations=makeMigrationsFunc;

# Applies migrations
alias migrate="python manage.py migrate";
