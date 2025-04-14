from . import db

class LearningSession(db.Model):
    __tablename__ = 'learning_session'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'), nullable=False)
    start_time = db.Column(db.DateTime, server_default=db.func.now())
    end_time = db.Column(db.DateTime)
    total_questions = db.Column(db.Integer, default=0)
    correct_answers = db.Column(db.Integer, default=0)
    
    # Relationships
    user = db.relationship('User', back_populates='learning_sessions')
    topic = db.relationship('Topic', back_populates='learning_sessions')
    
    def __repr__(self):
        return f'<LearningSession {self.user.username} - {self.topic.title}>' 