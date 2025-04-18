from . import db

class Statement(db.Model):
    __tablename__ = 'statement'
    
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_correct = db.Column(db.Boolean, default=False)
    explanation = db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    
    # Relationships
    question = db.relationship('Question', back_populates='statements')
    selected_answer_records = db.relationship('AnswerRecord', foreign_keys='AnswerRecord.selected_statement_id', back_populates='selected_statement')
    correct_answer_records = db.relationship('AnswerRecord', foreign_keys='AnswerRecord.correct_statement_id', back_populates='correct_statement')
    
    def __repr__(self):
        return f'<Statement {self.content[:50]}...>' 