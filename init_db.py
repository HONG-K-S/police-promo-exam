from app import app
from models import db, init_db, create_initial_data
from models.user import User

def init_database():
    with app.app_context():
        # 데이터베이스 초기화
        init_db(app)
        
        # 초기 데이터 생성
        create_initial_data()
        
        print('데이터베이스가 초기화되었습니다.')

if __name__ == '__main__':
    init_database() 