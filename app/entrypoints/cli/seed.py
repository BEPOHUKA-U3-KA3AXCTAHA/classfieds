"""Сидеры:

    python -m app.entrypoints.cli.seed categories     # базовые категории на 3 языках
    python -m app.entrypoints.cli.seed sources        # Montenegro Telegram-каналы
    python -m app.entrypoints.cli.seed demo           # 15+ демо-объявлений (для увидеть UI)
    python -m app.entrypoints.cli.seed all            # всё подряд

Composition root для сидинга — собирает SQLA-репо руками, как и другие CLI-команды.
"""
import asyncio
import sys
import random
from datetime import datetime, timezone, timedelta
from decimal import Decimal

from app.infra.db import SessionLocal, engine, Base
# регистрируем все ORM-таблицы в metadata
from app.modules.listings.adapters import orm as _l  # noqa: F401
from app.modules.catalog.adapters import orm as _c  # noqa: F401
from app.modules.sources.adapters import orm as _s  # noqa: F401
from app.modules.users.adapters import orm as _u  # noqa: F401

from app.modules.catalog.adapters.orm import CategoryORM
from app.modules.sources.adapters.sqla_repository import SqlaSourceRepository
from app.modules.listings.adapters.sqla_repository import SqlaListingRepository
from app.modules.sources import register_source, SourceType
from app.modules.listings import post_listing, Money, ContactInfo


# ─────────────────────────── DATA ────────────────────────────

CATEGORIES = [
    # (slug, me, ru, en, icon)
    ("real_estate", "Nekretnine", "Недвижимость", "Real Estate", "🏠"),
    ("auto", "Auto", "Авто", "Vehicles", "🚗"),
    ("jobs", "Posao", "Работа", "Jobs", "💼"),
    ("services", "Usluge", "Услуги", "Services", "🛠"),
    ("electronics", "Elektronika", "Электроника", "Electronics", "📱"),
    ("furniture", "Namještaj", "Мебель", "Furniture", "🪑"),
    ("clothing", "Odjeća", "Одежда", "Clothing", "👕"),
    ("kids", "Za djecu", "Детям", "Kids", "🧸"),
    ("other", "Ostalo", "Другое", "Other", "📦"),
]


# Реальные публичные TG-каналы черногорских барахолок и нишевых классифайдов.
# Все проверены — работают на момент 2026. Список расширяй здесь и запускай `seed sources`
# (дедупит по имени, не дублирует).
MONTENEGRO_TG_CHANNELS = [
    ("montenegromarket",   "Объявления Черногория | Montenegro Market"),
    ("montenegrobye",      "Барахолка Черногория (Будва/Бар/Тиват/Подгорица/Котор)"),
    ("montenegro_market",  "♻️ Черногория барахолка объявления чат"),
    ("montedvizh",         "Аренда жилья до €500 (вся Черногория)"),
    ("kids_montenegro",    "Детские товары б/у"),
    ("monteresume",        "Резюме и услуги специалистов"),
    ("montekosmetolog",    "Красота, массаж, расходники"),
]


CITIES = ["Podgorica", "Budva", "Kotor", "Tivat", "Bar", "Herceg Novi", "Cetinje", "Ulcinj"]


