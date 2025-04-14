from . import db

class Question(db.Model):
    __tablename__ = 'question'
    
    id = db.Column(db.Integer, primary_key=True)
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    
    # Relationships
    topic = db.relationship('Topic', back_populates='questions')
    statements = db.relationship('Statement', back_populates='question', cascade="all, delete-orphan")
    answer_records = db.relationship('AnswerRecord', back_populates='question')
    
    def __repr__(self):
        return f'<Question {self.title}>' 