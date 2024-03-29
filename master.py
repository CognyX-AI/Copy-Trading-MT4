from DWX_ZeroMQ_Connector_v2_0_1_RC8 import DWX_ZeroMQ_Connector
from datetime import datetime
from time import sleep
import psycopg2
import requests
from dotenv import load_dotenv
import os
from io import StringIO
import sys
import ast

load_dotenv()

DB_NAME = os.environ.get("DB_NAME")
DB_NAME_MAIN = os.environ.get("DB_NAME_MAIN")
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_HOST = os.environ.get("DB_HOST")
DB_PORT = os.environ.get("DB_PORT")

conn = psycopg2.connect(
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT
)

cursor = conn.cursor()

conn_user = psycopg2.connect(
    dbname=DB_NAME_MAIN,
    user=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT
)

cursor_user = conn_user.cursor()
zmq = DWX_ZeroMQ_Connector()

MASTER_ID = os.environ.get("MASTER_ID")
sql_query = "SELECT username, password, account_type_stock FROM users_credentials_master_mt4 WHERE id = %s"
cursor_user.execute(sql_query, (MASTER_ID,))
result = cursor_user.fetchone()

MASTER_USERNAME, MASTER_PASSWORD, MASTER_IS_STOCK = result

def create_trade_tables():
    try:
        # Create table if not exists
        create_table_query = '''
        CREATE TABLE IF NOT EXISTS open_trades (
            id SERIAL PRIMARY KEY,
            action VARCHAR(50),
            magic INTEGER,
            symbol VARCHAR(50),
            lots FLOAT,
            type INTEGER,
            open_price FLOAT,
            open_time TIMESTAMP,
            SL FLOAT,
            TP FLOAT,
            pnl FLOAT,
            comment TEXT UNIQUE,
            master_username VARCHAR(50)
        )
        '''
        cursor.execute(create_table_query)    
        
        create_table_query = '''
        CREATE TABLE IF NOT EXISTS past_trades (
            id SERIAL PRIMARY KEY,
            action VARCHAR(50),
            magic INTEGER,
            symbol VARCHAR(50),
            lots FLOAT,
            type INTEGER,
            open_price FLOAT,
            open_time TIMESTAMP,
            SL FLOAT,
            TP FLOAT,
            pnl FLOAT,
            comment TEXT,
            master_username VARCHAR(50)
        )
        '''
        cursor.execute(create_table_query)    


        conn.commit()
        print("Table created successfully!")

    except (Exception, psycopg2.Error) as error:
        print("Error while connecting to PostgreSQL:", error)


def create_user_table():
    try:
        # Create table if not exists
        create_table_query = '''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50),
            password VARCHAR(50)
        )
        '''
        
        cursor.execute(create_table_query)    

        conn.commit()
        print("Table created successfully!")

    except (Exception, psycopg2.Error) as error:
        print("Error while connecting to PostgreSQL:", error)


def drop_tables(table_names):
    try:
        # Drop each table in the list
        for table_name in table_names:
            cursor.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE")

        # Commit the transaction
        conn.commit()
        print("Tables dropped successfully!")

    except (Exception, psycopg2.Error) as error:
        print("Error while connecting to PostgreSQL:", error)
        

