# Практика 2 — MVP «Календарь событий»

## Как работает система

Система реализована как набор независимых микросервисов, которые общаются между собой через HTTP (синхронно) и через очередь сообщений RabbitMQ (асинхронно).

### Поток данных: регистрация и вход

```
Браузер → API Gateway (nginx) → User Service → PostgreSQL
                                             → Redis (JWT-blacklist)
```

1. Пользователь отправляет форму регистрации или входа.
2. **API Gateway** принимает запрос на `localhost:80` и проксирует его на User Service по URL-префиксу (`/auth/`, `/users/`).
3. **User Service** регистрирует пользователя (хэширует пароль через bcrypt, сохраняет в PostgreSQL) или проверяет учётные данные и выдаёт JWT-токен.
4. При выходе токен помещается в **Redis** (blacklist) с TTL равным оставшемуся сроку жизни — это делает токен недействительным без хранения состояния сессии на сервере.

### Поток данных: создание события и напоминания

```
Браузер → API Gateway → Event Service → PostgreSQL
                                      → User Service (HTTP, за email/telegram_id)
                                      → RabbitMQ (публикует задачу)
```

1. Клиент посылает запрос с `Authorization: Bearer <token>`.
2. **API Gateway** проксирует запрос на Event Service (`/events/`, `/reminders/`).
3. **Event Service** декодирует JWT локально (используя тот же `SECRET_KEY` что и User Service) — без HTTP-вызова к User Service. Из токена извлекается `user_id`.
4. При создании напоминания Event Service вызывает `GET /users/me` на User Service (пробрасывая токен пользователя), чтобы получить email и `telegram_chat_id` — они нужны для последующей отправки уведомления.
5. Задача публикуется в **RabbitMQ** (очередь `reminder_tasks`) в виде JSON-сообщения с полными данными для отправки.

### Поток данных: отправка уведомлений

```
Scheduler Service → PostgreSQL (опрос каждые 60 с)
                 → RabbitMQ (публикует задачи)

RabbitMQ → Notification Service → SMTP (email)
                               → Telegram Bot API
```

1. **Scheduler Service** (Celery Beat) каждые 60 секунд выполняет запрос к PostgreSQL: выбирает напоминания со статусом `pending` и временем `remind_at ≤ now() + 70s`. Использует `FOR UPDATE SKIP LOCKED` — это гарантирует что два воркера не возьмут одну задачу при масштабировании.
2. Для каждого найденного напоминания Scheduler публикует сообщение в RabbitMQ и меняет статус на `processing`.
3. **Notification Service** подписан на очередь `reminder_tasks` через aio-pika. При получении сообщения:
   - Если канал `email` — отправляет письмо через SMTP (aiosmtplib).
   - Если канал `telegram` — делает POST на Telegram Bot API с текстом уведомления.
4. Notification Service работает в фоне внутри FastAPI lifespan — один asyncio task читает очередь, параллельно FastAPI отвечает на `/health`.

---

## Компоненты

### API Gateway (nginx)

Единая точка входа. Не содержит бизнес-логики — только маршрутизирует запросы по URL-префиксу:

| Префикс | Назначение |
|---|---|
| `/auth/`, `/users/` | → User Service :8001 |
| `/events/`, `/reminders/` | → Event Service :8002 |
| `/health` | → nginx (200 OK напрямую) |

Frontend обращается к Gateway, а не к сервисам напрямую — это позволяет менять топологию без изменения клиентского кода.

### User Service

FastAPI-приложение. Отвечает за идентичность пользователя.

- **Регистрация** (`POST /auth/register`): валидирует данные, хэширует пароль, сохраняет пользователя в PostgreSQL.
- **Вход** (`POST /auth/login`): проверяет пароль, создаёт JWT (HS256, `SECRET_KEY` из `.env`), возвращает токен.
- **Выход** (`POST /auth/logout`): помещает токен в Redis с `SETEX` (ключ = токен, TTL = оставшееся время жизни). При следующем запросе с этим токеном — сервис проверяет Redis и отклоняет.
- **Профиль** (`GET/PUT/DELETE /users/me`): возвращает/обновляет данные текущего пользователя (включая `telegram_chat_id`).

