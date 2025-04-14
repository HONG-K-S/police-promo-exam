from datetime import datetime
from . import db

class Topic(db.Model):
    """
    주제 계층 구조를 저장하는 모델
    트리 구조로 주제들을 계층적으로 관리
    """
    __tablename__ = 'topic'
    
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    
    # Relationships
    category = db.relationship('Category', back_populates='topics')
    questions = db.relationship('Question', back_populates='topic', cascade="all, delete-orphan")
    learning_sessions = db.relationship('LearningSession', back_populates='topic')
    
    def __repr__(self):
        return f'<Topic {self.title}>' 