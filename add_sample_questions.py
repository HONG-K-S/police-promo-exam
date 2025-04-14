from app import app
from models import db
from models.category import Category
from models.question import Question

def add_sample_questions():
    with app.app_context():
        # 카테고리 찾기
        police_category = Category.query.filter_by(name='경찰학').first()
        criminal_law_category = Category.query.filter_by(name='형법').first()
        criminal_procedure_category = Category.query.filter_by(name='형사소송법').first()
        administrative_law_category = Category.query.filter_by(name='행정법').first()
        other_laws_category = Category.query.filter_by(name='기타 법령').first()
        
        # 하위 카테고리 찾기
        org_law_category = Category.query.filter_by(name='경찰조직법', parent_id=police_category.id).first()
        police_official_law_category = Category.query.filter_by(name='경찰공무원법', parent_id=police_category.id).first()
        police_tech_category = Category.query.filter_by(name='경찰기술', parent_id=police_category.id).first()
        general_criminal_law_category = Category.query.filter_by(name='형법총칙', parent_id=criminal_law_category.id).first()
        special_criminal_law_category = Category.query.filter_by(name='형법각칙', parent_id=criminal_law_category.id).first()
        investigation_category = Category.query.filter_by(name='수사', parent_id=criminal_procedure_category.id).first()
        evidence_category = Category.query.filter_by(name='증거', parent_id=criminal_procedure_category.id).first()
        trial_category = Category.query.filter_by(name='재판', parent_id=criminal_procedure_category.id).first()
        constitutional_law_category = Category.query.filter_by(name='헌법', parent_id=other_laws_category.id).first()
        
        # 샘플 문제 추가
        questions = [
            # 경찰학 - 경찰조직법
            Question(
                title="[경찰학][경찰조직법][경찰청조직] 경찰청의 조직에 관한 설명 중 옳은 것을 고르시오.",
                question_type='correct',
                statements={
                    "1": "경찰청은 청장, 차장, 기획조정실장, 운영지원과장으로 구성된다.",
                    "2": "경찰청은 청장, 차장, 기획조정실장, 운영지원과장, 대변인으로 구성된다.",
                    "3": "경찰청은 청장, 차장, 기획조정실장, 운영지원과장, 대변인, 감사관으로 구성된다.",
                    "4": "경찰청은 청장, 차장, 기획조정실장, 운영지원과장, 대변인, 감사관, 수사정보과장으로 구성된다."
                },
                correct_answer=3,
                explanation="경찰청은 청장, 차장, 기획조정실장, 운영지원과장, 대변인, 감사관으로 구성된다.",
                category_id=org_law_category.id
            ),
            
            # 경찰학 - 경찰공무원법
            Question(
                title="[경찰학][경찰공무원법][성실의무] 경찰공무원의 의무에 관한 설명 중 틀린 것을 고르시오.",
                question_type='incorrect',
                statements={
                    "1": "경찰공무원은 정당한 이유 없이 직무를 수행하지 아니할 수 없다.",
                    "2": "경찰공무원은 소속 상관의 명령에 복종하여야 한다.",
                    "3": "경찰공무원은 직무상 알게 된 비밀을 누설할 수 있다.",
                    "4": "경찰공무원은 공무원의 품위를 해치는 행위를 하여서는 아니 된다."
                },
                correct_answer=3,
                explanation="경찰공무원은 직무상 알게 된 비밀을 누설할 수 없다. 이는 경찰공무원법 제 5조(성실의무)에 규정되어 있다.",
                category_id=police_official_law_category.id
            ),
            
            # 경찰학 - 경찰기술
            Question(
                title="[경찰학][경찰기술][수사기술] 지문채취에 관한 설명 중 옳은 것을 고르시오.",
                question_type='correct',
                statements={
                    "1": "지문채취는 반드시 현장에서만 이루어져야 한다.",
                    "2": "지문채취는 증거물에만 적용되며, 현장에는 적용되지 않는다.",
                    "3": "지문채취는 현장과 증거물 모두에 적용되며, 적절한 방법으로 보존해야 한다.",
                    "4": "지문채취는 수사관의 판단에 따라 선택적으로 이루어질 수 있다."
                },
                correct_answer=3,
                explanation="지문채취는 현장과 증거물 모두에 적용되며, 적절한 방법으로 보존해야 한다. 이는 증거의 신뢰성과 증거능력을 확보하기 위해 필수적이다.",
                category_id=police_tech_category.id
            ),
            
            # 형법 - 형법총칙
            Question(
                title="[형법][형법총칙][죄형법정주의] 죄형법정주의에 관한 설명 중 옳은 것을 고르시오.",
                question_type='correct',
                statements={
                    "1": "죄형법정주의는 헌법에만 규정되어 있고 형법에는 규정되어 있지 않다.",
                    "2": "죄형법정주의는 형법 제1조에 규정되어 있으며, 법률에 규정되지 않은 행위는 처벌하지 않는다는 원칙이다.",
                    "3": "죄형법정주의는 형법 제2조에 규정되어 있으며, 법률에 규정되지 않은 행위도 유사한 법률이 있으면 처벌할 수 있다.",
                    "4": "죄형법정주의는 형법 제3조에 규정되어 있으며, 법률에 규정되지 않은 행위는 판례에 따라 처벌할 수 있다."
                },
                correct_answer=2,
                explanation="죄형법정주의는 형법 제1조에 규정되어 있으며, 법률에 규정되지 않은 행위는 처벌하지 않는다는 원칙이다. 이는 헌법 제13조의 죄형법정주의에 근거한다.",
                category_id=general_criminal_law_category.id
            ),
            
            # 형법 - 형법각칙
            Question(
                title="[형법][형법각칙][살인죄] 살인죄에 관한 설명 중 틀린 것을 고르시오.",
                question_type='incorrect',
                statements={
                    "1": "살인죄는 타인의 생명을 해하는 죄이다.",
                    "2": "살인죄는 고의로 타인의 생명을 해하는 죄이다.",
                    "3": "살인죄는 과실로 타인의 생명을 해하는 죄도 포함한다.",
                    "4": "살인죄는 미수범도 처벌한다."
                },
                correct_answer=3,
                explanation="살인죄는 고의로 타인의 생명을 해하는 죄이며, 과실로 타인의 생명을 해하는 것은 과실치사죄에 해당한다.",
                category_id=special_criminal_law_category.id
            ),
            
            # 형사소송법 - 수사
            Question(
                title="[형사소송법][수사][체포] 체포에 관한 설명 중 옳은 것을 고르시오.",
                question_type='correct',
                statements={
                    "1": "체포는 반드시 체포영장이 있어야만 가능하다.",
                    "2": "체포는 체포영장이 없어도 현행범인 경우 가능하다.",
                    "3": "체포는 체포영장이 없어도 피의자가 도주할 우려가 있는 경우 가능하다.",
                    "4": "체포는 체포영장이 없어도 피의자가 증거를 인멸할 우려가 있는 경우 가능하다."
                },
                correct_answer=2,
                explanation="체포는 체포영장이 없어도 현행범인 경우 가능하다. 이는 형사소송법 제212조에 규정되어 있다.",
                category_id=investigation_category.id
            ),
            
            # 형사소송법 - 증거
            Question(
                title="[형사소송법][증거][자백] 자백에 관한 설명 중 틀린 것을 고르시오.",
                question_type='incorrect',
                statements={
                    "1": "자백은 증거로 사용할 수 있다.",
                    "2": "자백은 피고인의 자백만으로는 유죄로 인정할 수 없다.",
                    "3": "자백은 고문, 폭행, 협박, 신체구속의 부당한 장기화 또는 기망 기타의 방법으로 임의로 진술한 것이 아닌 경우에도 증거로 사용할 수 있다.",
                    "4": "자백은 피고인의 자백이 공판정에서 이루어진 경우에도 다른 증거가 있어야 유죄로 인정할 수 있다."
                },
                correct_answer=3,
                explanation="자백은 고문, 폭행, 협박, 신체구속의 부당한 장기화 또는 기망 기타의 방법으로 임의로 진술한 것이 아닌 경우에는 증거로 사용할 수 없다. 이는 형사소송법 제309조에 규정되어 있다.",
                category_id=evidence_category.id
            ),
            
            # 형사소송법 - 재판
            Question(
                title="[형사소송법][재판][공판] 공판에 관한 설명 중 옳은 것을 고르시오.",
                question_type='correct',
                statements={
                    "1": "공판은 반드시 공개하여야 한다.",
                    "2": "공판은 반드시 비공개하여야 한다.",
                    "3": "공판은 원칙적으로 공개하되, 심리가 방해될 우려가 있는 경우에는 법원의 결정로 공개를 제한할 수 있다.",
                    "4": "공판은 원칙적으로 비공개하되, 특별한 사유가 있는 경우에는 법원의 결정으로 공개할 수 있다."
                },
                correct_answer=3,
                explanation="공판은 원칙적으로 공개하되, 심리가 방해될 우려가 있는 경우에는 법원의 결정으로 공개를 제한할 수 있다. 이는 헌법 제109조와 법원조직법 제57조에 규정되어 있다.",
                category_id=trial_category.id
            ),
            
            # 기타 법령 - 헌법
            Question(
                title="[기타 법령][헌법][기본권] 기본권에 관한 설명 중 옳은 것을 고르시오.",
                question_type='correct',
                statements={
                    "1": "모든 국민은 법 앞에 평등하다.",
                    "2": "모든 국민은 법 앞에 평등하지만, 성별, 종교, 사회적 신분에 따라 차별할 수 있다.",
                    "3": "모든 국민은 법 앞에 평등하지만, 정치적 의견에 따라 차별할 수 있다.",
                    "4": "모든 국민은 법 앞에 평등하지만, 경제적 지위에 따라 차별할 수 있다."
                },
                correct_answer=1,
                explanation="모든 국민은 법 앞에 평등하다. 이는 헌법 제11조에 규정되어 있으며, 성별, 종교, 사회적 신분, 정치적 의견, 경제적 지위 등에 따라 차별할 수 없다.",
                category_id=constitutional_law_category.id
            ),
            
            # 경찰학 - 경찰조직법
            Question(
                title="[경찰학][경찰조직법][지방경찰] 지방경찰에 관한 설명 중 틀린 것을 고르시오.",
                question_type='incorrect',
                statements={
                    "1": "지방경찰은 시·도 경찰청과 경찰서로 구성된다.",
                    "2": "지방경찰은 시·도 경찰청장의 지휘·감독을 받는다.",
                    "3": "지방경찰은 시·도지사의 지휘·감독을 받는다.",
                    "4": "지방경찰은 경찰서장의 지휘·감독을 받는다."
                },
                correct_answer=3,
                explanation="지방경찰은 시·도 경찰청장의 지휘·감독을 받으며, 시·도지사의 지휘·감독을 받지 않는다. 이는 경찰법 제12조에 규정되어 있다.",
                category_id=org_law_category.id
            ),
            
            # 경찰학 - 경찰공무원법
            Question(
                title="[경찰학][경찰공무원법][복무] 경찰공무원의 복무에 관한 설명 중 옳은 것을 고르시오.",
                question_type='correct',
                statements={
                    "1": "경찰공무원은 정당한 이유 없이 직무를 수행하지 아니할 수 없다.",
                    "2": "경찰공무원은 정당한 이유가 있으면 직무를 수행하지 아니할 수 있다.",
                    "3": "경찰공무원은 상관의 명령이 부당하다고 판단되면 직무를 수행하지 아니할 수 있다.",
                    "4": "경찰공무원은 직무가 위험하다고 판단되면 직무를 수행하지 아니할 수 있다."
                },
                correct_answer=1,
                explanation="경찰공무원은 정당한 이유 없이 직무를 수행하지 아니할 수 없다. 이는 경찰공무원법 제5조(성실의무)에 규정되어 있다.",
                category_id=police_official_law_category.id
            ),
            
            # 경찰학 - 경찰기술
            Question(
                title="[경찰학][경찰기술][감식] 감식에 관한 설명 중 옳은 것을 고르시오.",
                question_type='correct',
                statements={
                    "1": "감식은 증거물의 과학적 분석을 통해 증거의 신뢰성을 높이는 방법이다.",
                    "2": "감식은 증거물의 외형적 특징만을 관찰하는 방법이다.",
                    "3": "감식은 증거물의 법적 효력을 판단하는 방법이다.",
                    "4": "감식은 증거물의 경제적 가치를 평가하는 방법이다."
                },
                correct_answer=1,
                explanation="감식은 증거물의 과학적 분석을 통해 증거의 신뢰성을 높이는 방법이다. 이는 수사기술의 한 분야로, 증거의 신뢰성과 증거능력을 확보하기 위해 필수적이다.",
                category_id=police_tech_category.id
            ),
            
            # 형법 - 형법총칙
            Question(
                title="[형법][형법총칙][책임능력] 책임능력에 관한 설명 중 틀린 것을 고르시오.",
                question_type='incorrect',
                statements={
                    "1": "심신장애로 인하여 사물을 변별할 능력이 없거나 의사를 결정할 능력이 없는 자의 행위는 벌하지 아니한다.",
                    "2": "심신장애로 인하여 사물을 변별할 능력이 없거나 의사를 결정할 능력이 없는 자의 행위는 형을 감경한다.",
                    "3": "심신장애로 인하여 사물을 변별할 능력이 없거나 의사를 결정할 능력이 없는 자의 행위는 형을 면제한다.",
                    "4": "심신장애로 인하여 사물을 변별할 능력이 없거나 의사를 결정할 능력이 없는 자의 행위는 형을 감경하거나 면제한다."
                },
                correct_answer=2,
                explanation="심신장애로 인하여 사물을 변별할 능력이 없거나 의사를 결정할 능력이 없는 자의 행위는 벌하지 아니한다. 이는 형법 제10조에 규정되어 있다.",
                category_id=general_criminal_law_category.id
            ),
            
            # 형법 - 형법각칙
            Question(
                title="[형법][형법각칙][강간죄] 강간죄에 관한 설명 중 옳은 것을 고르시오.",
                question_type='correct',
                statements={
                    "1": "강간죄는 폭행 또는 협박으로 사람을 강간한 죄이다.",
                    "2": "강간죄는 폭행 또는 협박으로 사람을 강간한 죄이며, 피해자의 동의가 있으면 성립하지 않는다.",
                    "3": "강간죄는 폭행 또는 협박으로 사람을 강간한 죄이며, 피해자의 동의가 있더라도 성립한다.",
                    "4": "강간죄는 폭행 또는 협박으로 사람을 강간한 죄이며, 피해자의 동의가 있으면 형을 감경한다."
                },
                correct_answer=2,
                explanation="강간죄는 폭행 또는 협박으로 사람을 강간한 죄이며, 피해자의 동의가 있으면 성립하지 않는다. 이는 형법 제297조에 규정되어 있다.",
                category_id=special_criminal_law_category.id
            ),
            
            # 형사소송법 - 수사
            Question(
                title="[형사소송법][수사][검찰] 검찰의 수사에 관한 설명 중 틀린 것을 고르시오.",
                question_type='incorrect',
                statements={
                    "1": "검찰은 범죄의 수사와 공소의 제기 및 그 유지를 담당한다.",
                    "2": "검찰은 범죄의 수사와 공소의 제기 및 그 유지를 담당하며, 법령에 특별한 규정이 있는 경우를 제외하고는 경찰관서의 수사를 지휘·감독한다.",
                    "3": "검찰은 범죄의 수사와 공소의 제기 및 그 유지를 담당하며, 경찰관서의 수사를 지휘·감독할 수 없다.",
                    "4": "검찰은 범죄의 수사와 공소의 제기 및 그 유지를 담당하며, 경찰관서의 수사를 지휘·감독할 수 있지만, 경찰관서는 검찰의 지휘·감독을 받지 않아도 된다."
                },
                correct_answer=3,
                explanation="검찰은 범죄의 수사와 공소의 제기 및 그 유지를 담당하며, 법령에 특별한 규정이 있는 경우를 제외하고는 경찰관서의 수사를 지휘·감독한다. 이는 형사소송법 제196조에 규정되어 있다.",
                category_id=investigation_category.id
            ),
            
            # 형사소송법 - 증거
            Question(
                title="[형사소송법][증거][증거능력] 증거능력에 관한 설명 중 옳은 것을 고르시오.",
                question_type='correct',
                statements={
                    "1": "증거능력은 증거가 법원에 제출될 수 있는 자격을 말한다.",
                    "2": "증거능력은 증거가 법원에 제출될 수 있는 자격을 말하며, 모든 증거는 증거능력이 있다.",
                    "3": "증거능력은 증거가 법원에 제출될 수 있는 자격을 말하며, 법령에 특별한 규정이 있는 경우를 제외하고는 모든 증거는 증거능력이 있다.",
                    "4": "증거능력은 증거가 법원에 제출될 수 있는 자격을 말하며, 법령에 특별한 규정이 있는 경우를 제외하고는 모든 증거는 증거능력이 있지만, 증거의 증명력은 법원의 자유심증에 의한다."
                },
                correct_answer=4,
                explanation="증거능력은 증거가 법원에 제출될 수 있는 자격을 말하며, 법령에 특별한 규정이 있는 경우를 제외하고는 모든 증거는 증거능력이 있지만, 증거의 증명력은 법원의 자유심증에 의한다. 이는 형사소송법 제308조에 규정되어 있다.",
                category_id=evidence_category.id
            ),
            
            # 형사소송법 - 재판
            Question(
                title="[형사소송법][재판][판결] 판결에 관한 설명 중 옳은 것을 고르시오.",
                question_type='correct',
                statements={
                    "1": "판결은 법원이 사건에 관하여 내리는 결정이다.",
                    "2": "판결은 법원이 사건에 관하여 내리는 결정이며, 모든 사건에 대해 판결을 내려야 한다.",
                    "3": "판결은 법원이 사건에 관하여 내리는 결정이며, 공소사실이 증명되지 않은 경우에는 무죄의 판결을 선고하여야 한다.",
                    "4": "판결은 법원이 사건에 관하여 내리는 결정이며, 공소사실이 증명되지 않은 경우에는 무죄의 판결을 선고하여야 하고, 공소사실이 증명된 경우에는 유죄의 판결을 선고하여야 한다."
                },
                correct_answer=4,
                explanation="판결은 법원이 사건에 관하여 내리는 결정이며, 공소사실이 증명되지 않은 경우에는 무죄의 판결을 선고하여야 하고, 공소사실이 증명된 경우에는 유죄의 판결을 선고하여야 한다. 이는 형사소송법 제323조에 규정되어 있다.",
                category_id=trial_category.id
            ),
            
            # 기타 법령 - 헌법
            Question(
                title="[기타 법령][헌법][국회] 국회에 관한 설명 중 틀린 것을 고르시오.",
                question_type='incorrect',
                statements={
                    "1": "국회는 국민의 보통·평등·직접·비밀선거에 의하여 선출된 국회의원으로 구성한다.",
                    "2": "국회의원의 수는 법률로 정하되, 200인 이상으로 한다.",
                    "3": "국회의원의 선거구와 비례대표제 기타 선거에 관한 사항은 법률로 정한다.",
                    "4": "국회의원은 법률에 의하지 아니하고는 체포·구금되지 아니한다."
                },
                correct_answer=2,
                explanation="국회의원의 수는 법률로 정하되, 200인 이상으로 한다. 이는 헌법 제21조에 규정되어 있다.",
                category_id=constitutional_law_category.id
            ),
            
            # 경찰학 - 경찰조직법
            Question(
                title="[경찰학][경찰조직법][경찰권] 경찰권에 관한 설명 중 옳은 것을 고르시오.",
                question_type='correct',
                statements={
                    "1": "경찰권은 경찰공무원만이 행사할 수 있다.",
                    "2": "경찰권은 경찰공무원과 군인만이 행사할 수 있다.",
                    "3": "경찰권은 경찰공무원과 군인, 그리고 민간인도 행사할 수 있다.",
                    "4": "경찰권은 경찰공무원과 군인, 그리고 민간인도 행사할 수 있지만, 민간인은 제한적으로 행사할 수 있다."
                },
                correct_answer=1,
                explanation="경찰권은 경찰공무원만이 행사할 수 있다. 이는 경찰법 제3조에 규정되어 있다.",
                category_id=org_law_category.id
            ),
            
            # 경찰학 - 경찰공무원법
            Question(
                title="[경찰학][경찰공무원법][징계] 경찰공무원의 징계에 관한 설명 중 틀린 것을 고르시오.",
                question_type='incorrect',
                statements={
                    "1": "경찰공무원의 징계는 경찰공무원법에 따라 행해진다.",
                    "2": "경찰공무원의 징계는 국가공무원법에 따라 행해진다.",
                    "3": "경찰공무원의 징계는 경찰공무원법과 국가공무원법에 따라 행해진다.",
                    "4": "경찰공무원의 징계는 경찰공무원법과 국가공무원법에 따라 행해지며, 경찰공무원법에 특별한 규정이 있는 경우에는 그 규정에 따른다."
                },
                correct_answer=2,
                explanation="경찰공무원의 징계는 경찰공무원법과 국가공무원법에 따라 행해지며, 경찰공무원법에 특별한 규정이 있는 경우에는 그 규정에 따른다. 이는 경찰공무원법 제1조에 규정되어 있다.",
                category_id=police_official_law_category.id
            )
        ]
        
        # 데이터베이스에 저장
        for question in questions:
            db.session.add(question)
        db.session.commit()
        
        print('샘플 문제가 추가되었습니다.')

if __name__ == '__main__':
    add_sample_questions() 