# Flask 웹 애플리케이션의 메인 파일입니다.
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash, current_user  # Flask 웹 프레임워크의 필요한 기능들을 가져옵니다.
import os  # 운영체제 관련 기능을 사용하기 위한 모듈
import random  # 무작위 선택을 위한 파이썬 기본 라이브러리
from functools import wraps  # 데코레이터를 위한 파이썬 기본 라이브러리
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# 데이터베이스 설정과 모델 가져오기
from database import db, init_app
from models import Category, Question, Admin, User, AnswerRecord

# Flask 애플리케이션 생성
app = Flask(__name__)

# 애플리케이션 설정
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev_key_for_development')  # 세션 암호화를 위한 비밀키
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///questions.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 데이터베이스 초기화
init_app(app)

# Flask-Login 설정
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = '이 페이지에 접근하려면 로그인이 필요합니다.'

@login_manager.user_loader
def load_user(user_id):
    """
    Flask-Login에서 사용자 객체를 로드하는 함수입니다.
    """
    return User.query.get(int(user_id))

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
    if current_user.is_authenticated:
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # 사용자 인증
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            # 로그인 성공
            login_user(user)
            flash('로그인 성공!', 'success')
            return redirect(url_for('home'))
        else:
            # 로그인 실패
            flash('아이디 또는 비밀번호가 올바르지 않습니다.', 'error')
    
    # GET 요청: 로그인 페이지 표시
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """
    로그아웃 처리 함수입니다.
    세션에서 사용자 정보를 제거하고 로그인 페이지로 리다이렉트합니다.
    """
    logout_user()
    flash('로그아웃되었습니다.', 'info')
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
    
    if not questions:
        return jsonify({'error': '선택된 카테고리에 문제가 없습니다.'}), 404
    
    # 요청된 수만큼 무작위로 문제 선택
    selected_questions = random.sample(questions, min(num_questions, len(questions)))
    
    # 각 문제에 대해 무작위로 하위 카테고리 선택
    for question in selected_questions:
        category = Category.query.get(question.category_id)
        if category and category.parent:
            # 1차 하위 카테고리 선택
            first_level_subcategories = [c for c in category.parent.children if c.id != category.id]
            if first_level_subcategories:
                first_level = random.choice(first_level_subcategories)
                
                # 최종 하위 카테고리 찾기 (더 이상 하위 카테고리가 없는 카테고리)
                final_category = first_level
                category_path = [first_level.name]  # 카테고리 경로 저장
                while final_category.children:
                    final_category = random.choice(final_category.children)
                    category_path.append(final_category.name)
                
                # 상위 카테고리 이름 가져오기
                main_category = category.parent.name
                
                # 카테고리 경로를 대괄호로 구분하여 문자열 생성
                category_path_str = ''.join(f'[{cat}]' for cat in [main_category] + category_path)
                
                # 문제 텍스트 생성
                question.question_text = f"{category_path_str}에 대한 설명 중 옳은 것은?"
                
                # 무작위로 4개의 옵션 선택
                all_options = [c.name for c in final_category.children]
                if len(all_options) >= 4:
                    selected_options = random.sample(all_options, 4)
                    
                    # 정답과 오답 구분
                    correct_options = [opt for opt in selected_options if opt in [c.name for c in final_category.children if c.is_correct]]
                    wrong_options = [opt for opt in selected_options if opt not in correct_options]
                    
                    if correct_options and wrong_options:
                        # 정답과 오답을 무작위로 섞어서 옵션으로 설정
                        question.option1 = selected_options[0]
                        question.option2 = selected_options[1]
                        question.option3 = selected_options[2]
                        question.option4 = selected_options[3]
                        
                        # 정답 설정
                        question.correct_answer = selected_options.index(correct_options[0]) + 1
                        
                        # 해설 설정
                        question.explanation = f"{category_path_str}에 대한 설명 중 '{correct_options[0]}'이(가) 옳은 설명입니다."
    
    # 문제 데이터를 JSON 형식으로 변환
    questions_data = [{
        'id': q.id,
        'question_text': q.question_text,
        'option1': q.option1,
        'option2': q.option2,
        'option3': q.option3,
        'option4': q.option4,
        'correct_answer': q.correct_answer,
        'explanation': q.explanation,
        'category_id': q.category_id
    } for q in selected_questions]
    
    return jsonify({'questions': questions_data})

@app.route('/submit_answer', methods=['POST'])
@login_required
def submit_answer():
    """
    사용자의 답안을 저장하는 함수입니다.
    """
    data = request.get_json()
    question_id = data.get('question_id')
    selected_answer = data.get('selected_answer')
    
    question = Question.query.get(question_id)
    if not question:
        return jsonify({'error': '문제를 찾을 수 없습니다.'}), 404
    
    is_correct = selected_answer == question.correct_answer
    
    # 답안 기록 저장
    answer_record = AnswerRecord(
        user_id=current_user.id,
        question_id=question_id,
        category_id=question.category_id,
        selected_answer=selected_answer,
        is_correct=is_correct
    )
    
    db.session.add(answer_record)
    db.session.commit()
    
    return jsonify({
        'is_correct': is_correct,
        'correct_answer': question.correct_answer,
        'explanation': question.explanation
    })

