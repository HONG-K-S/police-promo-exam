from app import app, db
from models import Category

def cleanup_categories():
    with app.app_context():
        try:
            # Delete all categories
            Category.query.delete()
            db.session.commit()
            print("All categories have been deleted successfully.")
        except Exception as e:
            db.session.rollback()
            print(f"Error occurred: {str(e)}")

if __name__ == '__main__':
    cleanup_categories() 