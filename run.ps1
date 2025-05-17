# run.ps1
# Запуск в PowerShell (с учётом .env)

# 1. Загрузить переменные окружения из .env
Get-Content .env |
    Where-Object { $_ -and ($_ -notmatch '^\s*#') -and ($_ -match '=') } |
    ForEach-Object {
        $pair = $_ -split '=', 2
        [System.Environment]::SetEnvironmentVariable($pair[0], $pair[1], 'Process')
    }

# 2. Инициализация БД и создание дефолтного админа
$initScript = @"
from app import db, Admin
from werkzeug.security import generate_password_hash
# Создаём таблицы
db.create_all()
# Если нет админа — добавляем
if not Admin.query.filter_by(username='admin').first():
    admin = Admin(username='admin', password_hash=generate_password_hash('admin'))
    db.session.add(admin)
    db.session.commit()
"@

# Передаём скрипт в stdin Python-а
$initScript | python -

# 3. Запустить приложение
Write-Host "Запуск Flask-приложения на http://127.0.0.1:5000"
python app.py
