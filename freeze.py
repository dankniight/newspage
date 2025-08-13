from flask_frozen import Freezer
from app import app

# Initialize the database before freezing
import app as app_module
app_module.init_db()

# Make sure we have articles
try:
    saved_count = app_module.update_articles()
    print(f"Fetched and saved {saved_count} articles for static generation.")
except Exception as e:
    print(f"Error fetching articles: {e}")

freezer = Freezer(app)

if __name__ == '__main__':
    freezer.freeze()