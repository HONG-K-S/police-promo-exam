# Flask 웹 애플리케이션의 메인 파일입니다.
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os
import random
from functools import wraps
from datetime import datetime, timedelta

# 데이터베이스 설정과 모델 가져오기
from database import db, init_app, init_db
from models import Category, Question, Admin, User, AnswerRecord

# Flask 애플리케이션 생성
app = Flask(__name__)

# 애플리케이션 설정
app.config['SECRET_KEY'] = os.urandom(24)

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
    categories = Category.query.filter_by(parent_id=None).all()
    return render_template('index.html', categories=categories)

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
    data = request.get_json()
    selected_categories = data.get('categories', [])
    num_questions = int(data.get('num_questions', 5))
    
    questions = []
    for category_id in selected_categories:
        category = Category.query.get(category_id)
        if category:
            subcategories = Category.query.filter_by(parent_id=category_id).all()
            for subcategory in subcategories:
                questions.extend(Question.query.filter_by(category_id=subcategory.id).all())
    
    selected_questions = random.sample(questions, min(num_questions, len(questions)))
    return jsonify([{
        'id': q.id,
        'title': q.title,
        'question_type': q.question_type,
        'statements': q.statements,
        'correct_answer': q.correct_answer,
        'explanation': q.explanation
    } for q in selected_questions])

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

@app.route('/get_subcategories/<int:category_id>')
@login_required
def get_subcategories(category_id):
    """
    선택된 카테고리의 하위 카테고리를 가져오는 함수입니다.
    """
    subcategories = Category.query.filter_by(parent_id=category_id).all()
    return jsonify([{
        'id': c.id,
        'name': c.name
    } for c in subcategories])

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

@app.route('/profile')
@login_required
def profile():
    """사용자 프로필 페이지"""
    # 사용자의 학습 통계 계산
    stats = {
        'total_questions': Question.query.count(),
        'correct_rate': 75.5,  # 임시 데이터, 실제로는 사용자의 답안 기록에서 계산
        'study_time': 12,  # 임시 데이터, 실제로는 학습 시간 기록에서 계산
        'category_stats': [
            {'name': '경찰학', 'correct_rate': 80},
            {'name': '형법', 'correct_rate': 70},
            {'name': '형사소송법', 'correct_rate': 75},
            {'name': '기타 법령', 'correct_rate': 85}
        ]
    }
    
    # 최근 학습 활동 (임시 데이터)
    recent_activities = [
        {
            'created_at': datetime.now() - timedelta(days=1),
            'description': '경찰학 문제 10개 풀기 완료',
            'category': Category.query.filter_by(name='경찰학').first()
        },
        {
            'created_at': datetime.now() - timedelta(days=2),
            'description': '형법 문제 5개 풀기 완료',
            'category': Category.query.filter_by(name='형법').first()
        }
    ]
    
    return render_template('user/profile.html',
                         user=current_user,
                         stats=stats,
                         recent_activities=recent_activities)

@app.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """프로필 수정"""
    if request.method == 'POST':
        # 폼 데이터로 사용자 정보 업데이트
        current_user.name = request.form.get('name')
        current_user.rank = request.form.get('rank')
        current_user.department = request.form.get('department')
        current_user.email = request.form.get('email')
        current_user.phone = request.form.get('phone')
        
        db.session.commit()
        
        flash('프로필이 성공적으로 수정되었습니다.', 'success')
        return redirect(url_for('profile'))
    
    return render_template('user/edit_profile.html', user=current_user)

