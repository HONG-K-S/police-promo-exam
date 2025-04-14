# 데이터베이스 설정을 관리하는 파일입니다.
from flask_sqlalchemy import SQLAlchemy
import os
from sqlalchemy import text

# SQLAlchemy 객체 생성
db = SQLAlchemy()

def init_app(app):
    """
    Flask 애플리케이션에 데이터베이스를 초기화합니다.
    """
    app.config.setdefault('SQLALCHEMY_DATABASE_URI', 'sqlite:///police_promo.db')
    app.config.setdefault('SQLALCHEMY_TRACK_MODIFICATIONS', False)
    
    db.init_app(app)
    
    with app.app_context():
        try:
            # 데이터베이스 테이블 생성
            db.create_all()
            print("데이터베이스 테이블이 성공적으로 생성되었습니다.")
            
            # 데이터베이스 연결 테스트
            db.session.execute(text('SELECT 1'))
            db.session.commit()
            
        except Exception as e:
            print(f"데이터베이스 초기화 중 오류 발생: {str(e)}")
            db.session.rollback()
            raise

def init_db(app):
    """
    데이터베이스 테이블을 생성하는 함수입니다.
    """
    try:
        with app.app_context():
            db.create_all()
            print("데이터베이스 테이블이 성공적으로 생성되었습니다.")
    except Exception as e:
        print(f"데이터베이스 테이블 생성 중 오류 발생: {str(e)}")
        db.session.rollback() 