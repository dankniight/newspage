import sqlite3

# Connect to the database
conn = sqlite3.connect('news.db')
cursor = conn.cursor()

# Get the schema information
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='articles'")
schema = cursor.fetchone()

if schema:
    print("Articles table schema:")
    print(schema[0])
else:
    print("Articles table not found")

conn.close()