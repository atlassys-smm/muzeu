# Документы закупки цифровой экосистемы Музея

MkDocs Material с русскоязычным поиском и оглавлением двух исходных документов.

ТЗ разложено по 22 разделам и 12 приложениям. Разделы 9 и 15 дополнительно разбиты на подразделы. Порядок оценки разделён на три страницы. `verification/pages.json` задаёт порядок фрагментов для дословной сверки.

Для работы с требованиями открывайте нужный Markdown в `docs/technical-specification/` или `docs/evaluation/`: достаточно читать конкретный раздел. Оглавления находятся в `docs/technical-specification.md` и `docs/evaluation.md`. Старые браузерные закладки на якоря переводятся на новые страницы.

## Запуск

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/mkdocs serve --dev-addr 127.0.0.1:8000
```

Открыть http://127.0.0.1:8000/.

## Проверка

```sh
.venv/bin/python scripts/verify.py
.venv/bin/mkdocs build --strict
```

Исходные DOCX в `documents/` исключены из Git и не публикуются на сайте. Локальные файлы сохранены для повторной сверки. Контрольные суммы и эталонное содержимое находятся в `verification/`.
