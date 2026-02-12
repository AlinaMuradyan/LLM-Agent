import mysql.connector
from config import MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE

def test_connection():
    try:
        print(f"Connecting to {MYSQL_DATABASE} on {MYSQL_HOST}...")
        conn = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE
        )
        if conn.is_connected():
            print("Successfully connected to the database!")
            cursor = conn.cursor()
            cursor.execute("SHOW TABLES;")
            tables = cursor.fetchall()
            print("Tables found in database:")
            for table in tables:
                print(f"- {table[0]}")
            conn.close()
        else:
            print("Connection failed.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_connection()
