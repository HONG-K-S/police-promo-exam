# 데이터베이스 설정을 관리하는 파일입니다.
from flask_sqlalchemy import SQLAlchemy
import os
from sqlalchemy import text

# SQLAlchemy 객체 생성
db = SQLAlchemy()

def init_app(app):
    """
    Flask 애플리케이션에 데이터베이스를 초기화합니다.
    """
    app.config.setdefault('SQLALCHEMY_DATABASE_URI', 'sqlite:///police_promo.db')
    app.config.setdefault('SQLALCHEMY_TRACK_MODIFICATIONS', False)
    
    db.init_app(app)
    
    with app.app_context():
        try:
            # 데이터베이스 테이블 생성
            db.create_all()
            print("데이터베이스 테이블이 성공적으로 생성되었습니다.")
            
            # 데이터베이스 연결 테스트
            db.session.execute(text('SELECT 1'))
            db.session.commit()
            
        except Exception as e:
            print(f"데이터베이스 초기화 중 오류 발생: {str(e)}")
            db.session.rollback()
            raise

def init_db(app):
    """데이터베이스 초기화 함수"""
    with app.app_context():
        # 테이블 생성
        db.create_all()
        
        # 데이터베이스 연결 테스트
        try:
            db.session.execute(text('SELECT 1'))
            print("데이터베이스 테이블이 성공적으로 생성되었습니다.")
            
            # 카테고리 초기화
            if Topic.query.count() == 0:
                # 최상위 카테고리 생성
                police_practice = Topic(name="경찰실무종합", parent_id=None, level=1)
                criminal_law = Topic(name="형법", parent_id=None, level=1)
                criminal_procedure = Topic(name="형사소송법", parent_id=None, level=1)
                
                db.session.add_all([police_practice, criminal_law, criminal_procedure])
                db.session.commit()
                
                # 경찰실무종합 하위 카테고리
                practice_general = Topic(name="실무총론", parent_id=police_practice.id, level=2)
                practice_specific = Topic(name="실무각론", parent_id=police_practice.id, level=2)
                
                # 형법 하위 카테고리
                criminal_general = Topic(name="형법총론", parent_id=criminal_law.id, level=2)
                criminal_specific = Topic(name="형법각론", parent_id=criminal_law.id, level=2)
                
                # 형사소송법 하위 카테고리
                procedure_investigation = Topic(name="수사", parent_id=criminal_procedure.id, level=2)
                procedure_litigation = Topic(name="소송", parent_id=criminal_procedure.id, level=2)
                
                db.session.add_all([
                    practice_general, practice_specific,
                    criminal_general, criminal_specific,
                    procedure_investigation, procedure_litigation
                ])
                db.session.commit()

                # 실무총론 하위 주제 생성
                # 1. 수사기본
                investigation_basic = Topic(name="수사기본", parent_id=practice_general.id, level=3)
                db.session.add(investigation_basic)
                
                # 수사기본 하위 주제
                investigation_procedure = Topic(name="수사절차", parent_id=investigation_basic.id, level=4, is_final=True)
                investigation_rights = Topic(name="피의자권리", parent_id=investigation_basic.id, level=4, is_final=True)
                investigation_evidence = Topic(name="증거수집", parent_id=investigation_basic.id, level=4, is_final=True)
                
                db.session.add_all([investigation_procedure, investigation_rights, investigation_evidence])
                db.session.commit()

                # 수사절차 설명 지문 생성
                statements = [
                    # 옳은 지문
                    Statement(
                        content="수사기관은 피의자가 자유롭게 진술할 수 있는 환경을 조성해야 한다.",
                        is_correct=True,
                        explanation="피의자의 자유로운 진술은 수사의 공정성과 신뢰성을 위해 필수적입니다.",
                        topic_id=investigation_procedure.id
                    ),
                    Statement(
                        content="피의자는 수사기관의 조사에 대해 변호인의 도움을 받을 권리가 있다.",
                        is_correct=True,
                        explanation="변호인의 조력을 받을 권리는 헌법상 보장된 기본권입니다.",
                        topic_id=investigation_procedure.id
                    ),
                    # 틀린 지문
                    Statement(
                        content="피의자는 수사기관의 조사에 대해 무조건 침묵할 수 있다.",
                        is_correct=False,
                        explanation="피의자는 침묵할 권리가 있지만, 특정한 경우에는 진술의무가 있을 수 있습니다.",
                        topic_id=investigation_procedure.id
                    ),
                    Statement(
                        content="수사기관은 피의자의 동의 없이 야간에 조사를 진행할 수 있다.",
                        is_correct=False,
                        explanation="야간조사는 피의자의 동의가 있어야 하며, 특별한 사유가 없는 한 제한됩니다.",
                        topic_id=investigation_procedure.id
                    )
                ]
                
                db.session.add_all(statements)
                db.session.commit()
                
                print("경찰실무종합 > 실무총론 > 수사기본 카테고리의 샘플 데이터가 생성되었습니다.")
            
            # 피의자권리 설명 지문 생성
            statements = [
                # 옳은 지문
                Statement(
                    content="피의자는 자신에게 유리한 증거를 제출할 권리가 있다.",
                    is_correct=True,
                    explanation="피의자는 자신에게 유리한 증거를 제출할 권리가 있으며, 이는 공정한 재판을 위한 기본권입니다.",
                    topic_id=investigation_rights.id
                ),
                Statement(
                    content="피의자는 수사기관의 조사에 대해 변호인의 도움을 받을 권리가 있다.",
                    is_correct=True,
                    explanation="변호인의 조력을 받을 권리는 헌법상 보장된 기본권입니다.",
                    topic_id=investigation_rights.id
                ),
                # 틀린 지문
                Statement(
                    content="피의자는 수사기관의 조사에 대해 무조건 침묵할 수 있다.",
                    is_correct=False,
                    explanation="피의자는 침묵할 권리가 있지만, 특정한 경우에는 진술의무가 있을 수 있습니다.",
                    topic_id=investigation_rights.id
                ),
                Statement(
                    content="피의자는 수사기관의 조사에 대해 변호인의 동의 없이 진술할 수 없다.",
                    is_correct=False,
                    explanation="피의자는 변호인의 동의 없이도 자유롭게 진술할 수 있습니다.",
                    topic_id=investigation_rights.id
                )
            ]
            
            db.session.add_all(statements)
            db.session.commit()

            # 증거수집 설명 지문 생성
            statements = [
                # 옳은 지문
                Statement(
                    content="수사기관은 법령에 정한 절차와 방법에 따라 증거를 수집해야 한다.",
                    is_correct=True,
                    explanation="증거수집은 법령에 정한 절차와 방법을 준수해야 하며, 이는 증거의 증거능력을 보장하기 위함입니다.",
                    topic_id=investigation_evidence.id
                ),
                Statement(
                    content="수사기관은 증거수집 시 피의자의 인격과 권리를 존중해야 한다.",
                    is_correct=True,
                    explanation="증거수집 시에도 피의자의 인격과 권리를 존중하는 것이 필요합니다.",
                    topic_id=investigation_evidence.id
                ),
                # 틀린 지문
                Statement(
                    content="수사기관은 피의자의 동의 없이 증거를 수집할 수 없다.",
                    is_correct=False,
                    explanation="수사기관은 법령에 정한 절차와 방법에 따라 피의자의 동의 없이도 증거를 수집할 수 있습니다.",
                    topic_id=investigation_evidence.id
                ),
                Statement(
                    content="수사기관은 증거수집 시 피의자의 변호인에게 통지할 필요가 없다.",
                    is_correct=False,
                    explanation="수사기관은 증거수집 시 피의자의 변호인에게 통지할 필요가 있는 경우가 있습니다.",
                    topic_id=investigation_evidence.id
                )
            ]
            
            db.session.add_all(statements)
            db.session.commit()
            
            print("경찰실무종합 > 실무총론 > 수사기본 카테고리의 모든 샘플 데이터가 생성되었습니다.")
            
            # 수사기술 설명 지문 생성
            statements = [
                # 옳은 지문
                Statement(
                    content="수사기관은 과학적 수사방법을 활용하여 증거를 수집할 수 있다.",
                    is_correct=True,
                    explanation="과학적 수사방법은 현대 수사에서 중요한 역할을 하며, 법령에 정한 절차와 방법에 따라 활용할 수 있습니다.",
                    topic_id=investigation_technique.id
                ),
                Statement(
                    content="수사기관은 디지털 증거를 수집할 때 원본성과 무결성을 보존해야 한다.",
                    is_correct=True,
                    explanation="디지털 증거의 증거능력을 보장하기 위해서는 원본성과 무결성의 보존이 필수적입니다.",
                    topic_id=investigation_technique.id
                ),
                # 틀린 지문
                Statement(
                    content="수사기관은 피의자의 동의 없이 과학적 수사방법을 사용할 수 없다.",
                    is_correct=False,
                    explanation="수사기관은 법령에 정한 절차와 방법에 따라 피의자의 동의 없이도 과학적 수사방법을 사용할 수 있습니다.",
                    topic_id=investigation_technique.id
                ),
                Statement(
                    content="수사기관은 디지털 증거를 수집할 때 피의자의 변호인에게 통지할 필요가 없다.",
                    is_correct=False,
                    explanation="수사기관은 디지털 증거를 수집할 때 피의자의 변호인에게 통지할 필요가 있는 경우가 있습니다.",
                    topic_id=investigation_technique.id
                )
            ]
            
            db.session.add_all(statements)
            db.session.commit()

            # 수사관리 설명 지문 생성
            statements = [
                # 옳은 지문
                Statement(
                    content="수사기관은 수사과정을 기록하고 보관해야 한다.",
                    is_correct=True,
                    explanation="수사과정의 기록과 보관은 수사의 투명성과 책임성을 보장하기 위해 필요합니다.",
                    topic_id=investigation_management.id
                ),
                Statement(
                    content="수사기관은 수사결과를 피해자에게 통지해야 한다.",
                    is_correct=True,
                    explanation="피해자에 대한 수사결과 통지는 피해자의 알 권리를 보장하기 위해 필요합니다.",
                    topic_id=investigation_management.id
                ),
                # 틀린 지문
                Statement(
                    content="수사기관은 수사과정을 기록하지 않아도 된다.",
                    is_correct=False,
                    explanation="수사기관은 수사과정을 기록하고 보관해야 하며, 이는 수사의 투명성과 책임성을 보장하기 위함입니다.",
                    topic_id=investigation_management.id
                ),
                Statement(
                    content="수사기관은 수사결과를 피해자에게 통지할 필요가 없다.",
                    is_correct=False,
                    explanation="수사기관은 수사결과를 피해자에게 통지해야 하며, 이는 피해자의 알 권리를 보장하기 위함입니다.",
                    topic_id=investigation_management.id
                )
            ]
            
            db.session.add_all(statements)
            db.session.commit()
            
            print("경찰실무종합 > 실무총론 > 수사기본 카테고리의 모든 샘플 데이터가 생성되었습니다.")
            
            # 실무총론의 다른 하위 카테고리들에 대한 샘플 데이터 추가
            # 수사절차 카테고리
            investigation_procedure = Category(
                name="수사절차",
                description="수사절차에 관한 내용",
                parent_id=investigation_basic.id
            )
            db.session.add(investigation_procedure)
            db.session.commit()

            statements = [
                # 옳은 지문
                Statement(
                    content="수사기관은 피의자 신문 시 변호인의 참여를 보장해야 한다.",
                    is_correct=True,
                    explanation="피의자 신문 시 변호인의 참여는 피의자의 권리를 보장하기 위해 필수적입니다.",
                    topic_id=investigation_procedure.id
                ),
                Statement(
                    content="수사기관은 체포·구속 시 피의자에게 고지해야 할 사항을 고지해야 한다.",
                    is_correct=True,
                    explanation="체포·구속 시 피의자에게 고지해야 할 사항의 고지는 피의자의 권리를 보장하기 위해 필요합니다.",
                    topic_id=investigation_procedure.id
                ),
                # 틀린 지문
                Statement(
                    content="수사기관은 피의자 신문 시 변호인의 참여를 거부할 수 있다.",
                    is_correct=False,
                    explanation="수사기관은 피의자 신문 시 변호인의 참여를 보장해야 하며, 이는 피의자의 권리를 보장하기 위함입니다.",
                    topic_id=investigation_procedure.id
                ),
                Statement(
                    content="수사기관은 체포·구속 시 피의자에게 고지해야 할 사항을 고지하지 않아도 된다.",
                    is_correct=False,
                    explanation="수사기관은 체포·구속 시 피의자에게 고지해야 할 사항을 고지해야 하며, 이는 피의자의 권리를 보장하기 위함입니다.",
                    topic_id=investigation_procedure.id
                )
            ]
            
            db.session.add_all(statements)
            db.session.commit()

            # 수사협력 카테고리
            investigation_cooperation = Category(
                name="수사협력",
                description="수사협력에 관한 내용",
                parent_id=investigation_basic.id
            )
            db.session.add(investigation_cooperation)
            db.session.commit()

            statements = [
                # 옳은 지문
                Statement(
                    content="수사기관은 다른 수사기관과 협력하여 수사를 진행할 수 있다.",
                    is_correct=True,
                    explanation="수사기관 간의 협력은 효율적인 수사를 위해 필요하며, 법령에 정한 절차와 방법에 따라 이루어져야 합니다.",
                    topic_id=investigation_cooperation.id
                ),
                Statement(
                    content="수사기관은 민간전문가의 협력이 필요한 경우 이를 활용할 수 있다.",
                    is_correct=True,
                    explanation="민간전문가의 협력은 전문적인 지식과 기술을 활용하여 수사의 질을 향상시키기 위해 필요합니다.",
                    topic_id=investigation_cooperation.id
                ),
                # 틀린 지문
                Statement(
                    content="수사기관은 다른 수사기관과 협력하여 수사를 진행할 수 없다.",
                    is_correct=False,
                    explanation="수사기관은 다른 수사기관과 협력하여 수사를 진행할 수 있으며, 이는 효율적인 수사를 위해 필요합니다.",
                    topic_id=investigation_cooperation.id
                ),
                Statement(
                    content="수사기관은 민간전문가의 협력이 필요한 경우에도 이를 활용할 수 없다.",
                    is_correct=False,
                    explanation="수사기관은 민간전문가의 협력이 필요한 경우 이를 활용할 수 있으며, 이는 전문적인 지식과 기술을 활용하여 수사의 질을 향상시키기 위함입니다.",
                    topic_id=investigation_cooperation.id
                )
            ]
            
            db.session.add_all(statements)
            db.session.commit()
            
            print("경찰실무종합 > 실무총론의 모든 하위 카테고리에 대한 샘플 데이터가 생성되었습니다.")
        
        except Exception as e:
            db.session.rollback()
            print(f"데이터베이스 초기화 중 오류 발생: {str(e)}")
            raise 