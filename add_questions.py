from app import app, db
from models import Category, Question

def add_sample_questions():
    with app.app_context():
        # 경찰학 카테고리 찾기
        police_category = Category.query.filter_by(name='경찰학').first()
        
        # 경찰조직법 하위 카테고리 찾기
        org_law_category = Category.query.filter_by(
            name='경찰조직법',
            parent_id=police_category.id
        ).first()
        
        # 샘플 문제 추가 (옳은 것 고르기)
        question1 = Question(
            title="[경찰학][경찰조직법][경찰청조직] 경찰청의 조직에 관한 설명 중 옳은 것을 고르시오.",
            question_type='correct',  # 옳은 것 고르기
            statements={
                "1": "경찰청은 청장, 차장, 기획조정실장, 운영지원과장으로 구성된다.",
                "2": "경찰청은 청장, 차장, 기획조정실장, 운영지원과장, 대변인으로 구성된다.",
                "3": "경찰청은 청장, 차장, 기획조정실장, 운영지원과장, 대변인, 감사관으로 구성된다.",
                "4": "경찰청은 청장, 차장, 기획조정실장, 운영지원과장, 대변인, 감사관, 수사정보과장으로 구성된다."
            },
            correct_answer=3,  # 3번이 정답
            explanation="경찰청은 청장, 차장, 기획조정실장, 운영지원과장, 대변인, 감사관으로 구성된다.",
            category_id=org_law_category.id
        )

        # 샘플 문제 추가 (틀린 것 고르기)
        question2 = Question(
            title="[경찰학][경찰공무원법][성실의무] 경찰공무원의 의무에 관한 설명 중 틀린 것을 고르시오.",
            question_type='incorrect',  # 틀린 것 고르기
            statements={
                "1": "경찰공무원은 정당한 이유 없이 직무를 수행하지 아니할 수 없다.",
                "2": "경찰공무원은 소속 상관의 명령에 복종하여야 한다.",
                "3": "경찰공무원은 직무상 알게 된 비밀을 누설할 수 있다.",
                "4": "경찰공무원은 공무원의 품위를 해치는 행위를 하여서는 아니 된다."
            },
            correct_answer=3,  # 3번이 틀린 지문
            explanation="경찰공무원은 직무상 알게 된 비밀을 누설할 수 없다. 이는 경찰공무원법 제 5조(성실의무)에 규정되어 있다.",
            category_id=org_law_category.id
        )
        
        # 데이터베이스에 저장
        db.session.add(question1)
        db.session.add(question2)
        db.session.commit()

if __name__ == '__main__':
    add_sample_questions() 