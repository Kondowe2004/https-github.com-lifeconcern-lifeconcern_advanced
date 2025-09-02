\
@echo off
REM Create venv, install Django, migrate, load demo data, create demo user
python -m venv venv
call venv\Scripts\activate
pip install --upgrade pip
pip install Django>=5.0,<6.0
python manage.py bootstrap_demo
echo.
echo DONE. Start the server with:
echo    venv\Scripts\activate
echo    python manage.py runserver
pause
