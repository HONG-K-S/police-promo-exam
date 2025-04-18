from app import app
from models.category import Category

with app.app_context():
    categories = Category.query.all()
    if not categories:
        print('No categories found.')
    else:
        for category in categories:
            print(f'Category: id={category.id}, name={category.name}') 