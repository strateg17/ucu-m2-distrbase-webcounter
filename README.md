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

Таблиця `user_counter` створюється автоматично (стовпці `counter` та `version`), а запис для `COUNTER_USER_ID` (за замовчуванням 1)
додається, якщо його ще немає. Інкремент виконується через `UPDATE ... SET counter = counter + 1 RETURNING counter`, тому не
потребує додаткового блокування.

### Розгортання PostgreSQL (локально або в Docker)

> У репозиторії немає сервісу PostgreSQL, тому її потрібно підняти окремо.

#### Варіант 1: Docker

```bash
docker run --name webcounter-postgres \
  -e POSTGRES_USER=counter_user \
  -e POSTGRES_PASSWORD=counter_pass \
  -e POSTGRES_DB=counter_db \
  -p 5432:5432 \
  -d postgres:16
```

Перевірка доступності:

```bash
docker logs -f webcounter-postgres
```

DSN для підключення:

```
postgres://counter_user:counter_pass@localhost:5432/counter_db
```

#### Варіант 2: Локальна інсталяція (Ubuntu/Debian)

```bash
sudo apt-get update
sudo apt-get install -y postgresql
sudo service postgresql start
```

Створення користувача і БД:

```bash
sudo -u postgres psql <<'SQL'
CREATE USER counter_user WITH PASSWORD 'counter_pass';
CREATE DATABASE counter_db OWNER counter_user;
GRANT ALL PRIVILEGES ON DATABASE counter_db TO counter_user;
SQL
```

DSN для підключення:

```
postgres://counter_user:counter_pass@localhost:5432/counter_db
```

### Підключення сервера до PostgreSQL

1. Встановіть залежності:

   ```bash
   pip install -r requirements.txt
   ```

2. Запустіть сервер у режимі PostgreSQL:

   ```bash
   STORAGE_MODE=postgres \
   POSTGRES_DSN="postgres://counter_user:counter_pass@localhost:5432/counter_db" \
   uvicorn server:app --host 0.0.0.0 --port 8080
   ```

> Під час старту сервер сам створює таблицю `user_counter` і початковий запис для `user_id=1`.

### Підготовка та запуск сценаріїв Task 2

1. Створіть таблицю та рядок лічильника:

   ```bash
   python postgres_counter.py --dsn "postgres://counter_user:counter_pass@localhost:5432/counter_db" \
     --scenario in-place --clients 10 --requests-per-client 10000 --prepare --reset
   ```

2. Запустіть будь-який сценарій:

   ```bash
   python postgres_counter.py --dsn "postgres://counter_user:counter_pass@localhost:5432/counter_db" \
     --scenario row-locking --clients 10 --requests-per-client 10000 --reset
   ```

### Тест продуктивності для Web-counter (10 клієнтів × 10K)

1. Запустіть сервер у режимі PostgreSQL (див. вище).
2. Запустіть клієнт:

   ```bash
   python client.py http://localhost:8080 --clients 10 --requests-per-client 10000
   ```

Очікуване значення `count` після завершення — `100000`.

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
