# Flask 웹 애플리케이션의 메인 파일입니다.
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash, send_file, abort, send_from_directory
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import case, text, func, distinct
from functools import wraps
from datetime import datetime, timedelta
from urllib.parse import urlparse
import os
import random
import io
import csv
import sqlite3
from flask_restful import Resource, Api

from models import (
    db, init_db, create_initial_data,
    User, Category, Topic, Question, Statement,
    AnswerRecord, LearningSession, WrongAnswerNote
)
from forms import LoginForm, AdminLoginForm, UserEditForm

# Flask 애플리케이션 생성
app = Flask(__name__)
api = Api(app)

# 애플리케이션 설정
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-please-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///police_promo.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                             'favicon.ico', mimetype='image/vnd.microsoft.icon')

# 데이터베이스 설정
init_db(app)

# Flask-Login 설정
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = '이 페이지에 접근하려면 로그인이 필요합니다.'

# Flask-Migrate 설정
migrate = Migrate(app, db)

def initialize_category_orders():
    """Initialize order values for all categories."""
    with app.app_context():
        # Get all root categories (parent_id is None)
        root_categories = Category.query.filter_by(parent_id=None).order_by(Category.id).all()
        
        # Set order for root categories
        for i, category in enumerate(root_categories, 1):
            category.order = i
            db.session.add(category)
        
        # Get all subcategories
        subcategories = Category.query.filter(Category.parent_id.isnot(None)).order_by(Category.parent_id, Category.id).all()
        
        # Group subcategories by parent_id
        subcategories_by_parent = {}
        for subcategory in subcategories:
            if subcategory.parent_id not in subcategories_by_parent:
                subcategories_by_parent[subcategory.parent_id] = []
            subcategories_by_parent[subcategory.parent_id].append(subcategory)
        
        # Set order for subcategories within each parent
        for parent_id, subs in subcategories_by_parent.items():
            for i, subcategory in enumerate(subs, 1):
                subcategory.order = i
                db.session.add(subcategory)
        
        db.session.commit()

# 애플리케이션 시작 시 초기 데이터 생성
with app.app_context():
    try:
        create_initial_data()
        initialize_category_orders()
    except Exception as e:
        print(f"Error during initialization: {e}")
        pass

@login_manager.user_loader
def load_user(id):
    """
    Flask-Login에서 사용자 객체를 로드하는 함수입니다.
    """
    return User.query.get(int(id))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember_me', False)
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            if not user.is_active:
                flash('계정이 비활성화되었습니다. 관리자에게 문의하세요.', 'danger')
                return redirect(url_for('login'))
            
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            if not next_page or urlparse(next_page).netloc != '':
                next_page = url_for('home')
            return redirect(next_page)
        else:
            flash('아이디 또는 비밀번호가 올바르지 않습니다.', 'danger')
    
    return render_template('login.html')

