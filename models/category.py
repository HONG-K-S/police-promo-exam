from datetime import datetime
from . import db

class Category(db.Model):
    """
    문제 카테고리를 관리하는 모델입니다.
    계층 구조를 가진 카테고리 시스템을 구현합니다.
    """
    __tablename__ = 'category'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    parent_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 자기 참조 관계 설정
    subcategories = db.relationship('Category',
                                  backref=db.backref('parent', remote_side=[id]),
                                  lazy=True,
                                  primaryjoin="Category.parent_id==Category.id",
                                  cascade="all, delete-orphan")
    
    # 관계 설정
    topics = db.relationship('Topic', back_populates='category', cascade="all, delete-orphan")
    answer_records = db.relationship('AnswerRecord', back_populates='category')
    
    def __repr__(self):
        return f'<Category {self.name}>' 