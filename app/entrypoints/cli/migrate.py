"""CLI-обёртка над Alembic. Запуск:

    python -m app.entrypoints.cli.migrate upgrade
    python -m app.entrypoints.cli.migrate downgrade -1
    python -m app.entrypoints.cli.migrate revision -m "add foo"
    python -m app.entrypoints.cli.migrate current
    python -m app.entrypoints.cli.migrate history

Composition root для миграций — знает где лежит alembic.ini, можно подменить если надо.
"""
import sys
from pathlib import Path
from alembic.config import Config
from alembic import command


ALEMBIC_INI = Path(__file__).parent.parent.parent / "infra" / "db" / "alembic.ini"


def _cfg() -> Config:
    return Config(str(ALEMBIC_INI))


def main(argv: list[str]) -> None:
    if not argv:
        print(__doc__)
        return

    cmd, *args = argv
    cfg = _cfg()

    if cmd == "upgrade":
        target = args[0] if args else "head"
        command.upgrade(cfg, target)
    elif cmd == "downgrade":
        target = args[0] if args else "-1"
        command.downgrade(cfg, target)
    elif cmd == "revision":
        msg = None
        autogenerate = True
        i = 0
        while i < len(args):
            if args[i] == "-m":
                msg = args[i + 1]
                i += 2
            elif args[i] == "--no-autogenerate":
                autogenerate = False
                i += 1
            else:
                i += 1
        if not msg:
            print("usage: revision -m 'message' [--no-autogenerate]")
            sys.exit(1)
        command.revision(cfg, message=msg, autogenerate=autogenerate)
    elif cmd == "current":
        command.current(cfg, verbose=True)
    elif cmd == "history":
        command.history(cfg, verbose=True)
    elif cmd == "stamp":
        target = args[0] if args else "head"
        command.stamp(cfg, target)
    else:
        print(f"unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main(sys.argv[1:])
