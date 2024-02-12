from DWX_ZeroMQ_Connector_v2_0_1_RC8 import DWX_ZeroMQ_Connector
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
            comment TEXT UNIQUE
        )
        '''
        cursor.execute(create_table_query)    

        conn.commit()
        print("Table created successfully!")

    except (Exception, psycopg2.Error) as error:
        print("Error while connecting to PostgreSQL:", error)

    finally:
        # Close the cursor and connection
        if conn:
            cursor.close()
            conn.close()

def drop_tables(table_names):
    conn_params = {
        'dbname': DB_NAME,
        'user': DB_USER,
        'password': DB_PASSWORD,
        'host': DB_HOST,
        'port': DB_PORT
    }
    
    try:
        # Connect to the database
        conn = psycopg2.connect(**conn_params)

        # Create a cursor object using the connection
        cursor = conn.cursor()

        # Drop each table in the list
        for table_name in table_names:
            cursor.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE")

        # Commit the transaction
        conn.commit()
        print("Tables dropped successfully!")

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
                ON CONFLICT DO NOTHING
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
                trade_id
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


def insert_data_trades_table(trades_data):
    conn_params = {
        'dbname': DB_NAME,
        'user': DB_USER,
        'password': DB_PASSWORD,
        'host': DB_HOST,
        'port': DB_PORT
    }
    
    inserted_rows = []
    removed_comments = []
    inserted_rows_data = {}  # Dictionary to hold the inserted rows' data
    
    try:
        # Connect to the database
        conn = psycopg2.connect(**conn_params)

        # Create a cursor object using the connection
        cursor = conn.cursor()

        # Insert data into the table and track inserted trade_ids
        inserted_trade_ids = set()
        trades = trades_data['_trades']
        for trade_id, trade_info in trades.items():
            cursor.execute("""
                INSERT INTO trades (action, magic, symbol, lots, type, open_price, open_time, SL, TP, pnl, comment)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (comment) DO NOTHING
                RETURNING *
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
                trade_id
            ))

            # Fetch the inserted row's data if it doesn't conflict
            row = cursor.fetchone()
            if row:
                inserted_trade_ids.add(row[0])
                inserted_rows.append(row[0])
                inserted_rows_data[row[0]] = {
                    '_symbol': row[3],
                    '_lots': row[4],
                    '_type': row[5],
                    '_SL': row[8],
                    '_TP': row[9],
                    '_comment': row[11]
                }

        # Fetch all rows from the database table that were not inserted
        cursor.execute("SELECT id, comment FROM trades")
        all_rows = cursor.fetchall()
        for row in all_rows:
            trade_id = row[0]
            if trade_id not in inserted_trade_ids:
                removed_comments.append(row[1])

        # Delete rows from the database table that were not inserted
        if inserted_trade_ids:
            cursor.execute("DELETE FROM trades WHERE id NOT IN %s", (tuple(inserted_trade_ids),))

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
    
    return inserted_rows_data, removed_comments


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


def insert_from_MT4():
    zmq = DWX_ZeroMQ_Connector()
    zmq._DWX_MTX_GET_ALL_OPEN_TRADES_()
    response = zmq._get_response_()
    
    insert_data_trades_table(response)


def make_trade(inserted):
    for ticket, trade_data in inserted.items():
        _zmq = DWX_ZeroMQ_Connector()
        _my_trade = _zmq._generate_default_order_dict()
        
        _my_trade['_symbol'] = trade_data['_symbol']
        _my_trade['_lots'] = trade_data['_lots']
        _my_trade['_type'] = trade_data['_type']
        _my_trade['_SL'] = trade_data['_SL']
        _my_trade['_TP']= trade_data['_TP']
        _my_trade['_comment'] = trade_data['_comment']
        
        _zmq._DWX_MTX_NEW_TRADE_(_order=_my_trade)
    

def close_trades(removed):
    for remove in removed:
        _zmq = DWX_ZeroMQ_Connector()
        _zmq._DWX_MTX_CLOSE_TRADES_BY_COMMENT_(removed)
        

if __name__ == '__main__':
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
                '_comment': 't1'
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
                '_comment': 't2'
            }
        }
    }
    
    #drop_tables(['trades'])
    #create_trades_table()
    #inserted, removed = insert_data_trades_table(trades_data=trades_data)
    print(get_all_trades_data())
    #print(inserted)
    #print(removed)
    