Зависимости: **PostgreSQL** (хранение), **Redis** (blacklist).

### Event Service

FastAPI-приложение. Отвечает за события и напоминания.

- **События** (`/events/`): CRUD. Каждое событие привязано к `user_id` из JWT. Запросы от других пользователей возвращают 403.
- **Напоминания** (`/reminders/`): CRUD. При создании/изменении — публикует сообщение в RabbitMQ.
- **Авторизация**: JWT декодируется локально через тот же `SECRET_KEY` — нет сетевого вызова к User Service при каждом запросе. User Service вызывается только при создании напоминания (за email/telegram_id пользователя).

Зависимости: **PostgreSQL** (хранение), **RabbitMQ** (публикация задач), **User Service** (за контактными данными при создании напоминания).

### Scheduler Service

Celery Beat воркер. Не имеет HTTP API.

- Каждые 60 секунд выполняет задачу `check_and_publish_due_reminders`.
- Читает PostgreSQL напрямую (синхронный psycopg2) — ищет напоминания `status='pending'` с `remind_at ≤ now()+70s`.
- Публикует каждое напоминание в RabbitMQ через синхронный pika.
- Меняет статус на `processing` и коммитит транзакцию.
- `FOR UPDATE SKIP LOCKED` — если запустить несколько воркеров, они не будут дублировать задачи.

Зависимости: **PostgreSQL** (опрос), **Redis** (брокер Celery, db=1), **RabbitMQ** (публикация).

### Notification Service

FastAPI-приложение с фоновым consumer'ом.

- При старте запускает `asyncio.create_task(start_amqp_consumer())` — бесконечный цикл чтения очереди.
- Получает сообщение → десериализует JSON → отправляет по каналам из поля `channels`:
  - `email`: aiosmtplib + MIME-письмо на адрес `user_email` из сообщения.
  - `telegram`: httpx POST на `api.telegram.org` с `telegram_chat_id` из сообщения.
- Ошибки (SMTP недоступен, Telegram вернул 400) логируются, сообщение подтверждается (ack) — очередь не блокируется.
- При потере соединения с RabbitMQ — автоматически переподключается (цикл с `try/except`, `sleep(5)`).

Зависимости: **RabbitMQ** (получение задач), **SMTP** (email), **Telegram Bot API** (telegram).

### Frontend (React SPA)

Single-page application. Собирается в статику (node:20 → nginx:alpine).

- Хранит JWT в `localStorage`. Axios-interceptor добавляет `Authorization: Bearer` к каждому запросу.
- При получении 401 — очищает хранилище и перенаправляет на `/login`.
- Все API-запросы идут на `localhost:80` (API Gateway) — не напрямую к сервисам.

Зависимости: **API Gateway** (все запросы через него).

---

## Хранилища данных

### PostgreSQL

Единая БД `calendar_db`. Содержит три прикладные таблицы:

| Таблица | Владелец | Содержимое |
|---|---|---|
| `users` | User Service | Профили, хэши паролей, telegram_chat_id |
| `events` | Event Service | События с временными метками |
| `reminders` | Event Service | Напоминания (status, channels, remind_at) |

Каждый сервис ведёт свою историю миграций Alembic в отдельной таблице (`alembic_version_user`, `alembic_version_event`) — чтобы не конфликтовать при одинаковых revision ID.

### Redis

Два логических раздела:

- **db=0** — JWT blacklist (User Service). Ключ = токен, TTL = оставшееся время жизни.
- **db=1** — брокер задач Celery (Scheduler Service).

### RabbitMQ

Одна очередь `reminder_tasks` (durable, persistent). Event Service и Scheduler Service публикуют задачи, Notification Service потребляет. Persistence гарантирует что сообщения не теряются при перезапуске брокера.

---

## Архитектура (таблица сервисов)

