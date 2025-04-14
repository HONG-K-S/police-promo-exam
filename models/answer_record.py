from . import db

class AnswerRecord(db.Model):
    __tablename__ = 'answer_record'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    selected_statement_id = db.Column(db.Integer, db.ForeignKey('statement.id'), nullable=False)
    correct_statement_id = db.Column(db.Integer, db.ForeignKey('statement.id'), nullable=False)
    is_correct = db.Column(db.Boolean, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    
    # Relationships
    user = db.relationship('User', back_populates='answer_records')
    question = db.relationship('Question', back_populates='answer_records')
    category = db.relationship('Category', back_populates='answer_records')
    selected_statement = db.relationship('Statement', foreign_keys=[selected_statement_id], back_populates='selected_answers')
    correct_statement = db.relationship('Statement', foreign_keys=[correct_statement_id], back_populates='correct_answers')
    
    def __repr__(self):
        return f'<AnswerRecord {self.user.username} - {self.question.title}>' 