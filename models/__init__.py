from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

db = SQLAlchemy()

def init_db(app):
    """데이터베이스 초기화 함수"""
    db.init_app(app)
    
    with app.app_context():
        # 데이터베이스 연결 테스트
        try:
            db.session.execute(text('SELECT 1'))
            print("Database connection successful!")
        except Exception as e:
            print(f"Database connection failed: {e}")
            return False

        # 테이블 생성
        db.create_all()
        
        return True

def create_initial_data():
    """초기 데이터 생성"""
    from .user import User
    
    try:
        # 관리자 계정 생성
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                name='관리자',
                rank='관리자',
                department='시스템관리',
                email='admin@example.com',
                phone='010-0000-0000',
                is_admin=True
            )
            admin.set_password('admin123!')
            db.session.add(admin)
        
        # 테스트 계정 생성
        test_user = User.query.filter_by(username='test').first()
        if not test_user:
            test_user = User(
                username='test',
                name='테스트',
                rank='순경',
                department='경찰서',
                email='test@example.com',
                phone='010-1111-1111',
                is_admin=False
            )
            test_user.set_password('test123!')
            db.session.add(test_user)
        
        db.session.commit()
        print("초기 데이터 생성 완료")
        return True
        
    except Exception as e:
        print(f"초기 데이터 생성 실패: {e}")
        db.session.rollback()
        return False

# 모델 import 순서 조정
from .user import User
from .category import Category
from .topic import Topic
from .statement import Statement
from .question import Question
from .answer_record import AnswerRecord
from .learning_session import LearningSession
from .wrong_answer_note import WrongAnswerNote

__all__ = ['db', 'init_db', 'create_initial_data', 'User', 'Category', 'Topic', 'Question', 'Statement', 'AnswerRecord', 'LearningSession', 'WrongAnswerNote'] 