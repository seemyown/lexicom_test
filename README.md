## Задание 1.
Для запуска решения нужно ввести.
```docker compose up -d``` в корневой папке.
Обращение по http://127.0.0.1/ - сделает редирект на страницу swagger`а. Запущенный проект включает в себя redis сервер. 
Поэтому можно будет Сразу протестировать решение.

## Задание 2.
В файле task_2.py необходимо в переменную DSN вставить строку подключения к БД. Затем просто запустить файл.
### Этап 1.
Будут созданы таблицы в базе данных.
### Этап 2.
Таблицы заполнятся тестовыми данными.
### Этап 3.
Запуститься решение с помощью Pandas.
### Этап 4.
Очиститься таблица full_names.
### Этап 5.
Запуститься решение с помощью SQL запроса.

### Все действия логгируются и выводят время выполнения решения.

### Описание решений.
#### pandas - 330,5 секунд
```python
query_full = """
select * from full_names
"""

query_short = """
select * from short_names
"""

full_df = pd.read_sql(query_full, engine).drop(columns=["status"])
short_df = pd.read_sql(query_short, engine).drop(columns=['id']).rename(columns={"name": "short_name"})

tm_start = time.time()
full_df["clean_name"] = full_df["name"].str.replace(r'\.\w+$', "", regex=True)
full_updated_df = pd.merge(full_df, short_df, how="left", left_on="clean_name", right_on="short_name")

full_updated_df.drop(columns=["clean_name", "short_name"], inplace=True)
with engine.connect() as connection:
    for _, row in full_updated_df.iterrows():
        query = text(f"""
        update full_names
        set status = {int(row["status"])}
        where id = {int(row["id"])}
        """)
        connection.execute(query)
    connection.commit()
```

#### SQL - 4,5 секунды
```sql
    update full_names fn
    set status = sn.status
    from (
        select name, status
        from short_names
         ) sn
    where split_part(fn.name, '.', 1) = sn.name;
```