@app.route('/get_user_stats', methods=['GET'])
@login_required
def get_user_stats():
    """
    사용자의 카테고리별 정답률을 조회하는 함수입니다.
    """
    # 사용자의 모든 답안 기록 가져오기
    answer_records = AnswerRecord.query.filter_by(user_id=current_user.id).all()
    
    # 카테고리별 통계 계산
    stats = {}
    for record in answer_records:
        category_id = record.category_id
        if category_id not in stats:
            stats[category_id] = {'total': 0, 'correct': 0}
        
        stats[category_id]['total'] += 1
        if record.is_correct:
            stats[category_id]['correct'] += 1
    
    # 카테고리 이름과 함께 정답률 계산
    result = []
    for category_id, data in stats.items():
        category = Category.query.get(category_id)
        if category:
            accuracy = (data['correct'] / data['total']) * 100 if data['total'] > 0 else 0
            result.append({
                'category_id': category_id,
                'category_name': category.name,
                'total_questions': data['total'],
                'correct_answers': data['correct'],
                'accuracy': round(accuracy, 2)
            })
    
    return jsonify({'stats': result})

@app.route('/get_subcategories', methods=['GET'])
@login_required
def get_subcategories():
    """
    선택된 카테고리의 하위 카테고리를 가져오는 함수입니다.
    """
    category_id = request.args.get('category_id')
    if not category_id:
        return jsonify({'error': '카테고리 ID가 필요합니다.'}), 400
    
    category = Category.query.get(category_id)
    if not category:
        return jsonify({'error': '카테고리를 찾을 수 없습니다.'}), 404
    
    subcategories = [{'id': c.id, 'name': c.name} for c in category.children]
    return jsonify({'subcategories': subcategories})

@app.route('/register', methods=['GET', 'POST'])
def register():
    """사용자 등록 페이지"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        name = request.form.get('name')
        rank = request.form.get('rank')
        department = request.form.get('department')
        email = request.form.get('email')
        phone = request.form.get('phone')

        # 사용자 이름 중복 확인
        if User.query.filter_by(username=username).first():
            flash('이미 존재하는 사용자 이름입니다.')
            return redirect(url_for('register'))

        # 새 사용자 생성
        user = User(
            username=username,
            name=name,
            rank=rank,
            department=department,
            email=email,
            phone=phone
        )
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        flash('회원가입이 완료되었습니다. 로그인해주세요.')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """
    사용자 프로필 정보를 보여주고 수정하는 페이지입니다.
    """
    if request.method == 'POST':
        user = User.query.get(current_user.id)
        if user:
            user.name = request.form.get('name')
            user.rank = request.form.get('rank')
            user.department = request.form.get('department')
            
            # 비밀번호 변경이 요청된 경우
            new_password = request.form.get('new_password')
            if new_password:
                user.set_password(new_password)
            
            db.session.commit()
            flash('프로필이 성공적으로 업데이트되었습니다.', 'success')
            return redirect(url_for('profile'))
    
    return render_template('profile.html')

@app.route('/admin/users')
def admin_users():
    """관리자용 사용자 목록 페이지"""
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))

    users = User.query.all()
    return render_template('admin_users.html', users=users)

@app.route('/admin/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    # 관리자 권한 확인
    if not current_user.is_admin:
        flash('관리자 권한이 필요합니다.', 'error')
        return redirect(url_for('home'))
    
    # 사용자 정보 가져오기
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        # 폼 데이터 가져오기
        username = request.form.get('username')
        name = request.form.get('name')
        rank = request.form.get('rank')
        department = request.form.get('department')
        email = request.form.get('email')
        phone = request.form.get('phone')
        new_password = request.form.get('new_password')
        is_active = request.form.get('is_active') == 'on'
        
        # 사용자 정보 업데이트
        user.username = username
        user.name = name
        user.rank = rank
        user.department = department
        user.email = email
        user.phone = phone
        user.is_active = is_active
        
        # 새 비밀번호가 입력된 경우에만 업데이트
        if new_password:
            user.set_password(new_password)
        
        try:
            db.session.commit()
            flash('사용자 정보가 성공적으로 업데이트되었습니다.', 'success')
            return redirect(url_for('admin_users'))
        except Exception as e:
            db.session.rollback()
            flash('사용자 정보 업데이트 중 오류가 발생했습니다.', 'error')
            return redirect(url_for('edit_user', user_id=user_id))
    
    return render_template('admin/edit_user.html', user=user)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """
    관리자 로그인 페이지를 표시하고 로그인 처리를 하는 함수입니다.
    """
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        admin = Admin.query.filter_by(username=username).first()
        if admin and admin.check_password(password):
            session['admin_id'] = admin.id
            return redirect(url_for('admin_dashboard'))
        
        flash('잘못된 관리자 이름 또는 비밀번호입니다.')
    
    return render_template('admin/login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    """
    관리자 대시보드를 표시하는 함수입니다.
    """
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    
    return render_template('admin/dashboard.html')

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
            
        # 사용자 계정 생성
        if not User.query.filter_by(username='홍기석').first():
            user1 = User(
                username='홍기석',
                name='홍기석',
                rank='경사',
                department='광주북부경찰서 용봉지구대'
            )
            user1.set_password('1234')
            db.session.add(user1)
            print("사용자 계정이 생성되었습니다. 아이디: 홍기석, 비밀번호: 1234")
            
        if not User.query.filter_by(username='이산하').first():
            user2 = User(
                username='이산하',
                name='이산하',
                rank='경위',
                department='광주북부경찰서 용봉지구대'
            )
            user2.set_password('1234')
            db.session.add(user2)
            print("사용자 계정이 생성되었습니다. 아이디: 이산하, 비밀번호: 1234")
            
        db.session.commit()

# 프로그램이 직접 실행될 때만 실행되는 부분
if __name__ == '__main__':
    init_db()  # 데이터베이스 초기화
    app.run(host='0.0.0.0', port=8080, debug=True)  # Replit에서 실행되도록 호스트와 포트 설정 