#from DWX_ZeroMQ_Connector_v2_0_1_RC8 import DWX_ZeroMQ_Connector
from datetime import datetime
import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

DB_NAME = os.environ.get("DB_NAME")
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_HOST = os.environ.get("DB_HOST")
DB_PORT = os.environ.get("DB_PORT")


def create_trades_table():
    conn_params = {
        'dbname': DB_NAME,
        'user': DB_USER,
        'password': DB_PASSWORD,
        'host': DB_HOST,
        'port': DB_PORT
    }
    
    try:
        # Connect to the database
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )

        # Create a cursor object using the connection
        cursor = conn.cursor()

        # Create table if not exists
        create_table_query = '''
        CREATE TABLE IF NOT EXISTS trades (
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
            comment TEXT
        )
        '''
        cursor.execute(create_table_query)    

        conn.commit()
        print("Data inserted successfully!")

    except (Exception, psycopg2.Error) as error:
        print("Error while connecting to PostgreSQL:", error)

    finally:
        # Close the cursor and connection
        if conn:
            cursor.close()
            conn.close()


def insert_data_trades_table(trades_data):
    conn_params = {
        'dbname': DB_NAME,
        'user': DB_USER,
        'password': DB_PASSWORD,
        'host': DB_HOST,
        'port': DB_PORT
    }
    
    try:
        # Connect to the database
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )

        # Create a cursor object using the connection
        cursor = conn.cursor()

        # Insert data into the table
        trades = trades_data['_trades']
        for trade_id, trade_info in trades.items():
            cursor.execute("""
                INSERT INTO trades (action, magic, symbol, lots, type, open_price, open_time, SL, TP, pnl, comment)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (open_time) DO NOTHING
            """, (
                trades_data['action'],
                trade_info['_magic'],
                trade_info['_symbol'],
                trade_info['_lots'],
                trade_info['_type'],
                trade_info['_open_price'],
                datetime.strptime(trade_info['_open_time'], '%Y.%m.%d %H:%M:%S'),
                trade_info['_SL'],
                trade_info['_TP'],
                trade_info['_pnl'],
                trade_info['_comment']
            ))

        # Commit the transaction
        conn.commit()
        print("Data inserted successfully!")

    except (Exception, psycopg2.Error) as error:
        print("Error while connecting to PostgreSQL:", error)

    finally:
        # Close the cursor and connection
        if conn:
            cursor.close()
            conn.close()


def get_all_trades_data():
    conn_params = {
        'dbname': DB_NAME,
        'user': DB_USER,
        'password': DB_PASSWORD,
        'host': DB_HOST,
        'port': DB_PORT
    }
    
    trades_data = {'action': 'OPEN_TRADES', '_trades': {}}
    
    try:
        # Connect to the database
        conn = psycopg2.connect(**conn_params)
        cursor = conn.cursor()

        # Fetch all data from the trades table
        cursor.execute("SELECT * FROM trades")
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
                '_comment': row[11]
            }
            trades_data['_trades'][trade_id] = trade_info

    except (Exception, psycopg2.Error) as error:
        print("Error while connecting to PostgreSQL:", error)

    finally:
        # Close the cursor and connection
        if conn:
            cursor.close()
            conn.close()
            
    return trades_data


def main():
    zmq = DWX_ZeroMQ_Connector()
    zmq._DWX_MTX_GET_ALL_OPEN_TRADES_()
    response = zmq._get_response_()
    
    return response


if __name__ == '__main__':
    #main()
    
    trades_data = {
        'action': 'OPEN_TRADES',
        '_trades': {
            139859769: {
                '_magic': 0,
                '_symbol': 'USDJPY',
                '_lots': 1.0,
                '_type': 1,
                '_open_price': 149.388,
                '_open_time': '2024.02.09 08:01:41',
                '_SL': 0.0,
                '_TP': 0.0,
                '_pnl': 8.7,
                '_comment': ''
            },
            139859768: {
                '_magic': 0,
                '_symbol': 'EURUSD',
                '_lots': 1.0,
                '_type': 0,
                '_open_price': 1.07825,
                '_open_time': '2024.02.09 08:01:26',
                '_SL': 0.0,
                '_TP': 0.0,
                '_pnl': 9.0,
                '_comment': ''
            }
        }
    }
    
    #insert_data_trades_table(trades_data=trades_data)
    print(get_all_trades_data() == trades_data)
    
    
