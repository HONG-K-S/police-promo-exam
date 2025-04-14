# 데이터베이스 모델을 정의하는 파일입니다.
from datetime import datetime  # 날짜와 시간을 다루기 위한 파이썬 기본 라이브러리
from werkzeug.security import generate_password_hash, check_password_hash  # 비밀번호 해싱을 위한 Werkzeug 라이브러리
from flask_login import UserMixin
from database import db  # database.py에서 db 인스턴스를 가져옵니다.

class User(UserMixin, db.Model):
    """
    일반 사용자 계정을 관리하는 모델입니다.
    """
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    name = db.Column(db.String(80), nullable=False)
    rank = db.Column(db.String(20), nullable=False)
    department = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    def set_password(self, password):
        """
        비밀번호를 해시화하여 저장합니다.
        """
        self.password = generate_password_hash(password)
    
    def check_password(self, password):
        """
        입력된 비밀번호가 해시화된 비밀번호와 일치하는지 확인합니다.
        """
        return check_password_hash(self.password, password)

    def update_last_login(self):
        self.last_login = datetime.utcnow()
        db.session.commit()

    def __repr__(self):
        return f'<User {self.username}>'

class Category(db.Model):
    """
    문제 카테고리를 관리하는 모델입니다.
    계층 구조를 가진 카테고리 시스템을 구현합니다.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    parent_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 자기 참조 관계 설정
    subcategories = db.relationship('Category', backref=db.backref('parent', remote_side=[id]), lazy=True)
    questions = db.relationship('Question', backref='category', lazy=True)

    def __repr__(self):
        return f'<Category {self.name}>'

class Question(db.Model):
    """문제 모델"""
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    correct_answer = db.Column(db.String(200), nullable=False)
    explanation = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    answer_records = db.relationship('AnswerRecord', backref='question', lazy=True)

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
    selected_answer = db.Column(db.Integer, nullable=False)
    is_correct = db.Column(db.Boolean, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref='answer_records')
    category = db.relationship('Category', backref='answer_records')

    def __repr__(self):
        return f'<AnswerRecord {self.id}>' 