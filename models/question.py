from datetime import datetime
from models import db

class Question(db.Model):
    __tablename__ = 'question'
    
    id = db.Column(db.Integer, primary_key=True)
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    topic = db.relationship('Topic', back_populates='questions')
    category = db.relationship('Category', back_populates='questions')
    statements = db.relationship('Statement', back_populates='question', lazy=True)
    answer_records = db.relationship('AnswerRecord', back_populates='question', lazy=True)
    
    def __repr__(self):
        return f'<Question {self.title}>' 