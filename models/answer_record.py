from datetime import datetime
from . import db

class AnswerRecord(db.Model):
    __tablename__ = 'answer_record'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    learning_session_id = db.Column(db.Integer, db.ForeignKey('learning_session.id'), nullable=True)
    selected_statement_id = db.Column(db.Integer, db.ForeignKey('statement.id'), nullable=False)
    correct_statement_id = db.Column(db.Integer, db.ForeignKey('statement.id'), nullable=False)
    is_correct = db.Column(db.Boolean, nullable=False)
    time_taken = db.Column(db.Float, nullable=False)  # in seconds
    start_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, nullable=True, server_default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, nullable=True, server_default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    
    # Relationships
    user = db.relationship('User', back_populates='answer_records')
    question = db.relationship('Question', back_populates='answer_records')
    category = db.relationship('Category', back_populates='answer_records')
    learning_session = db.relationship('LearningSession', backref='answer_records')
    selected_statement = db.relationship('Statement', foreign_keys=[selected_statement_id], back_populates='selected_answer_records')
    correct_statement = db.relationship('Statement', foreign_keys=[correct_statement_id], back_populates='correct_answer_records')
    wrong_answer_note = db.relationship('WrongAnswerNote', back_populates='answer_record', uselist=False, lazy=True)
    
    def __repr__(self):
        return f'<AnswerRecord {self.id}>' 