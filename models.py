# 데이터베이스 모델을 정의하는 파일입니다.
from datetime import datetime  # 날짜와 시간을 다루기 위한 파이썬 기본 라이브러리
from werkzeug.security import generate_password_hash, check_password_hash  # 비밀번호 해싱을 위한 Werkzeug 라이브러리
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """
    사용자 정보를 저장하는 모델
    UserMixin을 상속받아 Flask-Login과 호환되도록 함
    """
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    name = db.Column(db.String(100))
    rank = db.Column(db.String(50))  # 계급
    department = db.Column(db.String(100))  # 부서
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # 관계 설정
    answer_records = db.relationship('AnswerRecord', backref='user', lazy=True)
    
    def set_password(self, password):
        """비밀번호 해싱"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """비밀번호 확인"""
        return check_password_hash(self.password_hash, password)

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

class Topic(db.Model):
    """
    주제 계층 구조를 저장하는 모델
    트리 구조로 주제들을 계층적으로 관리
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # 주제 이름
    parent_id = db.Column(db.Integer, db.ForeignKey('topic.id'), nullable=True)  # 상위 주제 ID
    level = db.Column(db.Integer, nullable=False)  # 주제 계층 레벨 (1: 최상위, 2: 1차 자식, ...)
    is_final = db.Column(db.Boolean, default=False)  # 최종 주제 여부
    has_statements = db.Column(db.Boolean, default=False)  # 설명 문장 존재 여부
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 자기 참조 관계 설정
    children = db.relationship('Topic', 
                             backref=db.backref('parent', remote_side=[id]),
                             lazy=True)
    
    # 관계 설정
    statements = db.relationship('Statement', backref='topic', lazy=True)

class Statement(db.Model):
    """
    설명 문장을 저장하는 모델
    각 문장은 특정 최종 주제에 속하며, 옳은/틀린 지문 여부와 해설을 포함
    """
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)  # 설명 문장 내용
    is_correct = db.Column(db.Boolean, nullable=False)  # True: 옳은 지문, False: 틀린 지문
    explanation = db.Column(db.Text, nullable=False)  # 해당 문장에 대한 해설
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'), nullable=False)  # 속한 최종 주제
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 관계 설정
    correct_answers = db.relationship('AnswerRecord', 
                                    foreign_keys='AnswerRecord.correct_statement_id',
                                    backref='correct_statement', 
                                    lazy=True)
    selected_answers = db.relationship('AnswerRecord', 
                                     foreign_keys='AnswerRecord.selected_statement_id',
                                     backref='selected_statement', 
                                     lazy=True)

class AnswerRecord(db.Model):
    """
    사용자의 답안 기록을 저장하는 모델
    문제 풀이 이력과 결과를 추적
    """
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    question_path = db.Column(db.String(500), nullable=False)  # 문제 경로 (예: [경찰실무종합][실무총론][수사기본])
    selected_statement_id = db.Column(db.Integer, db.ForeignKey('statement.id'), nullable=False)  # 사용자가 선택한 답안
    correct_statement_id = db.Column(db.Integer, db.ForeignKey('statement.id'), nullable=False)  # 정답 문장
    is_correct = db.Column(db.Boolean, nullable=False)  # 정답 여부
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class LearningSession(db.Model):
    """
    학습 세션 정보를 저장하는 모델
    사용자의 학습 진행 상황을 추적
    """
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    start_topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'), nullable=False)  # 시작 주제
    total_questions = db.Column(db.Integer, nullable=False)  # 총 문제 수
    current_question = db.Column(db.Integer, default=1)  # 현재 문제 번호
    correct_count = db.Column(db.Integer, default=0)  # 정답 개수
    wrong_count = db.Column(db.Integer, default=0)  # 오답 개수
    is_completed = db.Column(db.Boolean, default=False)  # 학습 완료 여부
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)  # 학습 완료 시간
    
    # 관계 설정
    answer_records = db.relationship('AnswerRecord', backref='session', lazy=True) 