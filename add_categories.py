from app import app
from models import db, Category, Topic

def add_categories():
    with app.app_context():
        # 1. 경찰법규 카테고리 추가
        police_law = Category(
            name='경찰법규',
            description='경찰법규에 관한 문제'
        )
        db.session.add(police_law)
        
        # 1-1. 경찰법 총칙
        police_law_general = Topic(
            title='경찰법 총칙',
            description='경찰법의 기본 원칙과 이론',
            category=police_law
        )
        db.session.add(police_law_general)
        
        # 1-2. 경찰조직법
        police_org_law = Topic(
            title='경찰조직법',
            description='경찰조직의 구성과 운영',
            category=police_law
        )
        db.session.add(police_org_law)
        
        # 1-3. 경찰작용법
        police_action_law = Topic(
            title='경찰작용법',
            description='경찰의 직무와 권한',
            category=police_law
        )
        db.session.add(police_action_law)
        
        # 2. 형법 카테고리 추가
        criminal_law = Category(
            name='형법',
            description='형법 총칙 및 각칙에 관한 문제'
        )
        db.session.add(criminal_law)
        
        # 2-1. 형법 총론
        criminal_law_general = Topic(
            title='형법 총론',
            description='형법의 기본 원칙과 이론',
            category=criminal_law
        )
        db.session.add(criminal_law_general)
        
        # 2-2. 형법 각론
        criminal_law_special = Topic(
            title='형법 각론',
            description='개별 범죄 유형별 형법',
            category=criminal_law
        )
        db.session.add(criminal_law_special)
        
        # 3. 형사소송법 카테고리 추가
        criminal_procedure = Category(
            name='형사소송법',
            description='형사소송 절차 및 증거에 관한 문제'
        )
        db.session.add(criminal_procedure)
        
        # 3-1. 형사소송법 수사 증거
        criminal_procedure_investigation = Topic(
            title='형사소송법 수사 증거',
            description='형사수사 절차와 방법 등',
            category=criminal_procedure
        )
        db.session.add(criminal_procedure_investigation)
        
        # 3-2. 형사소송법 소송 공판
        criminal_procedure_trial = Topic(
            title='형사소송법 소송 공판',
            description='형사소송 절차 등',
            category=criminal_procedure
        )
        db.session.add(criminal_procedure_trial)
        
        # 4. 경찰실무종합 카테고리 추가
        police_practice = Category(
            name='경찰실무종합',
            description='경찰 실무에 관한 종합적인 문제'
        )
        db.session.add(police_practice)
        
        # 4-1. 경찰실무종합 총론
        police_practice_general = Topic(
            title='경찰실무종합 총론',
            description='경찰 실무의 기본 원칙과 이론',
            category=police_practice
        )
        db.session.add(police_practice_general)
        
        # 4-2. 경찰실무종합 각론
        police_practice_special = Topic(
            title='경찰실무종합 각론',
            description='경찰 실무의 세부 영역별 실무',
            category=police_practice
        )
        db.session.add(police_practice_special)
        
        db.session.commit()
        print("카테고리 데이터가 성공적으로 추가되었습니다.")
        
        # 추가된 카테고리 출력
        print("\n추가된 카테고리 목록:\n")
        categories = Category.query.all()
        for category in categories:
            print(f"[{category.name}]")
            print(f"설명: {category.description}")
            topics = Topic.query.filter_by(category_id=category.id).all()
            for topic in topics:
                print(f"  - {topic.title}: {topic.description}")
            print()

if __name__ == '__main__':
    add_categories() 