| Сервис | Порт (хост) | Технологии |
|---|---|---|
| **API Gateway** | `$HOST_PORT_API` (80) | nginx 1.27 |
| **User Service** | `$HOST_PORT_USER_SVC` (8001) | FastAPI, SQLAlchemy async, asyncpg, Redis |
| **Event Service** | `$HOST_PORT_EVENT_SVC` (8002) | FastAPI, SQLAlchemy async, asyncpg, aio-pika |
| **Scheduler Service** | — | Celery Beat, psycopg2, pika |
| **Notification Service** | `$HOST_PORT_NOTIFY_SVC` (8003) | FastAPI, aio-pika, aiosmtplib, httpx |
| **Frontend** | `$HOST_PORT_FRONTEND` (3000) | React, nginx |
| **PostgreSQL** | `$HOST_PORT_POSTGRES` (5432) | postgres:16-alpine |
| **Redis** | `$HOST_PORT_REDIS` (6379) | redis:7-alpine |
| **RabbitMQ** | `$HOST_PORT_RABBITMQ` (5672) | rabbitmq:3.13-management |

Хост-порты настраиваются в `.env` — можно изменить если стандартные порты заняты.

---

## Быстрый старт

```bash
cd practice2

# 1. Скопировать и заполнить переменные окружения
cp .env.example .env
# Отредактировать .env: SMTP_USER, SMTP_PASSWORD, TELEGRAM_BOT_TOKEN

# 2. Запустить все сервисы
docker-compose up --build -d

# 3. Проверить статус
docker-compose ps

# 4. Открыть браузер
#   Frontend:          http://localhost:3000
#   RabbitMQ UI:       http://localhost:15672  (rabbituser / rabbitpass)
#   User Service docs: http://localhost:8001/docs
#   Event Service docs:http://localhost:8002/docs
```

## Smoke-тест (curl)

```bash
# Регистрация
curl -X POST http://localhost/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@example.com","username":"demo","password":"password123"}'

# Логин → сохраняем токен
TOKEN=$(curl -s -X POST http://localhost/auth/login \
  -d "username=demo@example.com&password=password123" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Создать событие
curl -X POST http://localhost/events/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Встреча","start_time":"2025-06-01T10:00:00Z"}'

# Создать напоминание (за 2 минуты до события)
curl -X POST http://localhost/reminders/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"event_id":"<id события>","remind_at":"2025-06-01T09:58:00Z","channels":["email","telegram"]}'
```

## Запуск тестов

Тесты используют SQLite in-memory и моки внешних сервисов:

```bash
cd practice2/tests
pip install -r requirements-test.txt

# User Service (цель >= 85% покрытия)
pytest user-service/ -v --cov=../../services/user-service/app --cov-report=term-missing

# Event Service (цель >= 85%)
pytest event-service/ -v --cov=../../services/event-service/app --cov-report=term-missing

# Notification Service (цель >= 80%)
pytest notification-service/ -v --cov=../../services/notification-service/app --cov-report=term-missing
```

## Структура кода

```
practice2/
  docker-compose.yml
  .env.example
  .env                    <- создать из .env.example (не коммитить)
  services/
    api-gateway/          nginx.conf + Dockerfile
    user-service/         FastAPI + SQLAlchemy + Redis (JWT)
    event-service/        FastAPI + SQLAlchemy + aio-pika
    scheduler-service/    Celery Beat + pika
    notification-service/ FastAPI + aio-pika consumer
    frontend/             React SPA (multi-stage Docker)
  tests/
    user-service/         ~12 тестов
    event-service/        ~16 тестов
    notification-service/ ~11 тестов
```

## Переменные окружения

| Переменная | Описание |
|---|---|
| `SECRET_KEY` | Общий JWT-секрет для user-service и event-service |
| `SMTP_HOST/USER/PASSWORD` | Параметры SMTP для email-уведомлений |
| `TELEGRAM_BOT_TOKEN` | Токен Telegram-бота для уведомлений |
| `POSTGRES_USER/PASSWORD/DB` | Данные PostgreSQL |
| `RABBITMQ_DEFAULT_USER/PASS` | Данные RabbitMQ |
| `HOST_PORT_*` | Хост-порты контейнеров (менять при конфликтах) |
