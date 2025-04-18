from app import app, db
from models.category import Category
from models.topic import Topic
from models.question import Question
from models.statement import Statement

def add_sample_questions():
    with app.app_context():
        # 경찰법규 카테고리와 주제 가져오기
        police_law = Category.query.filter_by(name='경찰법규').first()
        if not police_law:
            print("경찰법규 카테고리를 찾을 수 없습니다.")
            return

        general_principles = Topic.query.filter_by(title='경찰법 총칙', category_id=police_law.id).first()
        if not general_principles:
            print("경찰법 총칙 주제를 찾을 수 없습니다.")
            return

        # 샘플 문제 1: 경찰법의 개념
        question1 = Question(
            title='경찰법의 개념',
            description='경찰법의 개념과 특징에 관한 설명으로 옳은 것은?',
            topic_id=general_principles.id
        )
        db.session.add(question1)

        # 문제 1의 보기들
        statement1_1 = Statement(
            question=question1,
            content='경찰법은 경찰의 조직과 작용에 관한 법규의 총체이다.',
            is_correct=True
        )
        statement1_2 = Statement(
            question=question1,
            content='경찰법은 형법과 형사소송법만을 포함한다.',
            is_correct=False
        )
        statement1_3 = Statement(
            question=question1,
            content='경찰법은 행정법의 특별법이다.',
            is_correct=True
        )
        statement1_4 = Statement(
            question=question1,
            content='경찰법은 경찰의 내부규정만을 포함한다.',
            is_correct=False
        )

        # 샘플 문제 2: 경찰의 의무
        question2 = Question(
            title='경찰의 의무',
            description='경찰공무원의 의무에 관한 설명으로 옳은 것은?',
            topic_id=general_principles.id
        )
        db.session.add(question2)

        # 문제 2의 보기들
        statement2_1 = Statement(
            question=question2,
            content='경찰공무원은 정치적 중립을 지켜야 한다.',
            is_correct=True
        )
        statement2_2 = Statement(
            question=question2,
            content='경찰공무원은 직무상 알게 된 비밀을 누설할 수 있다.',
            is_correct=False
        )
        statement2_3 = Statement(
            question=question2,
            content='경찰공무원은 소속 상관의 명령에 항상 복종해야 한다.',
            is_correct=False
        )
        statement2_4 = Statement(
            question=question2,
            content='경찰공무원은 법령에 따라 성실히 직무를 수행해야 한다.',
            is_correct=True
        )

        # 모든 변경사항 저장
        db.session.commit()
        print("샘플 문제와 보기들이 성공적으로 추가되었습니다.")

if __name__ == '__main__':
    add_sample_questions() 