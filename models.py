# 데이터베이스 모델을 정의하는 파일입니다.
from database import db  # database.py에서 데이터베이스 객체를 가져옵니다.
from datetime import datetime  # 날짜와 시간을 다루기 위한 파이썬 기본 라이브러리
from werkzeug.security import generate_password_hash, check_password_hash  # 비밀번호 해싱을 위한 Werkzeug 라이브러리

class Admin(db.Model):
    """
    관리자 계정을 관리하는 모델입니다.
    """
    id = db.Column(db.Integer, primary_key=True)  # 관리자 ID (기본키)
    username = db.Column(db.String(80), unique=True, nullable=False)  # 관리자 아이디 (중복 불가)
    password_hash = db.Column(db.String(128))  # 해시된 비밀번호
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # 계정 생성 시간
    
    def set_password(self, password):
        """
        비밀번호를 해시하여 저장하는 메서드입니다.
        """
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """
        입력된 비밀번호가 저장된 해시와 일치하는지 확인하는 메서드입니다.
        """
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        """
        Admin 객체를 문자열로 표현할 때 사용되는 메서드입니다.
        """
        return f'<Admin {self.username}>'

class Category(db.Model):
    """
    문제 카테고리를 관리하는 모델입니다.
    """
    id = db.Column(db.Integer, primary_key=True)  # 카테고리 ID (기본키)
    name = db.Column(db.String(100), nullable=False)  # 카테고리 이름
    parent_id = db.Column(db.Integer, db.ForeignKey('category.id'))  # 상위 카테고리 ID (자기 참조)
    questions = db.relationship('Question', backref='category', lazy=True)  # 이 카테고리에 속한 문제들
    children = db.relationship('Category', backref=db.backref('parent', remote_side=[id]))  # 하위 카테고리들
    
    def __repr__(self):
        """
        Category 객체를 문자열로 표현할 때 사용되는 메서드입니다.
        """
        return f'<Category {self.name}>'

class Question(db.Model):
    """
    문제를 관리하는 모델입니다.
    """
    id = db.Column(db.Integer, primary_key=True)  # 문제 ID (기본키)
    question_text = db.Column(db.Text, nullable=False)  # 문제 내용
    option1 = db.Column(db.String(200), nullable=False)  # 보기 1
    option2 = db.Column(db.String(200), nullable=False)  # 보기 2
    option3 = db.Column(db.String(200), nullable=False)  # 보기 3
    option4 = db.Column(db.String(200), nullable=False)  # 보기 4
    correct_answer = db.Column(db.Integer, nullable=False)  # 정답 (1~4)
    explanation = db.Column(db.Text)  # 문제 해설
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)  # 속한 카테고리 ID
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # 문제 생성 시간
    
    def __repr__(self):
        """
        Question 객체를 문자열로 표현할 때 사용되는 메서드입니다.
        """
        return f'<Question {self.id}>' 