@app.route('/profile/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """비밀번호 변경"""
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not current_user.check_password(current_password):
            flash('현재 비밀번호가 일치하지 않습니다.', 'error')
            return redirect(url_for('change_password'))
        
        if new_password != confirm_password:
            flash('새 비밀번호가 일치하지 않습니다.', 'error')
            return redirect(url_for('change_password'))
        
        current_user.set_password(new_password)
        db.session.commit()
        
        flash('비밀번호가 성공적으로 변경되었습니다.', 'success')
        return redirect(url_for('profile'))
    
    return render_template('user/change_password.html')

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

@app.route('/admin/questions')
@login_required
@admin_required
def admin_manage_questions():
    """문제 관리 페이지"""
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search', '')
    selected_category = request.args.get('category', type=int)
    
    # 문제 쿼리 생성
    query = Question.query
    
    # 검색어가 있는 경우
    if search_query:
        query = query.filter(
            db.or_(
                Question.title.ilike(f'%{search_query}%'),
                Question.explanation.ilike(f'%{search_query}%')
            )
        )
    
    # 카테고리 필터
    if selected_category:
        query = query.filter_by(category_id=selected_category)
    
    # 페이지네이션
    pagination = query.order_by(Question.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False
    )
    
    return render_template('admin/manage_questions.html',
                         questions=pagination.items,
                         pagination=pagination,
                         categories=Category.query.all(),
                         search_query=search_query,
                         selected_category=selected_category)

@app.route('/admin/questions/add', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_add_question():
    """문제 추가"""
    if request.method == 'POST':
        # 폼 데이터 가져오기
        category_id = request.form.get('category_id')
        title = request.form.get('title')
        question_type = request.form.get('question_type')
        statements = request.form.getlist('statements[]')
        correct_answer = int(request.form.get('correct_answer'))
        explanation = request.form.get('explanation')
        
        # 새 문제 생성
        question = Question(
            category_id=category_id,
            title=title,
            question_type=question_type,
            statements=statements,
            correct_answer=correct_answer,
            explanation=explanation
        )
        
        db.session.add(question)
        db.session.commit()
        
        flash('문제가 성공적으로 추가되었습니다.', 'success')
        return redirect(url_for('admin_manage_questions'))
    
    return render_template('admin/question_form.html',
                         categories=Category.query.all())

@app.route('/admin/questions/<int:question_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_edit_question(question_id):
    """문제 수정"""
    question = Question.query.get_or_404(question_id)
    
    if request.method == 'POST':
        # 폼 데이터로 문제 업데이트
        question.category_id = request.form.get('category_id')
        question.title = request.form.get('title')
        question.question_type = request.form.get('question_type')
        question.statements = request.form.getlist('statements[]')
        question.correct_answer = int(request.form.get('correct_answer'))
        question.explanation = request.form.get('explanation')
        
        db.session.commit()
        
        flash('문제가 성공적으로 수정되었습니다.', 'success')
        return redirect(url_for('admin_manage_questions'))
    
    return render_template('admin/question_form.html',
                         question=question,
                         categories=Category.query.all())

@app.route('/admin/questions/<int:question_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_delete_question(question_id):
    """문제 삭제"""
    question = Question.query.get_or_404(question_id)
    
    db.session.delete(question)
    db.session.commit()
    
    return jsonify({'success': True})

def init_db():
    """데이터베이스 초기화 및 기본 데이터 추가"""
    with app.app_context():
        # 데이터베이스 테이블 생성
        db.drop_all()  # 기존 테이블 삭제
        db.create_all()  # 테이블 새로 생성
        
        # 기본 카테고리 추가
        # 경찰학
        police = Category(name='경찰학')
        db.session.add(police)
        db.session.commit()
        
        police_org = Category(name='경찰조직법', parent_id=police.id)
        police_emp = Category(name='경찰공무원법', parent_id=police.id)
        police_tech = Category(name='경찰기술', parent_id=police.id)
        db.session.add_all([police_org, police_emp, police_tech])
        
        # 형법
        criminal = Category(name='형법')
        db.session.add(criminal)
        db.session.commit()
        
        criminal_gen = Category(name='형법총칙', parent_id=criminal.id)
        criminal_sp = Category(name='형법각칙', parent_id=criminal.id)
        db.session.add_all([criminal_gen, criminal_sp])
        
        # 형사소송법
        criminal_proc = Category(name='형사소송법')
        db.session.add(criminal_proc)
        db.session.commit()
        
        investigation = Category(name='수사', parent_id=criminal_proc.id)
        evidence = Category(name='증거', parent_id=criminal_proc.id)
        trial = Category(name='재판', parent_id=criminal_proc.id)
        db.session.add_all([investigation, evidence, trial])
        
        # 기타 법령
        other = Category(name='기타 법령')
        db.session.add(other)
        db.session.commit()
        
        constitution = Category(name='헌법', parent_id=other.id)
        db.session.add(constitution)
        
        db.session.commit()

# 프로그램이 직접 실행될 때만 실행되는 부분
if __name__ == '__main__':
    init_db()  # 데이터베이스 초기화
    app.run(host='0.0.0.0', port=8080, debug=True)  # Replit에서 실행되도록 호스트와 포트 설정 