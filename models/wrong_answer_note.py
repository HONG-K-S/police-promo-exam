from datetime import datetime
from . import db

class WrongAnswerNote(db.Model):
    __tablename__ = 'wrong_answer_note'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    answer_record_id = db.Column(db.Integer, db.ForeignKey('answer_record.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, nullable=False, server_default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    
    # Relationships
    user = db.relationship('User', back_populates='wrong_answer_notes')
    answer_record = db.relationship('AnswerRecord', back_populates='wrong_answer_note')
    
    def __repr__(self):
        return f'<WrongAnswerNote {self.id}>' 