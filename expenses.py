import argparse
import csv
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

DATA_FILE = Path.home() / ".expenses.csv"
FIELDNAMES = ["date", "amount", "category", "note"]


def ensure_file():
    """Создаёт файл с заголовками, если его ещё нет."""
    if not DATA_FILE.exists():
        with open(DATA_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()


def load_expenses() -> list[dict]:
    ensure_file()
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [row for row in reader]


def add_expense(amount: float, category: str, note: str = "", date: str | None = None):
    ensure_file()
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    with open(DATA_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writerow({
            "date": date,
            "amount": f"{amount:.2f}",
            "category": category,
            "note": note,
        })
    print(f"✅ Добавлено: {amount:.2f} ₽ — {category} ({date})")


def parse_date(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%d")


def filter_by_period(expenses: list[dict], period: str | None) -> list[dict]:
    if not period:
        return expenses

    now = datetime.now()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)

    if period == "today":
        start = today
    elif period == "week":
        start = today - timedelta(days=7)
    elif period == "month":
        start = today - timedelta(days=30)
    elif period == "year":
        start = today - timedelta(days=365)
    else:
        # Пытаемся распарсить как конкретную дату YYYY-MM-DD
        try:
            start = parse_date(period)
        except ValueError:
            print(f"⚠ Не понял период: {period}. Используй today/week/month/year или YYYY-MM-DD")
            return []

    result = []
    for e in expenses:
        try:
            d = parse_date(e["date"])
            if d >= start:
                result.append(e)
        except ValueError:
            continue
    return result


def cmd_list(period: str | None):
    expenses = filter_by_period(load_expenses(), period)
    if not expenses:
        print("Трат нет.")
        return

    total = 0.0
    print(f"\n{'Дата':<12} {'Сумма':>10} {'Категория':<15} Заметка")
    print("-" * 60)
    for e in sorted(expenses, key=lambda x: x["date"]):
        amount = float(e["amount"])
        total += amount
        print(f"{e['date']:<12} {amount:>9.2f}₽ {e['category']:<15} {e['note']}")
    print("-" * 60)
    print(f"{'ИТОГО':<12} {total:>9.2f}₽")


def cmd_stats(period: str | None):
    expenses = filter_by_period(load_expenses(), period)
    if not expenses:
        print("Трат нет.")
        return

    by_category = defaultdict(float)
    total = 0.0

    for e in expenses:
        amount = float(e["amount"])
        by_category[e["category"]] += amount
        total += amount

    print(f"\n📊 Статистика ({period or 'за всё время'})")
    print(f"Всего: {total:.2f} ₽\n")

    # Сортируем категории по убыванию суммы
    for category, amount in sorted(by_category.items(), key=lambda x: -x[1]):
        percent = (amount / total * 100) if total else 0
        bar = "█" * int(percent / 3)
        print(f"{category:<15} {amount:>9.2f}₽  {percent:>5.1f}%  {bar}")


def cmd_export(output: str):
    """Сохраняет CSV в указанное место (полезно для бэкапа)."""
    expenses = load_expenses()
    if not expenses:
        print("Нечего экспортировать.")
        return

    out = Path(output).expanduser().resolve()
    with open(out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(expenses)
    print(f"✅ Экспортировано в {out} ({len(expenses)} записей)")


def main():
    parser = argparse.ArgumentParser(
        description="Простой CLI-трекер расходов. Данные хранятся в ~/.expenses.csv"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # add
    p_add = sub.add_parser("add", help="Добавить трату")
    p_add.add_argument("amount", type=float, help="Сумма")
    p_add.add_argument("category", help="Категория (еда, транспорт, ...)")
    p_add.add_argument("--note", default="", help="Заметка")
    p_add.add_argument("--date", help="Дата в формате YYYY-MM-DD (по умолчанию сегодня)")

    # list
    p_list = sub.add_parser("list", help="Показать траты")
    p_list.add_argument("--period", help="today / week / month / year / YYYY-MM-DD")

    # stats
    p_stats = sub.add_parser("stats", help="Статистика по категориям")
    p_stats.add_argument("--period", help="today / week / month / year / YYYY-MM-DD")

    # export
    p_export = sub.add_parser("export", help="Экспортировать в CSV")
    p_export.add_argument("output", help="Путь к файлу")

    args = parser.parse_args()

    if args.command == "add":
        add_expense(args.amount, args.category, args.note, args.date)
    elif args.command == "list":
        cmd_list(args.period)
    elif args.command == "stats":
        cmd_stats(args.period)
    elif args.command == "export":
        cmd_export(args.output)


if __name__ == "__main__":
    main()