def insert_data_trades_table(trades_data):   
    inserted_rows_data = {}
    removed_comments = []
    
    try:
        # Insert data into the table and track inserted trade_ids
        
        buffer = StringIO()
        sys.stdout = buffer
        zmq._DWX_MTX_GET_ACCOUNT_INFO_()
        print_output = buffer.getvalue()
        sys.stdout = sys.__stdout__
        account_dic = ast.literal_eval(print_output)
                
        trades = trades_data.get('_trades', {})
        orders = []
        for trade_id, trade_info in trades.items():
            orders.append(str(trade_id))
            cursor.execute("""
                INSERT INTO open_trades (action, magic, symbol, lots, type, open_price, open_time, SL, TP, pnl, comment, master_username)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (comment) DO NOTHING
                RETURNING *
            """, (
                trades_data.get('_action', ''),  # Use get method to avoid KeyError
                trade_info.get('_magic', 0),
                trade_info.get('_symbol', ''),
                trade_info.get('_lots', 0.0),
                trade_info.get('_type', 0),
                trade_info.get('_open_price', 0.0),
                datetime.strptime(trade_info.get('_open_time', ''), '%Y.%m.%d %H:%M:%S'),
                trade_info.get('_SL', 0.0),
                trade_info.get('_TP', 0.0),
                trade_info.get('_pnl', 0.0),
                trade_id,
                MASTER_USERNAME
            ))

            # Fetch the inserted row's data if it doesn't conflict
            row = cursor.fetchone()
            if row:
                inserted_rows_data[row[0]] = {
                    '_action': row[1],
                    '_magic': row[2],
                    '_symbol': row[3],
                    '_lots': row[4],
                    '_type': row[5],
                    '_open_price': row[6],
                    '_open_time': row[7].strftime('%Y.%m.%d %H:%M:%S'),
                    '_SL': row[8],
                    '_TP': row[9],
                    '_pnl': row[10],
                    '_comment': row[11],
                    '_master' : row[12],
                    '_is_stock' : MASTER_IS_STOCK,
                    '_master_balance' : account_dic['data'][0]['account_balance']
                }

        # Fetch all rows from the database table that were not inserted
        cursor.execute("SELECT id, comment FROM open_trades")
        all_rows = cursor.fetchall()
        for row in all_rows:
            trade_id = row[1]
            if trade_id not in orders:
                removed_comments.append(row[1])

        if removed_comments:
            for comment in removed_comments:
                cursor.execute("INSERT INTO past_trades (action, magic, symbol, lots, type, open_price, open_time, SL, TP, pnl, comment, master_username) SELECT action, magic, symbol, lots, type, open_price, open_time, SL, TP, pnl, comment, master_username FROM open_trades WHERE comment = %s", (comment,))
            
            cursor.execute("DELETE FROM open_trades WHERE comment IN %s", (tuple(removed_comments),))

        conn.commit()

    except (Exception, psycopg2.Error) as error:
        print("Error while connecting to PostgreSQL:", error)
            
    return inserted_rows_data, removed_comments


def get_all_trades_data():
    trades_data = {'action': 'OPEN_TRADES', '_trades': {}}
    
    try:
        # Fetch all data from the trades table
        cursor.execute("SELECT * FROM open_trades")
        rows = cursor.fetchall()

        # Loop through the rows and populate trades_data
        for row in rows:
            trade_id = row[0]
            trade_info = {
                '_magic': row[2],
                '_symbol': row[3],
                '_lots': row[4],
                '_type': row[5],
                '_open_price': row[6],
                '_open_time': row[7].strftime('%Y.%m.%d %H:%M:%S'),
                '_SL': row[8],
                '_TP': row[9],
                '_pnl': row[10],
                '_comment': row[11],
                '_master' : row[12]
            }
            trades_data['_trades'][trade_id] = trade_info
            
            cursor.close()
            conn.close()
    except Exception as error:
        print("Error while connecting to PostgreSQL:", error)            
            
    return trades_data


def insert_from_MT4():
    zmq._DWX_MTX_GET_ALL_OPEN_TRADES_()
    response = zmq._get_response_()
    
    if response:
        return insert_data_trades_table(response)
    
    return [], []
    
def get_all_users():
    try:
        cursor_user.execute("SELECT * FROM users_credentials_MT4 WHERE verification = TRUE AND is_active = TRUE AND master_username_id IS NOT NULL")
        rows = cursor_user.fetchall()
        return rows        

    except (Exception, psycopg2.Error) as error:
        print("Error while fetching data from users_credentials_MT4 table:", error)    


def make_trade_request(inserted):
    base_url = os.environ.get("BASE_URL")
    url = base_url + "/make-trades"
      
    try:
        response = requests.post(url, json=inserted)
        response.raise_for_status()
        print("Trades made successfully")
    except requests.exceptions.RequestException as e:
        print(f"Error making trades: {e}")


def close_trade_request(removed):
    base_url = os.environ.get("BASE_URL")
    url = base_url + "/close-trades"
    
    try:
        response = requests.post(url, json=removed)
        response.raise_for_status()
        print("Trades closed successfully")
    except requests.exceptions.RequestException as e:
        print(f"Error closing trades: {e}")

    
if __name__ == '__main__':
    
    # drop_tables(['open_trades', 'past_trades'])
    # create_trade_tables()
    # create_user_table()
    
    while True:
        sleep(3)
        users = get_all_users()
        inserted, removed = insert_from_MT4()
        print(inserted, removed)
        # make_trade_request(inserted)
        # close_trade_request(removed)