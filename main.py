from elasticsearch import Elasticsearch
from numpy import datetime_data
import pandas as pd
from fastapi import FastAPI, HTTPException
from typing import Optional
import psycopg2
import os


es_title = os.environ.get('ES_TITLE', "search-index")
sql_table_title = os.environ.get('PSQL_TITLE', "messages")
table_columns = ['text', 'created_date', 'rubrics']

def call_database():
    try:
        database = psycopg2.connect(
            host=os.environ.get('PSQL_ADDRESS', 'localhost'),
            port=os.environ.get('PSQL_PORT', '5432'),
            user=os.environ.get('PSQL_USER', 'postgres'),
            password=os.environ.get('PSQL_PASSWORD', None)
        )
        with database.cursor() as cursor:
            cursor.execute(
                "SELECT version();"
            )
            print(cursor.fetchone())
        return database
    except:
        return None

def call_es():
    
    ES = Elasticsearch(
        [{"host": os.environ.get('ES_ADDRESS', "localhost"), 
          "port": int(os.environ.get('ES_PORT', 9200)), 
          "scheme": "http"}]
    )
    if not ES.ping():
        return None
    else:
        return ES


app = FastAPI()

@app.get("/init_csv")
def init_csv() -> str:
    df = pd.read_csv("data/posts.csv", sep=",")
    ES = call_es()
    if ES:
        if not ES.indices.exists(index=es_title):
            ES.indices.create(index=es_title)
            for i, row in df.iterrows():
                ES.index(index=es_title, id=f"{i}", document=row.to_dict())
            report = 'es is done; '
        else:
            report = 'es is exists; '
    else:
        report = 'es is unreachable; '

    database = call_database()
    print(database)
    if database:    
        with database.cursor() as cursor:
            cursor.execute("select exists(select * from information_schema.tables where table_name=%s)", (sql_table_title,))
            if not cursor.fetchone()[0]:
               sql_command = f'CREATE TABLE {sql_table_title}'
               sql_command += '(id int,'
               for column in table_columns:
                   if column in ['text']:
                       sql_command += f'{column} text,'
                   else:
                       sql_command += f'{column} varchar(255),'        
               sql_command = sql_command[:-1]
               sql_command += ');'
               cursor.execute(sql_command)
               sql_primary_command = f'INSERT INTO {sql_table_title} (id, '
               for column in table_columns:
                   sql_primary_command += f'{column}, '
               sql_primary_command = sql_primary_command[:-2]
               sql_primary_command += ') VALUES ('
               for i, row in df.iterrows():
                   sql_secondary_command = sql_primary_command + "%s, "
                   values = [str(i)]                      
                   for column in table_columns:
                       values += [row[column]]
                       sql_secondary_command += f"%s, "
                   sql_secondary_command = sql_secondary_command[:-2]
                   sql_secondary_command += '), '
                   sql_secondary_command = sql_secondary_command[:-2]
                   sql_secondary_command += ';'
                   cursor.execute(sql_secondary_command, tuple(values))
               report += 'psql is done'
               database.commit()
            else:
               report += 'psql is exists'
        database.close()
    else:
        report += 'psql is unreachable'
    return report

@app.get("/search")
async def search(search_query: Optional[str] = None) -> list[dict]:
    ES = call_es()
    if ES is None:
        return [{'report': 'psql is unreachable'}]
    if search_query:
        search_result = ES.search(index=es_title, query={"match": {"text": {"query": search_query}}})['hits']['hits']
        suitable_ids = [row['_id'] for row in search_result]

        #print(suitable_ids)
        database = call_database()
        if database:
            with database.cursor() as cursor:
                columns = ['id'] + table_columns
                data = {}
                for column in columns:
                    data[column] = []
                for id in suitable_ids:
                    cursor.execute(f"SELECT * FROM {sql_table_title} WHERE id = %s;", [id])
                    row = cursor.fetchone()
                    for i in range(len(columns)):
                        data[columns[i]] += [list(row)[i]]
                print(data)
            database.close()

            suitable_df = pd.DataFrame.from_dict(data)
            suitable_df['created_date'] = pd.to_datetime(suitable_df['created_date'], dayfirst=True)
            suitable_df = suitable_df.sort_values(by='created_date', ascending=False).head(20)

            #print(suitable_df)

            search_result = []
            for i, row in suitable_df.iterrows():
                row_dict = {'id': i}
                for column in suitable_df.columns:
                    row_dict[column] = row[column]
                search_result += [row_dict]

            return search_result
        else:
            return [{'report': 'psql is unreachable'}]
    else:
        return []


@app.get("/remove")
def remover(id: Optional[int] = None) -> str:
    if id:
        id = int(id)

        database = call_database()
        if database:
            with database.cursor() as cursor:
                cursor.execute(f"DELETE FROM {sql_table_title} WHERE id = %s", [id])
            database.commit()
            database.close()
            ES = call_es()
            if ES:
                ES.delete(index=es_title, id=f'{id}')
            else:
                return 'es is unreachable'
            return f'{id} was removed'
        else:
            return 'psql is unreachable'
    else:
        return 'nothing to remove'
