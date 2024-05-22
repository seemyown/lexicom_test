import logging
import random
import time

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


engine = create_engine(
    "postgresql://postgres:postgres@localhost:5432/task2db"
)
async_engine = create_async_engine(
    "postgresql+asyncpg://postgres:postgres@localhost:5432/task2db"
)


class ShortNames(Base):
    __tablename__ = 'short_names'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)
    status: Mapped[int] = mapped_column(nullable=True)


class FullNames(Base):
    __tablename__ = 'full_names'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)
    status: Mapped[int] = mapped_column(nullable=True)


Base.metadata.create_all(engine)


def fill_tables():
    shorts_tables = [
        ShortNames(
            name=f"nazvanie{i}",
            status=random.randint(0, 1)
        )
        for i in range(700000)
    ]
    logger.info(f"Таблица short заполнена")

    file_extensions = [
        '.txt', '.doc', '.docx', '.xls',
        '.xlsx', '.ppt', '.pptx', '.jpg',
        '.png', '.gif', '.pdf', '.zip', '.rar',
        '.tar', '.gz', '.mp4', '.mp3', '.wav',
        '.avi', '.mkv', '.html', '.css', '.js',
        '.py', '.java', '.php', '.cpp', '.c', '.h',
        '.json', '.xml', '.csv', '.tsv', '.sql',
        '.sh', '.bat'
    ]

    full_tables = [
        FullNames(
            name=f"nazvanie{i}{random.choice(file_extensions)}",
        )
        for i in range(500000)
    ]
    logger.info(f"Таблица full заполнена")

    with Session(engine) as session:
        session.add_all(shorts_tables + full_tables)
        session.commit()
        logger.info(f"Данные выгружены")


def update_full_tables_v1():
    logger.info("Запускаю решение через pandas")

    query_full = """
    select * from full_names
    """

    query_short = """
    select * from short_names
    """

    full_df = pd.read_sql(query_full, engine).drop(columns=["status"])
    short_df = pd.read_sql(query_short, engine).drop(
        columns=['id']
    ).rename(columns={"name": "short_name"})

    tm_start = time.time()
    full_df["clean_name"] = full_df["name"].str.replace(
        r'\.\w+$', "", regex=True
    )
    full_updated_df = pd.merge(
        full_df, short_df,
        how="left", left_on="clean_name",
        right_on="short_name"
    )

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
    logger.info(f"Время выполнения запроса: {time.time() - tm_start:.2f} сек")

    logger.info("Решение через pandas выполнено")


def clean_tables():
    logger.info("Запускаю очищение таблицы")
    query = text("""
    update full_names
    set status = null;
    """)

    with engine.connect() as connection:
        connection.execute(query)
        connection.commit()

    logger.info("Таблица очищена")


def update_full_tables_v2():
    logger.info("Запускаю решение через sql")

    query = text("""
    update full_names fn
    set status = sn.status
    from (
        select name, status
        from short_names
         ) sn
    where split_part(fn.name, '.', 1) = sn.name;
    """)

    tm_start = time.time()
    with engine.connect() as connection:
        connection.execute(query)
        connection.commit()
    logger.info(f"Время выполнения запроса: {time.time() - tm_start:.2f} сек")

    logger.info("Решение через sql выполнено")


if __name__ == '__main__':
    fill_tables()
    update_full_tables_v1()
    time.sleep(1)
    clean_tables()
    update_full_tables_v2()
