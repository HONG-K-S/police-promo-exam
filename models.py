# 데이터베이스 모델을 정의하는 파일입니다.
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime  # 날짜와 시간을 다루기 위한 파이썬 기본 라이브러리
from werkzeug.security import generate_password_hash, check_password_hash  # 비밀번호 해싱을 위한 Werkzeug 라이브러리
from flask_login import UserMixin

db = SQLAlchemy()

class Admin(db.Model):
    """
    관리자 계정을 관리하는 모델입니다.
    """
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        """
        비밀번호를 해시화하여 저장합니다.
        """
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """
        입력된 비밀번호가 해시화된 비밀번호와 일치하는지 확인합니다.
        """
        return check_password_hash(self.password_hash, password)

class User(db.Model):
    """
    일반 사용자 계정을 관리하는 모델입니다.
    """
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    name = db.Column(db.String(100))
    rank = db.Column(db.String(50))
    department = db.Column(db.String(100))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 사용자의 답안 기록과의 관계 설정
    answer_records = db.relationship('AnswerRecord', backref='user', lazy=True)
    
    def set_password(self, password):
        """
        비밀번호를 해시화하여 저장합니다.
        """
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """
        입력된 비밀번호가 해시화된 비밀번호와 일치하는지 확인합니다.
        """
        return check_password_hash(self.password_hash, password)

class Category(db.Model):
    """
    문제 카테고리를 관리하는 모델입니다.
    계층 구조를 가진 카테고리 시스템을 구현합니다.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    is_correct = db.Column(db.Boolean, default=False)  # 이 카테고리가 정답인지 여부
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 자기 참조 관계 설정
    children = db.relationship('Category', backref=db.backref('parent', remote_side=[id]))
    # 문제와의 관계 설정
    questions = db.relationship('Question', backref='category', lazy=True)
    # 답안 기록과의 관계 설정
    answer_records = db.relationship('AnswerRecord', backref='category', lazy=True)

class Question(db.Model):
    """문제 모델"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text, nullable=False)  # 문제 제목 (카테고리 경로 포함)
    question_type = db.Column(db.String(20), nullable=False)  # 'correct' 또는 'incorrect' (옳은 것/틀린 것 고르기)
    statements = db.Column(db.JSON, nullable=False)  # 지문들을 JSON으로 저장
    correct_answer = db.Column(db.Integer, nullable=False)  # 정답 번호 (1~4)
    explanation = db.Column(db.Text, nullable=False)  # 해설
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Question {self.id}>'

class AnswerRecord(db.Model):
    """
    사용자의 답안 기록을 관리하는 모델입니다.
    """
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    selected_answer = db.Column(db.Integer, nullable=False)  # 1~4 사이의 값
    is_correct = db.Column(db.Boolean, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow) 