DEMO_LISTINGS = [
    # (category_slug, city, title, description, original_lang, price, currency, telegram, days_ago)
    ("real_estate", "Budva", "Сдаю студию у моря, долгосрок", "Уютная студия 25м² в 5 минутах от Словенской Плажи. Балкон с видом на море, кондиционер, стиральная машина, новая мебель. Долгосрочно от 3 месяцев. Депозит = 1 месяц.", "ru", 450, "EUR", "olga_budva", 1),
    ("real_estate", "Podgorica", "Двушка в новостройке, City Kvart", "Квартира 65м² в новом доме, район Сити Квартал. Полностью меблирована, 2 спальни, кухня-гостиная, два балкона. Парковка и кладовка в подвале. Свободна с 15 числа.", "ru", 750, "EUR", "podg_renter", 0),
    ("real_estate", "Kotor", "Iznajmljujem stan u Starom Gradu", "Šarmantan jednosoban stan u srcu Starog Grada Kotor. 40m², potpuno renoviran, kameni zidovi, nova kuhinja. Idealno za par. Dugoročni najam.", "me", 600, "EUR", "stari_grad_rent", 2),
    ("auto", "Podgorica", "Продам Volkswagen Golf 2014", "VW Golf 7, 1.6 TDI, 156000 км, дизель, механика. Один владелец в Черногории, обслуживался у официалов. Без ДТП, фото по запросу. Торг уместен.", "ru", 8500, "EUR", "auto_pg", 3),
    ("auto", "Budva", "BMW X5 2018, full options", "BMW X5 xDrive30d, M-pakket, panoramski krov, koža, navigacija. Pređeno 89000km. Servisna istorija dostupna. Hitno radi selidbe.", "me", 32000, "EUR", "bmwbudva", 1),
    ("electronics", "Tivat", "iPhone 14 Pro 256GB Deep Purple", "Айфон 14 Pro, 256гб, фиолетовый. Состояние идеальное, всегда в чехле и со стеклом. Аккумулятор 96%. Полный комплект.", "ru", 750, "EUR", "tivat_tech", 0),
    ("electronics", "Podgorica", "MacBook Air M2 2023", "MacBook Air 13' M2, 16GB RAM, 512GB SSD, серый. Куплен в США, гарантия Apple до 2026. В идеале, очень мало использовался.", "ru", 1100, "EUR", "macsale_pg", 2),
    ("furniture", "Budva", "Угловой диван IKEA", "Диван IKEA Vimle 5-местный угловой, бежевый. Куплен 2 года назад, в отличном состоянии (был в гостевой комнате). Размер 280x240см. Самовывоз.", "ru", 480, "EUR", "ikea_budva", 5),
    ("jobs", "Kotor", "Ищем официантов в ресторан на сезон", "Ресторан в старом городе ищет официантов и помощников на летний сезон (май-октябрь). Опыт желателен, английский обязателен. Оплата + чаевые. Жильё не предоставляем.", "ru", None, None, "kotor_jobs", 1),
    ("jobs", "Podgorica", "Remote frontend dev (React/TypeScript)", "Looking for a senior frontend dev (React + TypeScript) to join our remote team. Salary 3000-4500 EUR/mo. Must be Montenegro tax resident. Send portfolio.", "en", 3500, "EUR", "podg_tech_jobs", 0),
    ("services", "Bar", "Перевозка вещей по всей Черногории", "Грузоперевозки по ЧГ, фургон до 1.5 тонн. Аккуратно, в срок, помогу с погрузкой. Также вывоз мусора, доставка мебели из IKEA Подгорица.", "ru", 30, "EUR", "moving_cg", 4),
    ("services", "Budva", "Уроки сербского / черногорского", "Носитель языка, преподаватель с опытом 10 лет. Индивидуально, онлайн или офлайн в Будве. Подготовка к B2 экзамену для ВНЖ.", "ru", 25, "EUR", "serbian_teacher", 3),
    ("kids", "Tivat", "Детская коляска Cybex Eezy", "Коляска-трость Cybex Eezy S Twist+2, серая. Состояние отличное, поворотное сиденье, дождевик, корзина. Купили в Германии, использовали 8 месяцев.", "ru", 180, "EUR", "tivat_kids", 6),
    ("clothing", "Herceg Novi", "Зимняя куртка Moncler, размер M", "Куртка Moncler оригинал, размер M, чёрная. Носилась 1 сезон, состояние отличное. Чек и упаковка есть.", "ru", 600, "EUR", "hn_fashion", 2),
    ("electronics", "Bar", "PS5 Slim + 2 джойстика + игры", "PlayStation 5 Slim Disc Edition, 2 джойстика DualSense, игры: Spider-Man 2, GTA V, FIFA 24. Гарантия до сентября.", "ru", 550, "EUR", "ps5_bar", 1),
    ("furniture", "Podgorica", "Trpezarijski sto + 6 stolica", "Drveni trpezarijski sto, 180x90cm, hrastovo drvo. Sa 6 stolica iste serije. Korišćeno, ali u dobrom stanju. Cijena za komplet.", "me", 320, "EUR", "podg_furniture", 4),
    ("auto", "Ulcinj", "Renault Clio 2016, otkup za gotovinu", "Renault Clio 4, 1.5 dCi, 2016, 142000km. Klima, parking senzori. Dobar za grad. Cijena fiksna, gotovinski.", "me", 5500, "EUR", "ulcinj_auto", 0),
]