def admin_required(f):
    """
    관리자 권한이 필요한 페이지에 대한 데코레이터입니다.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('이 페이지에 접근하려면 관리자 권한이 필요합니다.')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    """
    메인 페이지를 보여주는 함수입니다.
    로그인하지 않은 사용자는 로그인 페이지로 리다이렉트됩니다.
    """
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    return redirect(url_for('login'))

@app.route('/home')
@login_required
def home():
    """
    로그인 후 메인 페이지를 보여주는 함수입니다.
    모든 상위 카테고리를 가져와서 템플릿에 전달합니다.
    로그인이 필요합니다.
    """
    try:
        # 카테고리 정보 가져오기
        categories = Category.query.filter_by(parent_id=None).all()
        
        # 사용자의 학습 통계 계산
        total_questions = AnswerRecord.query.filter_by(user_id=current_user.id).count()
        correct_answers = AnswerRecord.query.filter_by(user_id=current_user.id, is_correct=True).count()
        correct_rate = round((correct_answers / total_questions * 100) if total_questions > 0 else 0, 1)
        
        # 학습 시간 계산 (예: 마지막 7일간의 학습 시간)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        recent_records_count = AnswerRecord.query.filter(
            AnswerRecord.user_id == current_user.id,
            AnswerRecord.created_at >= seven_days_ago
        ).count()
        study_time = f"{recent_records_count * 5}분"  # 문제당 5분으로 가정
        
        # 최근 학습 활동 가져오기
        recent_activities = AnswerRecord.query.filter_by(user_id=current_user.id)\
            .order_by(AnswerRecord.created_at.desc())\
            .limit(5)\
            .all()
        
        # 활동 설명 생성
        activities = []
        for record in recent_activities:
            question = Question.query.get(record.question_id)
            category = Category.query.get(record.category_id)
            if question and category:
                description = f"{category.name} - {question.title}"
                if record.is_correct:
                    description += " (정답)"
                else:
                    description += " (오답)"
                activities.append({
                    'description': description,
                    'timestamp': record.created_at
                })
        
        return render_template('index.html',
                             categories=categories,
                             total_questions=total_questions,
                             correct_rate=correct_rate,
                             study_time=study_time,
                             recent_activities=activities)
    except Exception as e:
        app.logger.error(f"Error in home route: {str(e)}")
        flash('페이지를 로드하는 중 오류가 발생했습니다.', 'error')
        return redirect(url_for('login'))

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

@app.route('/submit_answer/<int:session_id>/<int:question_id>', methods=['POST'])
@login_required
def submit_answer(session_id, question_id):
    session = LearningSession.query.get_or_404(session_id)
    question = Question.query.get_or_404(question_id)
    
    if session.user_id != current_user.id:
        flash('잘못된 접근입니다.', 'error')
        return redirect(url_for('index'))
        
    if session.end_time is not None:
        flash('이미 종료된 세션입니다.', 'error')
        return redirect(url_for('session_results', session_id=session_id))
        
    selected_statement_id = request.form.get('answer')
    if not selected_statement_id:
        flash('답변을 선택해주세요.', 'error')
        return redirect(url_for('learning_session', session_id=session_id))
        
    selected_statement = Statement.query.get_or_404(selected_statement_id)
    correct_statement = Statement.query.filter_by(
        question_id=question_id, 
        is_correct=True
    ).first()
    
    # 답변 기록 저장
    answer_record = AnswerRecord(
        user_id=current_user.id,
        question_id=question_id,
        category_id=question.category_id,
        selected_statement_id=selected_statement_id,
        correct_statement_id=correct_statement.id,
        is_correct=(selected_statement_id == correct_statement.id)
    )
    db.session.add(answer_record)
    
    # 세션의 현재 문제 번호 증가
    session.current_question_number += 1
    
    # 모든 문제를 풀었는지 확인
    if session.current_question_number >= session.total_questions:
        session.end_time = datetime.utcnow()
        db.session.commit()
        return redirect(url_for('session_results', session_id=session_id))
        
    db.session.commit()
    return redirect(url_for('learning_session', session_id=session_id))

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
    total_questions = AnswerRecord.query.filter_by(user_id=current_user.id).count()
    correct_answers = AnswerRecord.query.filter_by(user_id=current_user.id, is_correct=True).count()
    correct_rate = round((correct_answers / total_questions * 100) if total_questions > 0 else 0, 1)
    
    # 학습 시간 계산 (예: 마지막 7일간의 학습 시간)
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    recent_records = AnswerRecord.query.filter(
        AnswerRecord.user_id == current_user.id,
        AnswerRecord.created_at >= seven_days_ago
    ).count()
    study_time = recent_records * 5  # 문제당 5분으로 가정
    
    # 카테고리별 통계 계산
    categories = Category.query.all()
    category_stats = []
    
    for category in categories:
        category_records = AnswerRecord.query.filter_by(
            user_id=current_user.id,
            category_id=category.id
        ).all()
        
        if category_records:
            category_total = len(category_records)
            category_correct = sum(1 for record in category_records if record.is_correct)
            category_rate = round((category_correct / category_total * 100), 1)
            
            category_stats.append({
                'name': category.name,
                'correct_rate': category_rate
            })
    
    stats = {
        'total_questions': total_questions,
        'correct_rate': correct_rate,
        'study_time': study_time,
        'category_stats': category_stats
    }
    
    # 최근 학습 활동 가져오기
    recent_records = AnswerRecord.query.filter_by(user_id=current_user.id)\
        .order_by(AnswerRecord.created_at.desc())\
        .limit(5)\
        .all()
    
    recent_activities = []
    for record in recent_records:
        question = Question.query.get(record.question_id)
        category = Category.query.get(record.category_id)
        
        if question and category:
            description = f"{question.title}"
            if record.is_correct:
                description += " (정답)"
            else:
                description += " (오답)"
                
            recent_activities.append({
                'created_at': record.created_at,
                'description': description,
                'category': category
            })
    
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

@app.route('/profile/cleanup', methods=['POST'])
@login_required
def cleanup_user_data():
    try:
        # Get the cleanup type from the form
        cleanup_type = request.form.get('cleanup_type')
        
        # 백업 데이터베이스 연결
        backup_db = sqlite3.connect('instance/user_data_backup.db')
        backup_cursor = backup_db.cursor()
        
        # 백업 테이블 생성 (없는 경우)
        backup_cursor.execute('''
            CREATE TABLE IF NOT EXISTS answer_records_backup (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                question_id INTEGER,
                category_id INTEGER,
                is_correct BOOLEAN,
                created_at DATETIME,
                backup_date DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        if cleanup_type == 'old_activities':
            # 6개월 이상 된 데이터 백업 후 삭제
            six_months_ago = datetime.utcnow() - timedelta(days=180)
            old_records = AnswerRecord.query.filter(
                AnswerRecord.user_id == current_user.id,
                AnswerRecord.created_at < six_months_ago
            ).all()
            
            # 백업
            for record in old_records:
                backup_cursor.execute('''
                    INSERT INTO answer_records_backup 
                    (id, user_id, question_id, category_id, is_correct, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (record.id, record.user_id, record.question_id, 
                     record.category_id, record.is_correct, record.created_at))
            
            # 삭제
            AnswerRecord.query.filter(
                AnswerRecord.user_id == current_user.id,
                AnswerRecord.created_at < six_months_ago
            ).delete()
            message = '6개월 이상 된 학습 기록이 백업 후 삭제되었습니다.'
            
        elif cleanup_type == 'wrong_answers':
            # 오답 기록 백업 후 삭제
            wrong_records = AnswerRecord.query.filter_by(
                user_id=current_user.id,
                is_correct=False
            ).all()
            
            # 백업
            for record in wrong_records:
                backup_cursor.execute('''
                    INSERT INTO answer_records_backup 
                    (id, user_id, question_id, category_id, is_correct, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (record.id, record.user_id, record.question_id, 
                     record.category_id, record.is_correct, record.created_at))
            
            # 삭제
            AnswerRecord.query.filter_by(
                user_id=current_user.id,
                is_correct=False
            ).delete()
            message = '모든 오답 기록이 백업 후 삭제되었습니다.'
            
        elif cleanup_type == 'all':
            # 전체 기록 백업 후 삭제
            all_records = AnswerRecord.query.filter_by(user_id=current_user.id).all()
            
            # 백업
            for record in all_records:
                backup_cursor.execute('''
                    INSERT INTO answer_records_backup 
                    (id, user_id, question_id, category_id, is_correct, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (record.id, record.user_id, record.question_id, 
                     record.category_id, record.is_correct, record.created_at))
            
            # 삭제
            AnswerRecord.query.filter_by(user_id=current_user.id).delete()
            message = '모든 학습 기록이 백업 후 삭제되었습니다.'
            
        else:
            flash('잘못된 요청입니다.', 'danger')
            return redirect(url_for('profile'))
        
        # 백업 DB 커밋
        backup_db.commit()
        backup_db.close()
            
        # 메인 DB 커밋
        db.session.commit()
        flash(message, 'success')
        
    except Exception as e:
        # 오류 발생 시 롤백
        if 'backup_db' in locals():
            backup_db.rollback()
            backup_db.close()
        db.session.rollback()
        flash('데이터 정리 중 오류가 발생했습니다.', 'danger')
        
    return redirect(url_for('profile'))

@app.route('/admin/users')
@login_required
def admin_users():
    """사용자 관리 페이지"""
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@app.route('/admin/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_edit_user(user_id):
    user = User.query.get_or_404(user_id)
    form = UserEditForm(obj=user)
    
    if form.validate_on_submit():
        user.name = form.name.data
        user.rank = form.rank.data
        user.department = form.department.data
        user.email = form.email.data
        user.phone = form.phone.data
        
        if form.password.data:
            user.set_password(form.password.data)
        
        user.is_admin = form.is_admin.data
        user.is_active = form.is_active.data
        
        try:
            db.session.commit()
            flash('사용자 정보가 성공적으로 수정되었습니다.', 'success')
            return redirect(url_for('admin_users'))
        except Exception as e:
            db.session.rollback()
            flash('사용자 정보 수정 중 오류가 발생했습니다.', 'danger')
    
    return render_template('admin/edit_user.html', form=form, user=user)

@app.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_delete_user(user_id):
    user = User.query.get_or_404(user_id)
    
    # 자신의 계정은 삭제할 수 없음
    if user.id == current_user.id:
        flash('자신의 계정은 삭제할 수 없습니다.', 'danger')
        return redirect(url_for('admin_users'))
    
    try:
        db.session.delete(user)
        db.session.commit()
        flash('사용자가 성공적으로 삭제되었습니다.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('사용자 삭제 중 오류가 발생했습니다.', 'danger')
    
    return redirect(url_for('admin_users'))

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """
    관리자 로그인 페이지를 보여주고 로그인 처리를 하는 함수입니다.
    GET 요청: 관리자 로그인 페이지 표시
    POST 요청: 관리자 로그인 처리
    """
    if current_user.is_authenticated and current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    
    form = AdminLoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data) or not user.is_admin:
            flash('관리자 아이디 또는 비밀번호가 올바르지 않습니다.', 'danger')
            return redirect(url_for('admin_login'))
        
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or not next_page.startswith('/'):
            next_page = url_for('admin_dashboard')
        return redirect(next_page)
    
    return render_template('admin_login.html', title='관리자 로그인', form=form)

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    # 통계 데이터 가져오기
    total_users = User.query.count()
    total_questions = Question.query.count()
    total_categories = Category.query.count()
    
    # 최근 활동 가져오기
    recent_activities = []
    
    # 최근 로그인 기록
    recent_logins = User.query.order_by(User.last_login.desc()).limit(5).all()
    for user in recent_logins:
        if user.last_login:  # None이 아닌 경우만 추가
            recent_activities.append({
                'type': 'login',
                'user': user.username,
                'time': user.last_login
            })
    
    # 최근 학습 기록
    recent_studies = AnswerRecord.query.order_by(AnswerRecord.created_at.desc()).limit(5).all()
    for record in recent_studies:
        user = User.query.get(record.user_id)
        if user:
            recent_activities.append({
                'type': 'study',
                'user': user.username,
                'time': record.created_at
            })
    
    # 시간순으로 정렬
    recent_activities.sort(key=lambda x: x['time'], reverse=True)
    
    return render_template('admin/dashboard.html',
                         total_users=total_users,
                         total_questions=total_questions,
                         total_categories=total_categories,
                         recent_activities=recent_activities)

@app.route('/admin/questions')
@login_required
def admin_questions():
    """문제 관리 페이지"""
    # 필터링 옵션
    selected_category = request.args.get('category', type=int)
    selected_type = request.args.get('question_type')
    search = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)
    
    # 기본 쿼리 설정
    query = Question.query
    
    # 필터 적용
    if selected_category:
        query = query.filter_by(category_id=selected_category)
    if selected_type:
        query = query.filter_by(question_type=selected_type)
    if search:
        query = query.filter(
            db.or_(
                Question.title.ilike(f'%{search}%'),
                Statement.content.ilike(f'%{search}%')
            )
        )
    
    # 페이지네이션 적용
    pagination = query.order_by(Question.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False
    )
    questions = pagination.items
    
    # 모든 카테고리 가져오기 (필터용)
    categories = Category.query.all()
    
    return render_template('admin/questions.html',
                         questions=questions,
                         categories=categories,
                         pagination=pagination,
                         selected_category=selected_category,
                         selected_type=selected_type,
                         search=search)

@app.route('/admin/questions/<int:question_id>/delete', methods=['POST'])
@login_required
def admin_delete_question(question_id):
    """문제 삭제"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': '관리자 권한이 필요합니다.'})
    
    try:
        question = Question.query.get_or_404(question_id)
        
        # 문제의 모든 답안 기록 삭제
        AnswerRecord.query.filter_by(question_id=question_id).delete()
        
        # 문제 삭제
        db.session.delete(question)
        db.session.commit()
        
        return jsonify({'success': True, 'message': '문제가 삭제되었습니다.'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@app.route('/wrong_notes')
@login_required
def wrong_notes():
    """
    오답 노트 페이지를 보여주는 함수입니다.
    사용자가 틀린 문제와 맞은 문제를 확인하고 재학습할 수 있습니다.
    """
    # 필터링 옵션 (기본값: 모든 문제)
    filter_type = request.args.get('filter', 'all')
    
    # 정렬 옵션 (기본값: 최신순)
    sort_by = request.args.get('sort', 'latest')
    
    # 카테고리 필터
    category_id = request.args.get('category', None)
    
    # 기본 쿼리 설정
    query = AnswerRecord.query.filter_by(user_id=current_user.id)
    
    # 필터 적용
    if filter_type == 'correct':
        query = query.filter_by(is_correct=True)
    elif filter_type == 'incorrect':
        query = query.filter_by(is_correct=False)
    
    # 카테고리 필터 적용
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    # 정렬 적용
    if sort_by == 'latest':
        query = query.order_by(AnswerRecord.created_at.desc())
    elif sort_by == 'oldest':
        query = query.order_by(AnswerRecord.created_at.asc())
    elif sort_by == 'category':
        query = query.order_by(AnswerRecord.category_id, AnswerRecord.created_at.desc())
    
    # 결과 가져오기
    records = query.all()
    
    # 문제 정보 가져오기
    questions = []
    for record in records:
        question = Question.query.get(record.question_id)
        category = Category.query.get(record.category_id)
        if question and category:
            questions.append({
                'id': question.id,
                'title': question.title,
                'category_id': category.id,
                'category_name': category.name,
                'is_correct': record.is_correct,
                'timestamp': record.created_at,
                'selected_answer': record.selected_answer,
                'correct_answer': question.correct_answer,
                'explanation': question.explanation
            })
    
    # 모든 카테고리 가져오기 (필터용)
    categories = Category.query.all()
    
    return render_template('wrong_notes.html',
                         questions=questions,
                         categories=categories,
                         filter_type=filter_type,
                         sort_by=sort_by,
                         selected_category=category_id)

@app.route('/start_learning', methods=['GET', 'POST'])
@login_required
def start_learning():
    """
    학습 시작 페이지를 보여주는 함수입니다.
    로그인이 필요합니다.
    """
    if request.method == 'POST':
        # 모든 카테고리 ID와 문제 수를 가져옵니다
        category_counts = {}
        total_questions = 0
        
        # 폼 데이터에서 카테고리별 문제 수를 추출합니다
        for key, value in request.form.items():
            if key.startswith('category_'):
                category_id = int(key.split('_')[1])
                count = int(value)
                if count > 0:
                    category_counts[category_id] = count
                    total_questions += count
        
        # 선택된 카테고리가 없으면 오류 메시지를 표시합니다
        if not category_counts:
            flash('최소 하나 이상의 카테고리를 선택해주세요.', 'error')
            return redirect(url_for('start_learning'))
        
        # 학습 세션 생성
        session = LearningSession(
            user_id=current_user.id,
            total_questions=total_questions,
            correct_answers=0,
            start_time=datetime.utcnow()
        )
        db.session.add(session)
        db.session.commit()
        
        # 세션에 카테고리별 문제 수를 저장합니다
        session.category_counts = category_counts
        
        return redirect(url_for('learning_session', session_id=session.id))
    
    # 2차 카테고리만 가져오기
    categories = Category.query.filter(Category.parent_id.isnot(None)).all()
    
    return render_template('start_learning.html', categories=categories)

@app.route('/learning_session/<int:session_id>')
@login_required
def learning_session(session_id):
    """
    학습 세션 페이지를 보여주는 함수입니다.
    로그인이 필요합니다.
    """
    session = LearningSession.query.get_or_404(session_id)
    
    # 현재 사용자의 세션이 아닌 경우 접근을 거부합니다
    if session.user_id != current_user.id:
        abort(403)
    
    # 이미 완료된 세션인 경우 결과 페이지로 리다이렉트합니다
    if session.end_time is not None:
        return redirect(url_for('learning_result', session_id=session_id))
    
    # 현재 문제 번호를 가져옵니다
    current_question_number = session.correct_answers + session.incorrect_answers + 1
    
    # 현재 문제를 가져옵니다
    question = get_next_question(session)
    
    # 문제가 없는 경우 결과 페이지로 리다이렉트합니다
    if question is None:
        session.end_time = datetime.utcnow()
        db.session.commit()
        return redirect(url_for('learning_result', session_id=session_id))
    
    return render_template('learning_session.html',
                         session=session,
                         question=question,
                         current_question_number=current_question_number)

def get_next_question(session):
    """
    다음 문제를 가져오는 함수입니다.
    """
    # 이미 답변한 문제의 ID 목록을 가져옵니다
    answered_question_ids = db.session.query(AnswerRecord.question_id)\
        .filter(AnswerRecord.session_id == session.id)\
        .all()
    answered_question_ids = [q[0] for q in answered_question_ids]
    
    # 카테고리별 문제 수를 가져옵니다
    category_counts = session.category_counts
    
    # 각 카테고리에서 문제를 가져옵니다
    questions = []
    for category_id, count in category_counts.items():
        # 해당 카테고리에서 아직 답변하지 않은 문제를 가져옵니다
        category_questions = Question.query\
            .filter(Question.category_id == category_id)\
            .filter(~Question.id.in_(answered_question_ids))\
            .order_by(func.random())\
            .limit(count)\
            .all()
        questions.extend(category_questions)
    
    # 문제가 없으면 None을 반환합니다
    if not questions:
        return None
    
    # 랜덤하게 문제를 선택합니다
    return random.choice(questions)

@app.route('/export_wrong_notes')
@login_required
def export_wrong_notes():
    """
    오답 노트를 CSV 파일로 내보내는 함수입니다.
    """
    # 필터링 옵션 (기본값: 모든 문제)
    filter_type = request.args.get('filter', 'all')
    
    # 정렬 옵션 (기본값: 최신순)
    sort_by = request.args.get('sort', 'latest')
    
    # 카테고리 필터
    category_id = request.args.get('category', None)
    
    # 기본 쿼리 설정
    query = AnswerRecord.query.filter_by(user_id=current_user.id)
    
    # 필터 적용
    if filter_type == 'correct':
        query = query.filter_by(is_correct=True)
    elif filter_type == 'incorrect':
        query = query.filter_by(is_correct=False)
    
    # 카테고리 필터 적용
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    # 정렬 적용
    if sort_by == 'latest':
        query = query.order_by(AnswerRecord.created_at.desc())
    elif sort_by == 'oldest':
        query = query.order_by(AnswerRecord.created_at.asc())
    elif sort_by == 'category':
        query = query.order_by(AnswerRecord.category_id, AnswerRecord.created_at.desc())
    
    # 결과 가져오기
    records = query.all()
    
    # CSV 파일 생성
    output = io.StringIO()
    writer = csv.writer(output)
    
    # 헤더 작성
    writer.writerow(['카테고리', '문제 제목', '정답 여부', '선택한 답', '정답', '설명', '학습 시간'])
    
    # 데이터 작성
    for record in records:
        question = Question.query.get(record.question_id)
        category = Category.query.get(record.category_id)
        if question and category:
            writer.writerow([
                category.name,
                question.title,
                '정답' if record.is_correct else '오답',
                record.selected_answer,
                question.correct_answer,
                question.explanation,
                record.created_at.strftime('%Y-%m-%d %H:%M')
            ])
    
    # 파일 포인터를 처음으로 이동
    output.seek(0)
    
    # 현재 시간을 파일명에 포함
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'wrong_notes_{timestamp}.csv'
    
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=filename
    )

@app.context_processor
def utility_processor():
    """
    템플릿에서 사용할 유틸리티 함수들을 등록합니다.
    """
    def is_admin_user():
        return current_user.is_authenticated and current_user.is_admin
    
    def get_category_level(category):
        """카테고리의 레벨을 계산하는 함수 (1차, 2차, 3차 등)"""
        level = 0
        current = category
        
        # 딕셔너리인 경우 (템플릿에서 사용되는 경우)
        if isinstance(current, dict):
            while current.get('parent_id'):
                level += 1
                # 부모 카테고리 찾기
                parent = Category.query.get(current['parent_id'])
                if not parent:
                    break
                current = {
                    'id': parent.id,
                    'parent_id': parent.parent_id
                }
        # Category 객체인 경우
        else:
            while current.parent:
                level += 1
                current = current.parent
            
        return level
    
    def get_category_fullname(category):
        """카테고리의 전체 경로를 반환하는 함수"""
        names = []
        current = category
        
        # 딕셔너리인 경우 (템플릿에서 사용되는 경우)
        if isinstance(current, dict):
            names.append(current['name'])
            while current.get('parent_id'):
                parent = Category.query.get(current['parent_id'])
                if not parent:
                    break
                names.append(parent.name)
                current = {
                    'id': parent.id,
                    'parent_id': parent.parent_id,
                    'name': parent.name
                }
        # Category 객체인 경우
        else:
            while current:
                names.append(current.name)
                current = current.parent
        
        return " > ".join(reversed(names))
    
    return dict(
        is_admin_user=is_admin_user,
        get_category_level=get_category_level,
        get_category_fullname=get_category_fullname
    )

@app.route('/admin/users/add', methods=['GET', 'POST'])
@login_required
def admin_add_user():
    if request.method == 'POST':
        username = request.form.get('username')
        name = request.form.get('name')
        rank = request.form.get('rank')
        department = request.form.get('department')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')
        is_admin = 'is_admin' in request.form
        is_active = 'is_active' in request.form

        # Check if username already exists
        if User.query.filter_by(username=username).first():
            flash('이미 존재하는 아이디입니다.', 'danger')
            return redirect(url_for('admin_add_user'))

        # Create new user
        new_user = User(
            username=username,
            name=name,
            rank=rank,
            department=department,
            email=email,
            phone=phone,
            is_admin=is_admin,
            is_active=is_active
        )
        new_user.set_password(password)

        try:
            db.session.add(new_user)
            db.session.commit()
            flash('사용자가 성공적으로 추가되었습니다.', 'success')
            return redirect(url_for('admin_users'))
        except Exception as e:
            db.session.rollback()
            flash('사용자 추가 중 오류가 발생했습니다.', 'danger')
            return redirect(url_for('admin_add_user'))

    return render_template('admin/add_user.html')

@app.route('/session_results/<int:session_id>')
@login_required
def session_results(session_id):
    session = LearningSession.query.get_or_404(session_id)
    
    if session.user_id != current_user.id:
        flash('잘못된 접근입니다.', 'error')
        return redirect(url_for('index'))
        
    # 세션의 모든 답변 기록 조회
    answer_records = AnswerRecord.query.filter_by(
        user_id=current_user.id,
        learning_session_id=session_id
    ).all()
    
    # 정답률 계산
    total_questions = len(answer_records)
    correct_answers = sum(1 for record in answer_records if record.is_correct)
    accuracy = (correct_answers / total_questions * 100) if total_questions > 0 else 0
    
    return render_template(
        'session_results.html',
        session=session,
        answer_records=answer_records,
        accuracy=accuracy
    )

def get_category_fullname(category):
    """카테고리의 전체 경로를 반환하는 함수"""
    names = []
    while category:
        names.append(category.name)
        category = category.parent
    return " > ".join(reversed(names))

# 템플릿 필터 등록
app.jinja_env.filters['get_category_fullname'] = get_category_fullname

@app.route('/admin/edit_category/<int:category_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_edit_category(category_id):
    category = Category.query.get_or_404(category_id)
    if request.method == 'POST':
        category.name = request.form.get('name')
        category.description = request.form.get('description')
        category.parent_id = request.form.get('parent_id', type=int)
        category.is_leaf = bool(request.form.get('is_leaf'))
        db.session.commit()
        flash('카테고리가 수정되었습니다.', 'success')
        return redirect(url_for('admin_manage_categories'))
    categories = Category.query.filter(Category.id != category_id, Category.is_leaf == False).all()
    category_choices = [(cat.id, get_category_fullname(cat)) for cat in categories]
    return render_template('admin/edit_category.html', category=category, category_choices=category_choices)

@app.route('/admin/categories/<int:category_id>/reorder', methods=['POST'])
@login_required
@admin_required
def reorder_category(category_id):
    try:
        data = request.get_json()
        new_order = data.get('new_order')
        direction = data.get('direction')  # 'up' or 'down'
        
        if not new_order or not direction:
            return jsonify({'success': False, 'message': '필수 파라미터가 누락되었습니다.'}), 400
            
        category = Category.query.get_or_404(category_id)
        parent_id = category.parent_id
        
        # 같은 레벨의 모든 카테고리를 순서대로 가져옴
        siblings = Category.query.filter_by(parent_id=parent_id).order_by(Category.order).all()
        
        if direction == 'up' and new_order > 1:
            # 위로 이동
            prev_category = next((c for c in siblings if c.order == new_order - 1), None)
            if prev_category:
                # 순서 교환
                category.order, prev_category.order = prev_category.order, category.order
                db.session.commit()
                return jsonify({'success': True, 'message': '카테고리 순서가 변경되었습니다.'})
        elif direction == 'down' and new_order < len(siblings):
            # 아래로 이동
            next_category = next((c for c in siblings if c.order == new_order + 1), None)
            if next_category:
                # 순서 교환
                category.order, next_category.order = next_category.order, category.order
                db.session.commit()
                return jsonify({'success': True, 'message': '카테고리 순서가 변경되었습니다.'})
                
        return jsonify({'success': False, 'message': '순서를 변경할 수 없습니다.'}), 400
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/admin/statistics')
@login_required
@admin_required
def admin_statistics():
    """관리자용 사용자 통계 페이지"""
    users = User.query.all()
    user_stats = []
    
    for user in users:
        stats = get_user_statistics(user.id)
        user_stats.append({
            'user': user,
            'stats': stats
        })
    
    return render_template('admin/statistics.html', user_stats=user_stats)

@app.route('/admin/statistics/<int:user_id>')
@login_required
def admin_user_statistics(user_id):
    if not current_user.is_admin:
        flash('관리자만 접근할 수 있습니다.', 'danger')
        return redirect(url_for('index'))
    
    # 특정 사용자의 통계 데이터 조회
    user = User.query.get_or_404(user_id)
    stats = get_user_statistics(user_id)
    return render_template('admin/user_statistics.html', user=user, stats=stats)

@app.route('/wrong_answer_notes', methods=['GET'])
@login_required
def wrong_answer_notes():
    """사용자의 오답 노트 목록을 보여주는 페이지"""
    notes = WrongAnswerNote.query.filter_by(user_id=current_user.id).order_by(WrongAnswerNote.created_at.desc()).all()
    return render_template('wrong_answer_notes.html', notes=notes)

@app.route('/wrong_answer_note/<int:answer_record_id>', methods=['GET', 'POST'])
@login_required
def wrong_answer_note(answer_record_id):
    """오답 노트 작성/수정 페이지"""
    answer_record = AnswerRecord.query.get_or_404(answer_record_id)
    
    # 자신의 답안 기록만 접근 가능
    if answer_record.user_id != current_user.id:
        flash('접근 권한이 없습니다.', 'error')
        return redirect(url_for('wrong_answer_notes'))
    
    note = WrongAnswerNote.query.filter_by(answer_record_id=answer_record_id).first()
    
    if request.method == 'POST':
        content = request.form.get('content', '').strip()
        
        if not content:
            flash('내용을 입력해주세요.', 'error')
            return redirect(url_for('wrong_answer_note', answer_record_id=answer_record_id))
        
        if note:
            note.content = content
            note.updated_at = datetime.utcnow()
        else:
            note = WrongAnswerNote(
                user_id=current_user.id,
                answer_record_id=answer_record_id,
                content=content
            )
            db.session.add(note)
        
        try:
            db.session.commit()
            flash('오답 노트가 저장되었습니다.', 'success')
            return redirect(url_for('wrong_answer_notes'))
        except Exception as e:
            db.session.rollback()
            flash('오답 노트 저장 중 오류가 발생했습니다.', 'error')
            return redirect(url_for('wrong_answer_note', answer_record_id=answer_record_id))
    
    return render_template('wrong_answer_note.html', answer_record=answer_record, note=note)

@app.route('/user/statistics')
@login_required
def user_statistics():
    # 기본 통계 데이터
    stats = {
        'total_questions': AnswerRecord.query.filter_by(user_id=current_user.id).count(),
        'correct_rate': calculate_correct_rate(current_user.id),
        'study_time': calculate_total_study_time(current_user.id),
        'study_days': calculate_study_days(current_user.id),
        'category_stats': get_category_stats(current_user.id)
    }
    
    # 시간대별 학습 패턴
    time_data = get_time_distribution(current_user.id)
    
    # 최근 학습 활동
    recent_activities = get_recent_activities(current_user.id)
    
    return render_template('user/statistics.html', 
                         stats=stats,
                         time_data=time_data,
                         recent_activities=recent_activities)

def calculate_correct_rate(user_id):
    total = AnswerRecord.query.filter_by(user_id=user_id).count()
    if total == 0:
        return 0
    correct = AnswerRecord.query.filter_by(user_id=user_id, is_correct=True).count()
    return (correct / total) * 100

def calculate_total_study_time(user_id):
    records = AnswerRecord.query.filter_by(user_id=user_id).all()
    total_minutes = sum((record.end_time - record.start_time).total_seconds() / 60 for record in records)
    hours = int(total_minutes // 60)
    minutes = int(total_minutes % 60)
    return f"{hours}시간 {minutes}분"

def calculate_study_days(user_id):
    return db.session.query(db.func.count(db.func.distinct(db.func.date(AnswerRecord.start_time)))).filter_by(user_id=user_id).scalar()

def get_category_stats(user_id):
    categories = Category.query.all()
    stats = []
    for category in categories:
        total = AnswerRecord.query.filter_by(user_id=user_id, category_id=category.id).count()
        
        if total == 0:
            correct_rate = 0
            category_avg_time = 0
        else:
            correct = AnswerRecord.query.filter_by(user_id=user_id, category_id=category.id, is_correct=True).count()
            correct_rate = (correct / total) * 100
            
            # 카테고리별 평균 풀이 시간
            category_avg_time_result = db.session.query(db.func.avg(AnswerRecord.time_taken))\
                .filter_by(user_id=user_id, category_id=category.id).scalar()
            category_avg_time = round(category_avg_time_result or 0, 1)
        
        stats.append({
            'name': category.name,
            'total_questions': total,
            'correct_answers': correct if total > 0 else 0,
            'correct_rate': correct_rate,
            'avg_time': category_avg_time
        })
    return stats

def get_time_distribution(user_id):
    records = AnswerRecord.query.filter_by(user_id=user_id).all()
    time_slots = [0] * 4  # 00-06, 06-12, 12-18, 18-24
    
    for record in records:
        hour = record.created_at.hour
        if 0 <= hour < 6:
            time_slots[0] += 1
        elif 6 <= hour < 12:
            time_slots[1] += 1
        elif 12 <= hour < 18:
            time_slots[2] += 1
        else:
            time_slots[3] += 1
            
    return time_slots

def get_recent_activities(user_id, limit=10):
    records = AnswerRecord.query.filter_by(user_id=user_id).order_by(AnswerRecord.created_at.desc()).limit(limit).all()
    activities = []
    
    for record in records:
        question = Question.query.get(record.question_id)
        category = Category.query.get(record.category_id)
        status = "정답" if record.is_correct else "오답"
        
        activities.append({
            'timestamp': record.created_at,
            'category': category.name,
            'question': question.title,
            'is_correct': record.is_correct
        })
    
    return activities

def get_user_statistics(user_id):
    """사용자의 상세 학습 통계를 계산하는 함수"""
    # 총 문제 수 계산
    total_questions = AnswerRecord.query.filter_by(user_id=user_id).count()
    
    # 정답률 계산
    correct_answers = AnswerRecord.query.filter_by(user_id=user_id, is_correct=True).count()
    accuracy = (correct_answers / total_questions * 100) if total_questions > 0 else 0
    
    # 총 세션 수 계산
    total_sessions = db.session.query(db.func.count(db.func.distinct(AnswerRecord.learning_session_id))).filter_by(user_id=user_id).scalar()
    
    # 평균 문제 풀이 시간 계산 (초 단위)
    avg_time_result = db.session.query(db.func.avg(AnswerRecord.time_taken)).filter_by(user_id=user_id).scalar()
    avg_time = round(avg_time_result or 0, 1)  # None인 경우 0으로 처리
    
    # 총 학습 시간 계산 (초 단위)
    total_time = db.session.query(db.func.sum(AnswerRecord.time_taken)).filter_by(user_id=user_id).scalar() or 0
    study_hours = int(total_time / 3600)
    study_minutes = int((total_time % 3600) / 60)
    
    # 학습 일수 계산
    study_days = db.session.query(db.func.count(db.func.distinct(db.func.date(AnswerRecord.created_at)))).filter_by(user_id=user_id).scalar()
    
    # 카테고리별 통계
    category_stats = []
    categories = Category.query.all()
    for category in categories:
        total = AnswerRecord.query.filter_by(user_id=user_id, category_id=category.id).count()
        
        if total == 0:
            correct_rate = 0
            category_avg_time = 0
        else:
            correct = AnswerRecord.query.filter_by(user_id=user_id, category_id=category.id, is_correct=True).count()
            correct_rate = (correct / total) * 100
            
            # 카테고리별 평균 풀이 시간
            category_avg_time_result = db.session.query(db.func.avg(AnswerRecord.time_taken))\
                .filter_by(user_id=user_id, category_id=category.id).scalar()
            category_avg_time = round(category_avg_time_result or 0, 1)
        
        category_stats.append({
            'name': category.name,
            'total_questions': total,
            'correct_answers': correct if total > 0 else 0,
            'correct_rate': correct_rate,
            'avg_time': category_avg_time
        })
    
    # 시간대별 통계
    time_distribution = [0] * 24  # 24시간별 통계
    records = AnswerRecord.query.filter_by(user_id=user_id).all()
    for record in records:
        hour = record.created_at.hour
        time_distribution[hour] += 1
    
    # 최근 활동
    recent_activities = get_recent_activities(user_id)
    
    return {
        'total_questions': total_questions,
        'accuracy': accuracy,
        'total_sessions': total_sessions,
        'avg_time': avg_time,
        'study_time': f"{study_hours}시간 {study_minutes}분",
        'study_days': study_days,
        'category_stats': category_stats,
        'time_distribution': time_distribution,
        'recent_activities': recent_activities
    }

@app.route('/admin/manage_categories')
@login_required
@admin_required
def admin_manage_categories():
    """
    카테고리 관리 페이지를 보여주는 함수입니다.
    """
    # 모든 카테고리 가져오기
    all_categories = Category.query.order_by(Category.order).all()
    
    # 루트 카테고리만 가져오기 (parent_id가 None인 카테고리)
    root_categories = Category.query.filter_by(parent_id=None).order_by(Category.order).all()
    
    # 각 카테고리의 자식 관계 설정
    for category in all_categories:
        if category.parent_id:
            parent = next((cat for cat in all_categories if cat.id == category.parent_id), None)
            if parent:
                if not hasattr(parent, 'children'):
                    parent.children = []
                parent.children.append(category)
    
    return render_template('admin/manage_categories.html',
                         root_categories=root_categories,
                         all_categories=all_categories)

@app.route('/admin/categories/add', methods=['GET', 'POST'])
@login_required
def admin_add_category():
    if not current_user.is_authenticated or not current_user.is_admin:
        flash('관리자만 접근할 수 있습니다.', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        parent_id = request.form.get('parent_id')
        is_leaf = 'is_leaf' in request.form
        
        if not name:
            flash('카테고리 이름은 필수입니다.', 'error')
            return redirect(url_for('admin_add_category'))
        
        # 같은 레벨에서만 중복 체크
        existing_category = Category.query.filter_by(
            parent_id=parent_id if parent_id else None,
            name=name
        ).first()
        
        if existing_category:
            flash('같은 레벨에 동일한 이름의 카테고리가 이미 존재합니다.', 'error')
            return redirect(url_for('admin_add_category'))
        
        try:
            # 상위 카테고리가 없는 경우 최상위 카테고리로 생성
            parent_id = parent_id if parent_id else None
            
            # 같은 레벨의 카테고리 수를 확인하여 order 값 설정
            siblings = Category.query.filter_by(parent_id=parent_id).all()
            order = len(siblings) + 1
            
            category = Category(
                name=name,
                description=description,
                parent_id=parent_id,
                is_leaf=is_leaf,
                order=order
            )
            db.session.add(category)
            db.session.commit()
            flash('카테고리가 추가되었습니다.', 'success')
            return redirect(url_for('admin_manage_categories'))
        except Exception as e:
            db.session.rollback()
            flash(f'카테고리 추가 중 오류가 발생했습니다: {str(e)}', 'error')
            return redirect(url_for('admin_add_category'))
    
    # GET 요청 시 모든 카테고리를 트리 구조로 가져옴
    categories = Category.query.all()
    category_tree = []
    
    def build_category_tree(category, level=0):
        category_dict = {
            'id': category.id,
            'name': category.name,
            'level': level,
            'is_leaf': category.is_leaf,
            'full_path': category.name
        }
        
        if category.parent:
            parent_path = build_category_tree(category.parent, level - 1)
            category_dict['full_path'] = f"{parent_path['full_path']} > {category.name}"
        
        return category_dict
    
    for category in categories:
        if not category.parent_id:  # 최상위 카테고리만 시작점으로
            category_tree.append(build_category_tree(category))
    
    return render_template('admin/add_category.html', categories=category_tree)

@app.route('/admin/delete_category/<int:category_id>', methods=['POST'])
@login_required
@admin_required
def admin_delete_category(category_id):
    """카테고리 삭제"""
    try:
        category = Category.query.get_or_404(category_id)
        
        # 하위 카테고리가 있는지 확인
        subcategories = Category.query.filter_by(parent_id=category_id).all()
        if subcategories and not category.is_leaf:
            return jsonify({
                'success': False,
                'message': '하위 카테고리가 있는 카테고리는 삭제할 수 없습니다. 먼저 하위 카테고리를 삭제하거나 이동해주세요.'
            })
        
        # 삭제할 카테고리의 순서와 부모 ID 저장
        deleted_order = category.order
        parent_id = category.parent_id
        
        # 관련된 문제들도 함께 삭제
        Question.query.filter_by(category_id=category_id).delete()
        db.session.delete(category)
        
        # 같은 레벨의 카테고리들의 순서 재정렬
        categories_to_update = Category.query.filter(
            Category.parent_id == parent_id,
            Category.order > deleted_order
        ).all()
        
        for cat in categories_to_update:
            cat.order -= 1
            db.session.add(cat)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '카테고리가 성공적으로 삭제되었습니다.'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'카테고리 삭제 중 오류가 발생했습니다: {str(e)}'
        })

@app.route('/admin/category/<int:category_id>', methods=['GET'])
@login_required
@admin_required
def get_category(category_id):
    """카테고리 정보를 JSON으로 반환하는 API"""
    category = Category.query.get_or_404(category_id)
    return jsonify({
        'id': category.id,
        'name': category.name,
        'description': category.description,
        'parent_id': category.parent_id,
        'is_leaf': category.is_leaf
    })

@app.route('/admin/category/<int:category_id>', methods=['PUT'])
@login_required
@admin_required
def update_category(category_id):
    """카테고리 정보를 수정하는 API"""
    category = Category.query.get_or_404(category_id)
    data = request.get_json()
    
    try:
        category.name = data.get('name', category.name)
        category.description = data.get('description', category.description)
        category.parent_id = data.get('parent_id', category.parent_id)
        category.is_leaf = data.get('is_leaf', category.is_leaf)
        
        db.session.commit()
        return jsonify({'success': True, 'message': '카테고리가 수정되었습니다.'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

# 프로그램이 직접 실행될 때만 실행되는 부분
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

class CategoryList(Resource):
    def get(self):
        try:
            categories = Category.query.all()
            return [{
                'id': category.id,
                'name': category.name,
                'description': category.description,
                'parent_id': category.parent_id,
                'order': category.order
            } for category in categories]
        except Exception as e:
            return {'message': 'Error fetching categories', 'error': str(e)}, 500

class CategoryDetail(Resource):
    def get(self, id):
        try:
            category = Category.query.get_or_404(id)
            return {
                'id': category.id,
                'name': category.name,
                'description': category.description,
                'parent_id': category.parent_id,
                'order': category.order
            }
        except Exception as e:
            return {'message': 'Error fetching category', 'error': str(e)}, 500

class CategoryQuestions(Resource):
    def get(self, id):
        try:
            category = Category.query.get_or_404(id)
            questions = Question.query.filter_by(category_id=id).all()
            return [{
                'id': question.id,
                'title': question.title,
                'description': question.description,
                'created_at': question.created_at.isoformat()
            } for question in questions]
        except Exception as e:
            return {'message': 'Error fetching questions', 'error': str(e)}, 500

class CategoryStats(Resource):
    def get(self, category_id):
        questions = Question.query.filter_by(category_id=category_id).all()
        total_questions = len(questions)
        completed_questions = AnswerRecord.query.filter(
            AnswerRecord.user_id == current_user.id,
            AnswerRecord.question_id.in_([q.id for q in questions])
        ).count()
        
        # 평균 정답률 계산
        total_accuracy = 0
        answered_count = 0
        for question in questions:
            record = AnswerRecord.query.filter_by(
                question_id=question.id,
                user_id=current_user.id
            ).first()
            if record:
                total_accuracy += record.accuracy
                answered_count += 1
        
        average_accuracy = round(total_accuracy / answered_count, 1) if answered_count > 0 else 0
        
        return {
            'total_questions': total_questions,
            'completed_questions': completed_questions or 0,
            'accuracy': round(average_accuracy, 1)
        }

class StatisticsOverall(Resource):
    def get(self):
        try:
            # 전체 문제 수
            total_questions = Question.query.count()
            
            # 완료한 문제 수
            completed_questions = AnswerRecord.query.filter_by(
                user_id=current_user.id
            ).count()
            
            # 평균 정답률
            records = AnswerRecord.query.filter_by(user_id=current_user.id).all()
            total_accuracy = sum(record.accuracy for record in records)
            average_accuracy = round(total_accuracy / len(records), 1) if records else 0
            
            return {
                'total_questions': total_questions,
                'completed_questions': completed_questions,
                'average_accuracy': average_accuracy
            }
        except Exception as e:
            return {'message': 'Error fetching statistics', 'error': str(e)}, 500

class StatisticsCategories(Resource):
    def get(self):
        try:
            categories = Category.query.all()
            result = []
            
            for category in categories:
                # 카테고리별 문제 수
                questions = Question.query.filter_by(category_id=category.id).all()
                total_questions = len(questions)
                
                # 완료한 문제 수
                completed_questions = AnswerRecord.query.filter(
                    AnswerRecord.question_id.in_([q.id for q in questions]),
                    AnswerRecord.user_id == current_user.id
                ).count()
                
                # 정답률 계산
                records = AnswerRecord.query.filter(
                    AnswerRecord.question_id.in_([q.id for q in questions]),
                    AnswerRecord.user_id == current_user.id
                ).all()
                
                total_accuracy = sum(record.accuracy for record in records)
                accuracy = round(total_accuracy / len(records), 1) if records else 0
                
                # 완료율 계산
                completion_rate = round((completed_questions / total_questions * 100), 1) if total_questions > 0 else 0
                
                # 최근 학습일
                last_record = AnswerRecord.query.filter(
                    AnswerRecord.question_id.in_([q.id for q in questions]),
                    AnswerRecord.user_id == current_user.id
                ).order_by(AnswerRecord.created_at.desc()).first()
                
                last_studied = last_record.created_at.strftime('%Y-%m-%d') if last_record else None
                
                result.append({
                    'id': category.id,
                    'name': category.name,
                    'total_questions': total_questions,
                    'completed_questions': completed_questions,
                    'accuracy': accuracy,
                    'completion_rate': completion_rate,
                    'last_studied': last_studied
                })
            
            return result
        except Exception as e:
            return {'message': 'Error fetching category statistics', 'error': str(e)}, 500

# Register API resources
api.add_resource(CategoryList, '/api/categories')
api.add_resource(CategoryDetail, '/api/categories/<int:id>')
api.add_resource(CategoryQuestions, '/api/categories/<int:id>/questions')
api.add_resource(CategoryStats, '/api/categories/<int:category_id>/stats')
api.add_resource(StatisticsOverall, '/api/statistics/overall')
api.add_resource(StatisticsCategories, '/api/statistics/categories') 