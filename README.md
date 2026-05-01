# Oglasi.me — Montenegro Classifieds

Доска объявлений Черногории. Агрегатор-первый: парсим Telegram-каналы и FB-группы, показываем у себя как полноценные карточки, нативный постинг тоже сразу. Мультиязычность: `me` (Crnogorski), `ru`, `en`.

## Stack

| слой | технология |
|---|---|
| Web framework | FastAPI |
| ORM | SQLAlchemy 2.0 (async) |
| Migrations | Alembic |
| DB | SQLite (dev) → Postgres (prod) |
| Templates | Jinja2 |
| UI interactivity | HTMX |
| CSS | Tailwind (CDN) |
| Admin panel | SQLAdmin |
| Scrapers | Telethon (Telegram), позже Playwright (FB/OLX) |
| LLM (parsing + translation) | Anthropic SDK (Claude Haiku) |
| Config | pydantic-settings |

---

## Архитектура

**Modular Monolith + Hexagonal внутри каждого модуля + vertical slicing по доменам.**

Подход вдохновлён [Cosmic Python](https://www.cosmicpython.com), но с поправками: мы держим N bounded contexts (у них 1), используем declarative SQLAlchemy mapping (у них imperative), `typing.Protocol` вместо `abc.ABC`, FastAPI Depends вместо ручного `bootstrap.py`. Unit of Work и Domain Events не используем пока не появится реальная нужда.

**Принципы:**

- **vertical slicing** — код сгруппирован по бизнес-доменам, не по техническим слоям
- **гексагональность внутри модуля** — бизнес-логика не знает про SQLAlchemy/Telethon/Anthropic, только про свои `ports/` интерфейсы
- **driving (inbound) ≠ adapter** — HTTP/CLI это `entrypoints/`, ничего не "адаптируют" к портам, просто зовут сервисы
- **driven (outbound) = adapter** — реальный Protocol-port + N реализаций, polymorphism есть
- **кросс-модульное взаимодействие — только через `__init__.py` соседа.** Прямой импорт публичного API: `from app.modules.listings import post_listing`. Лезть внутрь чужих `models/`/`adapters/`/`services/` — запрещено. Циклы запрещены. Подробнее в разделе "Правила зависимостей" ниже.

---

## Структура папок

```
classfieds/
│
├── app/
│   ├── modules/                      # БИЗНЕС-ДОМЕНЫ (vertical slicing)
│   │   ├── listings/                 # ★ ядро — объявления
│   │   ├── catalog/                  # категории (потом города)
│   │   ├── users/                    # юзеры, auth
│   │   ├── sources/                  # реестр источников (TG-каналы, FB-группы)
│   │   ├── scraping/                 # скрейпинг + оркестрация импорта
│   │   └── translation/              # LLM-парсинг и перевод
│   │
│   ├── entrypoints/                  # КТО ЗОВЁТ систему снаружи
│   │   ├── http/                     # FastAPI app, routes, admin, шаблоны
│   │   └── cli/                      # CLI команды (cron, скрейпер)
│   │
│   ├── infra/                        # ТЕХНИЧЕСКИЙ glue
│   │   ├── config.py                 # pydantic Settings из .env
│   │   ├── i18n.py                   # функция t(key, lang)
│   │   └── db/                       # вся БД-инфра в одной папке
│   │       ├── __init__.py           # реэкспорт Base, engine, SessionLocal, transaction
│   │       ├── engine.py             # async engine, Base, session, transaction()
│   │       ├── alembic.ini           # конфиг Alembic — рядом со своими миграциями
│   │       └── migrations/           # Alembic миграции
│   │           ├── env.py
│   │           └── versions/
│   │
│   ├── shared/                       # DDD Shared Kernel — пустой пока
│   │                                 # (только когда что-то реально шарится между 2+ модулями)
│   │
│   └── main.py                       # ASGI export: app = create_app()
│
├── requirements.txt
├── .env / .env.example
└── dev.db                            # SQLite для дева (gitignored)
```

### Структура каждого модуля (одинаковая для всех)

```
modules/<domain>/
├── __init__.py                       # ★ ПУБЛИЧНОЕ API — единственная точка входа извне
│                                     # реэкспортит то что соседи могут юзать (entities, services)
│
├── models/                           # доменные определения (отражения реального мира)
│   ├── __init__.py                   # реэкспорт всего наружу
│   │
│   │   # ★ ОДИН ФАЙЛ = ОДИН КОНЦЕПТ. Разбиваем по смыслу — сколько концептов, столько файлов.
│   │   # Внутри файла лежит entity + её enum + её errors + связанные с ней методы.
│   │
│   ├── user.py                       # User (entity) + UserStatus (enum) + UserNotFound (error) — всё про юзера
│   ├── vip_user.py                   # VipUser — отдельный концепт → отдельный файл
│   ├── listing.py                    # Listing + ListingImage + ListingStatus + ListingNotFound
│   ├── money.py                      # Money (value object) — отдельная сущность → свой файл
│   └── contact.py                    # ContactInfo — отдельный value object
│
├── ports/                            # контракты с внешним миром (Protocol-интерфейсы)
│   └── repository.py                 # 1 driven port на модуль (стремимся)
│
├── adapters/                         # driven adapters — реализации портов
│   ├── orm.py                        # SQLAlchemy ORM-таблицы
│   ├── mappers.py                    # entity ↔ ORM конверсия
│   └── sqla_repository.py            # SqlaListingRepository реализует ListingRepository
│
└── services/                         # сервисы — use cases модуля
    ├── list_recent.py
    ├── get_listing.py
    └── post_listing.py
```

**Что куда кладётся** — короткая шпаргалка:

| папка | что лежит | критерий |
|---|---|---|
| `models/` | модели | **отражение реального концепта** домена (entity, value object, enum, error) |
| `ports/` | порты | **контракт заявленный доменом** — "что мне нужно от мира" (часть домена, не инфра) |
| `services/` | сервисы | use cases — операции домена (по умолчанию функции; класс только если есть состояние между вызовами — кеш, соединение, счётчик. Много зависимостей не повод — заверни их в dataclass-bag) |
| `adapters/` | адаптеры | реализации портов — **единственный нечистый слой** где живёт инфраструктура (БД/API/файлы) |

### Структура `entrypoints/http/`

```
entrypoints/http/
├── app.py                            # create_app() — собирает middleware, роуты, admin
├── middleware.py                     # LanguageMiddleware (resolve lang из URL)
├── admin.py                          # SQLAdmin instance + ModelView для всех ORM
├── templates_setup.py                # Jinja2Templates instance + globals
├── deps/                             # DI-фабрики (composition root для HTTP)
│   ├── core.py                       # session, lang
│   ├── listings.py                   # listing_repo
│   ├── catalog.py                    # category_repo
│   ├── ...
│   └── translation.py                # translator (singleton)
├── routes/                           # FastAPI APIRouter'ы по концерну/домену
│   ├── home.py                       # GET /{lang}/ — кросс-модульный
│   ├── listings.py                   # GET /{lang}/l/{id}, /translate (HTMX)
│   └── ...
├── templates/                        # Jinja .html (один root)
│   ├── base.html
│   ├── home.html
│   ├── listing_detail.html
│   └── _description.html             # HTMX-партиалы
└── locale/                           # UI-строки
    ├── me.json
    ├── ru.json
    └── en.json
```

---

## Правила зависимостей

```
entrypoints/http   →  modules/<m>/services  →  modules/<m>/ports
entrypoints/cli    →  modules/<m>/services  →  modules/<m>/ports
modules/<m>/adapters    ─реализуют→         modules/<m>/ports
infra/, shared/    ←─── НИКОГДА не импортят из modules/, entrypoints/
```

### Главное правило кросс-модульного импорта

**Между модулями зовём только через `__init__.py` соседа. Никогда — внутрь его потрохов.**

```python
# ✅ МОЖНО
from app.modules.listings import post_listing, Listing
from app.modules.users import User, get_user
from app.modules.translation import Translator, translate_description

# ❌ НЕЛЬЗЯ — лезем мимо публичного API
from app.modules.listings.services.post_listing import post_listing
from app.modules.listings.adapters.orm import ListingORM
from app.modules.listings.models.listing import Listing
from app.modules.listings.ports.repository import ListingRepository
```

`__init__.py` модуля — это **единственный его публичный контракт**. Он реэкспортит то что разрешено снаружи. Если чего-то нет в `__init__.py` — значит это **внутренняя деталь**, и сосед лезть туда не имеет права.

**Зачем:** автор модуля свободен переименовывать/перемещать любые внутренние файлы пока не трогает `__init__.py`. Соседи не сломаются.

### Прочие правила

- **`infra/` и `shared/`** не знают про модули — только сверху вниз
- **Модули** не знают про FastAPI / Telethon / Anthropic — только через свои `ports/`
- **Только `entrypoints/http/deps/` и `entrypoints/cli/<cmd>.py`** знают про конкретные классы из `adapters/` (composition root)
- **`shared/`** — только для truly cross-domain типов (Money если уйдёт за пределы listings, UserId, DomainError, Page); **не помойка**
- **Циклов нет:** если модуль A импортит из модуля B, то B не должен импортить из A. Граф ацикличный.

---

## Поток HTTP запроса

```
браузер
   │ GET /me/
   ▼
LanguageMiddleware                    # resolve lang → request.state.lang
   │
   ▼
routes/home.py:home()                 # FastAPI маршрутизация
   │
   ▼
FastAPI Depends собирает:
   • get_session()       → AsyncSession
   • listing_repo(s)     → SqlaListingRepository (реализует ListingRepository port)
   • category_repo(s)    → SqlaCategoryRepository
   │
   ▼
listings.list_recent_listings(repo)   # use case — чистая функция
catalog.list_root_categories(repo)
   │
   ▼
Jinja Templates render home.html      # передаём entities в шаблон
   │
   ▼
HTML response
```

## Поток CLI запроса (скрейпер)

```
$ python -m app.entrypoints.cli.scrape
   │
   ▼
entrypoints/cli/scrape.py             # composition root для CLI
   │ собирает руками:
   │   • TelegramClient (Telethon)
   │   • TelegramScraper(client)            ← реализует Scraper port
   │   • SqlaSourceRepository(session)      ← реализует SourceRepository
   │   • SqlaListingRepository(session)     ← реализует ListingRepository
   │   • AnthropicTranslator(api_key)       ← реализует Translator
   │
   ▼
scraping.import_telegram_posts(...)   # оркестратор:
   ├─ список активных Telegram-источников ← sources.list_active_sources
   ├─ для каждого канала: scraper.fetch() → RawPost stream
   ├─ для каждого RawPost: translator.parse_post() → ParsedListing
   └─ listings.post_listing(...) сохраняет
```

---

## Запуск

### Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env
# отредактируй .env: ANTHROPIC_API_KEY, TELEGRAM_API_ID, TELEGRAM_API_HASH
```

### Миграции

```bash
.venv/bin/python -m app.entrypoints.cli.migrate upgrade               # применить
.venv/bin/python -m app.entrypoints.cli.migrate revision -m "msg"     # сгенерировать новую (autogenerate включён)
.venv/bin/python -m app.entrypoints.cli.migrate current               # текущая ревизия
.venv/bin/python -m app.entrypoints.cli.migrate history               # история
.venv/bin/python -m app.entrypoints.cli.migrate downgrade -1          # откатить на одну
```

### Dev сервер

```bash
.venv/bin/uvicorn app.main:app --reload
```

Открыть:
- `http://localhost:8000/` → редирект на язык юзера
- `http://localhost:8000/me/` → главная (черногорский)
- `http://localhost:8000/admin/` → SQLAdmin

### Скрейпер

```bash
.venv/bin/python -m app.entrypoints.cli.scrape
```

(сначала добавь Telegram-каналы в БД через админку или register_source service)

---

## Конвенции кода

- **Entities** — `@dataclass`, не классы с поведением. Поведение → `services/`
- **Ports** — `typing.Protocol`, не `abc.ABC` (структурная типизация)
- **Services** — функции, не классы (нет состояния → не нужен класс)
- **DTO для HTTP** — Pydantic в `entrypoints/http/schemas/<module>.py` (не лезут в домен)
- **Имена**: `<entity>_repo`, `<service_name>`, `Sqla<X>Repository`, `<Provider><Service>`
- **Cross-module** — только через `from app.modules.<m> import ...` (публичное API)

---

## Что почитать

- [Architecture Patterns with Python](https://www.cosmicpython.com) (Cosmic Python) — главный референс
- Code примеров: https://github.com/cosmicpython/code
- Hexagonal: оригинальная статья Cockburn 2005
- DDD: "Domain-Driven Design" Eric Evans (синяя книга) для теории, "Implementing DDD" Vaughn Vernon (красная) для практики
