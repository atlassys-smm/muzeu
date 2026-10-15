# Документы закупки цифровой экосистемы Музея

MkDocs Material с русскоязычным поиском и оглавлением двух исходных документов.

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
