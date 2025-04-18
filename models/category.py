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
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_leaf = db.Column(db.Boolean, default=False, nullable=False)
    order = db.Column(db.Integer, default=0)
    
    # 자기 참조 관계 설정
    subcategories = db.relationship('Category',
                                  backref=db.backref('parent', remote_side=[id]),
                                  lazy=True,
                                  primaryjoin="Category.parent_id==Category.id",
                                  cascade="all, delete-orphan",
                                  order_by="Category.order")
    
    # 관계 설정
    topics = db.relationship('Topic', back_populates='category', cascade="all, delete-orphan")
    answer_records = db.relationship('AnswerRecord', back_populates='category')
    questions = db.relationship('Question', back_populates='category', lazy=True)
    
    def __init__(self, name, description=None, parent_id=None, is_leaf=False, order=None):
        self.name = name
        self.description = description
        self.parent_id = parent_id
        self.is_leaf = is_leaf
        
        try:
            # order가 명시적으로 지정된 경우 해당 값을 사용
            if order is not None:
                self.order = order
            else:
                # 같은 레벨의 마지막 순서를 찾아 새로운 순서 설정
                if parent_id is not None:
                    max_order = db.session.query(db.func.max(Category.order)).filter_by(parent_id=parent_id).scalar()
                    self.order = (max_order or 0) + 1
                else:
                    max_order = db.session.query(db.func.max(Category.order)).filter_by(parent_id=None).scalar()
                    self.order = (max_order or 0) + 1
                
                # 동시성 문제를 방지하기 위해 즉시 커밋
                db.session.flush()
                
        except Exception as e:
            print(f"Error setting category order: {e}")
            # 기본값으로 설정
            self.order = 0
    
    def __repr__(self):
        return f'<Category {self.name}>'
    
    def get_full_path(self):
        """카테고리의 전체 경로를 반환합니다."""
        path = [self.name]
        current = self
        while current.parent:
            current = current.parent
            path.insert(0, current.name)
        return ' > '.join(path)
    
    @property
    def is_leaf_node(self):
        """이 카테고리가 리프 노드(자식이 없는 카테고리)인지 확인합니다."""
        return self.subcategories.count() == 0 or self.is_leaf 