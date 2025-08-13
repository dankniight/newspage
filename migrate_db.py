import sqlite3
import os

def migrate_database():
    # Check if the database exists
    if not os.path.exists('news.db'):
        print("Database not found. It will be created with the new schema.")
        return

    # Connect to the database
    conn = sqlite3.connect('news.db')
    c = conn.cursor()

    # Check if the link column already has a unique constraint
    c.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='articles'")
    result = c.fetchone()
    
    if result and 'link TEXT UNIQUE' in result[0]:
        print("Database already migrated.")
        conn.close()
        return

    print("Migrating database...")
    
    # Create a new table with the updated schema
    c.execute('''CREATE TABLE articles_new
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  title TEXT,
                  link TEXT UNIQUE,
                  published TEXT,
                  summary TEXT,
                  source TEXT,
                  image_url TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

    # Copy data from the old table, keeping only the first occurrence of each link
    c.execute('''INSERT INTO articles_new 
                 (title, link, published, summary, source, image_url, created_at)
                 SELECT title, link, published, summary, source, image_url, created_at
                 FROM articles
                 GROUP BY link''')  # This groups by link, keeping only the first occurrence
    
    # Count how many duplicates were removed
    c.execute("SELECT COUNT(*) FROM articles")
    old_count = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM articles_new")
    new_count = c.fetchone()[0]
    
    print(f"Removed {old_count - new_count} duplicate articles")
    
    # Drop the old table and rename the new one
    c.execute("DROP TABLE articles")
    c.execute("ALTER TABLE articles_new RENAME TO articles")
    
    # Create an index on the link column for faster lookups
    c.execute("CREATE INDEX IF NOT EXISTS idx_link ON articles(link)")
    
    conn.commit()
    conn.close()
    
    print("Database migration completed.")

if __name__ == "__main__":
    migrate_database()