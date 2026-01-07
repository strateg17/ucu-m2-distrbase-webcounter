# Web Counter Performance

Цей репозиторій містить простий FastAPI-сервіс з двома ендпоінтами:

- `GET /inc` — потокобезпечний інкремент лічильника.
- `GET /count` — повертає поточне значення лічильника.

Сховище лічильника можна перемикати між оперативною пам'яттю та файловою системою змінною оточення `STORAGE_MODE` (`memory` або `file`). 
Для файлового режиму шлях до файлу задається `COUNTER_FILE` (за замовчуванням `./data/counter.txt`).

## Вимоги

- Python 3.11+
- Залежності з `requirements.txt`

```bash
pip install -r requirements.txt
```

> Якщо бачите `ModuleNotFoundError: No module named 'psycopg2'` під час запуску
> серверу або `postgres_counter.py`, переконайтесь, що встановлені залежності з
> `requirements.txt` у тій самій віртуальній енвіронменті, де запускається
> команда.

## Запуск сервера

```bash
# ОЗУ режим (за замовчуванням)
uvicorn server:app --host 0.0.0.0 --port 8080

# Файловий режим
STORAGE_MODE=file COUNTER_FILE=./data/counter.txt uvicorn server:app --host 0.0.0.0 --port 8080
```

## Клієнт для навантаження

Скрипт `client.py` запускає декілька потоків і робить вказану кількість запитів до `/inc`, вимірюючи загальний час виконання та обраховуючи throughput.

```bash
python client.py http://localhost:8080 --clients 5 --requests-per-client 10000
```

У виході буде надруковано:

```
clients=5 requests_per_client=10000 total_requests=50000 elapsed=2.345s throughput=21314.61rps count=50000
```

`count` показує фактичне значення на сервері після навантаження.

## PostgreSQL як сховище

Сервер підтримує сховище в PostgreSQL з атомарним збільшенням лічильника:

```bash
STORAGE_MODE=postgres POSTGRES_DSN="postgres://user:pass@localhost/db" uvicorn server:app --host 0.0.0.0 --port 8080
```

Сервер очікує, що PostgreSQL вже запущений та доступний за вказаним DSN; якщо з'єднання відсутнє, ендпоінти повернуть 503 з
підказкою перевірити DSN/стан сервера. Таблиця `user_counter` створюється автоматично (стовпці `counter` та `version`), а запис для
`COUNTER_USER_ID` (за замовчуванням 1) додається, якщо його ще немає. Інкремент виконується через `UPDATE ... SET counter = counter + 1 RETURNING counter`, тому не потребує додаткового блокування.

### Налаштування PostgreSQL у WSL2 (Ubuntu 22.04)

Для виконання завдання потрібен доступний сервер PostgreSQL. Є два типові варіанти.

**Варіант 1: Локальна інсталяція у WSL2**

```bash
sudo apt update
sudo apt install -y postgresql postgresql-contrib
sudo service postgresql start
```

Далі створіть базу та користувача (з прикладу нижче змініть пароль):

```bash
sudo -u postgres psql -c "CREATE USER webcounter WITH PASSWORD 'webcounter';"
sudo -u postgres psql -c "CREATE DATABASE webcounter OWNER webcounter;"
```

DSN для запуску сервера/скриптів:

```bash
postgres://webcounter:webcounter@localhost:5432/webcounter
```

**Варіант 2: Docker контейнер (рекомендовано, якщо не хочете ставити PostgreSQL локально)**

```bash
docker pull postgres:16
docker run --name webcounter-postgres \
  -e POSTGRES_USER=webcounter \
  -e POSTGRES_PASSWORD=webcounter \
  -e POSTGRES_DB=webcounter \
  -p 5432:5432 \
  -d postgres:16
```

Перевірка, що контейнер готовий:

```bash
docker logs -f webcounter-postgres
```

DSN для запуску серверу/скриптів такий самий:

```bash
postgres://webcounter:webcounter@localhost:5432/webcounter
```

## Перед початком вимірювань

1. **Почистити стан**: перед новою серією тестів видаліть файл лічильника або перезапустіть сервер, щоб значення починалось з нуля.
2. **Паралельний старт клієнтів**: усі потоки стартують одночасно за допомогою бар’єру, що дозволяє оцінювати мультиклієнтські сценарії.
3. **Безпечність**: у пам'ятному режимі використовується `threading.Lock`, у файловому — блокування файлу через `fcntl`, що усуває `lost update` під час конкурентних записів.

## Приклади серій

- 1 клієнт × 10K запитів → очікуване `count = 10_000`
- 2 клієнти × 10K запитів → очікуване `count = 20_000`
- 5 клієнтів × 10K запитів → очікуване `count = 50_000`
- 10 клієнтів × 10K запитів → очікуване `count = 100_000`

Після кожної серії throughput можна отримати зі стандартного виводу `client.py`, а фінальне значення лічильника — через `GET /count` або з того ж виводу.

## Тести PostgreSQL для завдання 2

Скрипт `postgres_counter.py` запускає п'ять сценаріїв конкурентних оновлень у базі PostgreSQL: `lost-update`, `serializable`,
`in-place`, `row-locking`, `optimistic`. Кожен варіант створює власні підключення для потоків, комітить кожну операцію та повертає
час виконання.

Перед запуском можна створити таблицю та початковий запис прапорцем `--prepare`, а очищення значення виконується через `--reset`.

```bash
python postgres_counter.py --dsn "postgres://user:pass@localhost/db" \
  --scenario in-place --clients 10 --requests-per-client 10000 --prepare --reset
```

Після завершення скрипт друкує фактичне значення `counter`/`version`, час виконання та throughput, що дозволяє порівнювати
продуктивність усіх стратегій.
