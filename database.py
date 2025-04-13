# 데이터베이스 설정을 관리하는 파일입니다.
from flask_sqlalchemy import SQLAlchemy
import os

# SQLAlchemy 객체 생성
db = SQLAlchemy()

def init_app(app):
    """
    Flask 애플리케이션에 데이터베이스를 초기화하는 함수입니다.
    """
    # 데이터베이스 설정
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///app.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # 데이터베이스 초기화
    db.init_app(app) 