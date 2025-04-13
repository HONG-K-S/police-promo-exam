# Flask 웹 애플리케이션의 메인 파일입니다.
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash  # Flask 웹 프레임워크의 필요한 기능들을 가져옵니다.
import os  # 운영체제 관련 기능을 사용하기 위한 모듈
import random  # 무작위 선택을 위한 파이썬 기본 라이브러리
from functools import wraps  # 데코레이터를 위한 파이썬 기본 라이브러리

# 데이터베이스 설정과 모델 가져오기
from database import db, init_app
from models import Category, Question, Admin

# Flask 애플리케이션 생성
app = Flask(__name__)

# 애플리케이션 설정
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev_key_for_development')  # 세션 암호화를 위한 비밀키

# 데이터베이스 초기화
init_app(app)

# 로그인 필요 데코레이터
def login_required(f):
    """
    로그인이 필요한 페이지에 접근할 때 사용하는 데코레이터입니다.
    로그인하지 않은 사용자는 로그인 페이지로 리다이렉트됩니다.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
@login_required
def home():
    """
    메인 페이지를 보여주는 함수입니다.
    모든 상위 카테고리(경찰실무종합, 형법, 형사소송법)를 가져와서 템플릿에 전달합니다.
    로그인이 필요합니다.
    """
    main_categories = Category.query.filter_by(parent_id=None).all()  # 상위 카테고리만 가져옴
    return render_template('index.html', categories=main_categories)  # HTML 템플릿 렌더링

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    로그인 페이지를 보여주고 로그인 처리를 하는 함수입니다.
    GET 요청: 로그인 페이지 표시
    POST 요청: 로그인 처리
    """
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # 사용자 인증
        admin = Admin.query.filter_by(username=username).first()
        if admin and admin.check_password(password):
            # 로그인 성공
            session['admin_id'] = admin.id
            session['admin_username'] = admin.username
            return redirect(url_for('home'))
        else:
            # 로그인 실패
            return render_template('login.html', error='아이디 또는 비밀번호가 올바르지 않습니다.')
    
    # GET 요청: 로그인 페이지 표시
    return render_template('login.html')

@app.route('/logout')
def logout():
    """
    로그아웃 처리 함수입니다.
    세션에서 관리자 정보를 제거하고 로그인 페이지로 리다이렉트합니다.
    """
    session.pop('admin_id', None)
    session.pop('admin_username', None)
    return redirect(url_for('login'))

@app.route('/get_random_questions', methods=['POST'])
@login_required
def get_random_questions():
    """
    선택된 카테고리에서 무작위로 문제를 가져오는 함수입니다.
    클라이언트로부터 POST 요청을 받아 처리합니다.
    로그인이 필요합니다.
    """
    data = request.get_json()  # 클라이언트로부터 받은 JSON 데이터
    category_ids = data.get('category_ids', [])  # 선택된 카테고리 ID들
    num_questions = data.get('num_questions', 5)  # 요청된 문제 수
    
    # 선택된 카테고리들의 모든 하위 카테고리 ID 가져오기
    all_category_ids = set(category_ids)  # 중복 제거를 위해 set 사용
    for cat_id in category_ids:
        category = Category.query.get(cat_id)
        if category:
            for child in category.children:
                all_category_ids.add(child.id)
    
    # 무작위로 문제 선택
    questions = Question.query.filter(Question.category_id.in_(all_category_ids)).all()
    selected_questions = random.sample(questions, min(num_questions, len(questions)))
    
    # 선택된 문제들을 JSON 형식으로 변환하여 반환
    return jsonify([{
        'id': q.id,
        'question_text': q.question_text,
        'options': [q.option1, q.option2, q.option3, q.option4],
        'correct_answer': q.correct_answer,
        'explanation': q.explanation,
        'category': q.category.name
    } for q in selected_questions])

@app.route('/get_subcategories/<int:category_id>')
@login_required
def get_subcategories(category_id):
    """
    특정 상위 카테고리의 하위 카테고리들을 가져오는 함수입니다.
    로그인이 필요합니다.
    """
    subcategories = Category.query.filter_by(parent_id=category_id).all()
    return jsonify([{
        'id': cat.id,
        'name': cat.name
    } for cat in subcategories])

def init_db():
    """
    데이터베이스를 초기화하고 기본 카테고리 데이터를 추가하는 함수입니다.
    """
    with app.app_context():
        db.create_all()  # 데이터베이스 테이블 생성
        
        # 초기 카테고리 데이터 추가
        if not Category.query.first():  # 카테고리가 하나도 없을 때만 실행
            # 메인 카테고리 추가
            police_practice = Category(name='경찰실무종합')
            criminal_law = Category(name='형법')
            criminal_procedure = Category(name='형사소송법')
            
            db.session.add_all([police_practice, criminal_law, criminal_procedure])
            db.session.commit()
            
            # 예시 하위 카테고리 추가
            subcategories = [
                (police_practice.id, '경찰조직법'),
                (police_practice.id, '경찰공무원법'),
                (criminal_law.id, '총칙'),
                (criminal_law.id, '각칙'),
                (criminal_procedure.id, '총칙'),
                (criminal_procedure.id, '수사'),
                (criminal_procedure.id, '공소')
            ]
            
            for parent_id, name in subcategories:
                subcategory = Category(name=name, parent_id=parent_id)
                db.session.add(subcategory)
            
            db.session.commit()
        
        # 기본 관리자 계정 생성
        if not Admin.query.first():  # 관리자 계정이 하나도 없을 때만 실행
            admin = Admin(username='admin')
            admin.set_password('admin123')  # 기본 비밀번호 설정
            db.session.add(admin)
            db.session.commit()
            print("기본 관리자 계정이 생성되었습니다. 아이디: admin, 비밀번호: admin123")

# 프로그램이 직접 실행될 때만 실행되는 부분
if __name__ == '__main__':
    init_db()  # 데이터베이스 초기화
    app.run(host='0.0.0.0', port=8080, debug=True)  # Replit에서 실행되도록 호스트와 포트 설정 