# ─────────────────────────── SEED FNS ────────────────────────────

async def seed_categories(session) -> int:
    from sqlalchemy import select
    count = 0
    for i, (slug, me, ru, en, icon) in enumerate(CATEGORIES):
        existing = (await session.execute(select(CategoryORM).where(CategoryORM.slug == slug))).scalar_one_or_none()
        if existing is not None:
            continue
        session.add(CategoryORM(
            slug=slug, name_me=me, name_ru=ru, name_en=en, icon=icon, position=i,
        ))
        count += 1
    await session.flush()
    return count


async def seed_sources(session) -> int:
    repo = SqlaSourceRepository(session)
    count = 0
    # Telegram channels
    for name, label in MONTENEGRO_TG_CHANNELS:
        existing = await repo.get_by_name(SourceType.TELEGRAM, name)
        if existing is None:
            await register_source(repo, SourceType.TELEGRAM, name, url=f"https://t.me/{name}")
            count += 1
    # Mojkvadrat: один сорс — это весь сайт, scraper'у имя нужно только как метка
    if await repo.get_by_name(SourceType.MOJKVADRAT, "mojkvadrat.me") is None:
        await register_source(repo, SourceType.MOJKVADRAT, "mojkvadrat.me", url="https://www.mojkvadrat.me")
        count += 1
    # Polovni Auto: тоже один источник на весь сайт
    if await repo.get_by_name(SourceType.POLOVNI, "polovniautomobili.com") is None:
        await register_source(repo, SourceType.POLOVNI, "polovniautomobili.com", url="https://www.polovniautomobili.com")
        count += 1
    return count


async def seed_demo_listings(session) -> int:
    """Создаёт N демо-объявлений привязанных к первому Telegram-источнику.

    Безопасно для повторного запуска — проверяет внешний id чтобы не дублировать.
    """
    sources_repo = SqlaSourceRepository(session)
    listings_repo = SqlaListingRepository(session)

    sources = await sources_repo.list_active(type=SourceType.TELEGRAM)
    if not sources:
        print("  ! сначала запусти 'sources' чтобы добавить TG-каналы")
        return 0

    count = 0
    for i, (cat_slug, city, title, description, lang, price, currency, telegram, days_ago) in enumerate(DEMO_LISTINGS):
        external_id = f"demo-{i}"
        src = sources[i % len(sources)]

        # дедуп: пропускаем если уже создан
        existing = await listings_repo.get_by_external(src.id, external_id)
        if existing is not None:
            continue

        money = Money(amount=Decimal(str(price)), currency=currency or "EUR") if price else None
        await post_listing(
            listings_repo,
            source_id=src.id,
            title=title,
            description=description,
            original_lang=lang,
            title_translations={lang: title},  # пока без авто-перевода — добавим когда LLM подключим
            price=money,
            city=city,
            contact=ContactInfo(telegram=telegram),
            external_id=external_id,
            external_url=f"https://t.me/{src.name}/{external_id}",
            posted_at=datetime.now(timezone.utc) - timedelta(days=days_ago),
        )
        count += 1
    return count


# ─────────────────────────── ENTRY ────────────────────────────

COMMANDS = {
    "categories": seed_categories,
    "sources": seed_sources,
    "demo": seed_demo_listings,
}


async def main(argv: list[str]) -> None:
    if not argv or argv[0] not in (*COMMANDS, "all"):
        print(__doc__)
        sys.exit(1 if argv else 0)

    # на всякий — гарантируем что таблицы есть (если миграции ещё не прогнали)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with SessionLocal() as session:
        try:
            cmds = list(COMMANDS) if argv[0] == "all" else [argv[0]]
            for cmd in cmds:
                n = await COMMANDS[cmd](session)
                print(f"  ✓ {cmd}: добавлено {n}")
            await session.commit()
        except Exception:
            await session.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:]))
