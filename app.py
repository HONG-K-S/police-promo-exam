# Flask 웹 애플리케이션의 메인 파일입니다.
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import case
import os
import random
from functools import wraps
from datetime import datetime, timedelta
from forms import LoginForm, AdminLoginForm
import io
import csv
from flask_migrate import Migrate
from database import db, init_app
from models import Category, Question, User, AnswerRecord
from urllib.parse import urlparse

# Flask 애플리케이션 생성
app = Flask(__name__)

# 애플리케이션 설정
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-please-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///police_promo.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 데이터베이스 설정과 모델 가져오기
init_app(app)

# Flask-Login 설정
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = '이 페이지에 접근하려면 로그인이 필요합니다.'

# Flask-Migrate 설정
migrate = Migrate(app, db)

# 모델 가져오기 (migrate 설정 후에 가져와야 함)
from models import Category, Question, User, AnswerRecord

# 데이터베이스 테이블 초기화 및 초기 계정 생성
def create_initial_accounts():
    """초기 계정 생성"""
    try:
        # 관리자 계정 생성
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                name='관리자',
                rank='관리자',
                department='시스템관리과',
                email='admin@example.com',
                phone='010-0000-0000',
                is_admin=True
            )
            admin.set_password('admin123!')
            db.session.add(admin)
        
        # 테스트 사용자 계정 생성
        test_user = User.query.filter_by(username='test').first()
        if not test_user:
            test_user = User(
                username='test',
                name='테스트사용자',
                rank='경위',
                department='테스트과',
                email='test@example.com',
                phone='010-1111-1111',
                is_admin=False
            )
            test_user.set_password('test123!')
            db.session.add(test_user)
        
        db.session.commit()
        print("초기 계정이 성공적으로 생성되었습니다.")
    except Exception as e:
        db.session.rollback()
        print(f"초기 계정 생성 중 오류 발생: {str(e)}")

# 애플리케이션 시작 시 초기 계정 생성
with app.app_context():
    db.create_all()
    create_initial_accounts()

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
        
        if cleanup_type == 'old_activities':
            # Delete activities older than 6 months
            six_months_ago = datetime.utcnow() - timedelta(days=180)
            AnswerRecord.query.filter(
                AnswerRecord.user_id == current_user.id,
                AnswerRecord.created_at < six_months_ago
            ).delete()
            message = '6개월 이상 된 학습 기록이 삭제되었습니다.'
            
        elif cleanup_type == 'wrong_answers':
            # Delete all wrong answer records
            AnswerRecord.query.filter_by(
                user_id=current_user.id,
                is_correct=False
            ).delete()
            message = '모든 오답 기록이 삭제되었습니다.'
            
        elif cleanup_type == 'all':
            # Delete all user's answer records
            AnswerRecord.query.filter_by(user_id=current_user.id).delete()
            message = '모든 학습 기록이 삭제되었습니다.'
            
        else:
            flash('잘못된 요청입니다.', 'danger')
            return redirect(url_for('profile'))
            
        db.session.commit()
        flash(message, 'success')
        
    except Exception as e:
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
    """
    관리자용 문제 관리 페이지를 보여주는 함수입니다.
    """
    # 모든 문제 가져오기
    questions = Question.query.all()
    
    # 모든 카테고리 가져오기
    categories = Category.query.all()
    
    return render_template('admin/questions.html',
                         questions=questions,
                         categories=categories)

@app.route('/admin/categories', methods=['GET', 'POST'])
@login_required
def admin_categories():
    """카테고리 관리 페이지"""
    if request.method == 'POST':
        category_id = request.form.get('category_id')
        name = request.form.get('name')
        description = request.form.get('description')
        
        if category_id:  # 수정
            category = Category.query.get_or_404(category_id)
            category.name = name
            category.description = description
        else:  # 추가
            category = Category(name=name, description=description)
            db.session.add(category)
        
        try:
            db.session.commit()
            flash('카테고리가 성공적으로 저장되었습니다.', 'success')
            return redirect(url_for('admin_categories'))
        except Exception as e:
            db.session.rollback()
            flash('카테고리 저장 중 오류가 발생했습니다.', 'error')
            return redirect(url_for('admin_categories'))
    
    # 수정할 카테고리 ID가 있는 경우
    edit_id = request.args.get('edit')
    category = None
    if edit_id:
        category = Category.query.get_or_404(edit_id)
    
    # 카테고리 목록 조회 (문제 수와 정답률 포함)
    categories = db.session.query(
        Category,
        db.func.count(Question.id).label('question_count'),
        db.func.avg(case([(AnswerRecord.is_correct, 1)], else_=0)).label('correct_rate')
    ).outerjoin(Question, Category.id == Question.category_id)\
     .outerjoin(AnswerRecord, Question.id == AnswerRecord.question_id)\
     .group_by(Category.id)\
     .all()
    
    return render_template('admin/categories.html',
                         category=category,
                         categories=categories)

@app.route('/admin/categories/<int:category_id>/delete', methods=['POST'])
@login_required
def delete_category(category_id):
    """카테고리 삭제"""
    category = Category.query.get_or_404(category_id)
    
    try:
        # 카테고리에 속한 모든 문제 삭제
        Question.query.filter_by(category_id=category_id).delete()
        # 카테고리 삭제
        db.session.delete(category)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/questions/add', methods=['GET', 'POST'])
@login_required
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
        return redirect(url_for('admin_questions'))
    
    return render_template('admin/question_form.html',
                         categories=Category.query.all())

@app.route('/admin/questions/<int:question_id>/edit', methods=['GET', 'POST'])
@login_required
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
        return redirect(url_for('admin_questions'))
    
    return render_template('admin/question_form.html',
                         question=question,
                         categories=Category.query.all())

@app.route('/admin/questions/<int:question_id>/delete', methods=['POST'])
@login_required
def admin_delete_question(question_id):
    """문제 삭제"""
    question = Question.query.get_or_404(question_id)
    
    db.session.delete(question)
    db.session.commit()
    
    return jsonify({'success': True})

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
    학습 시작 페이지를 보여주고 학습을 시작하는 함수입니다.
    GET 요청: 학습 시작 페이지 표시
    POST 요청: 선택한 카테고리와 문제 개수에 따라 학습 시작
    """
    # 모든 카테고리 가져오기
    categories = Category.query.all()
    
    if request.method == 'POST':
        # 폼 데이터 가져오기
        category_id = request.form.get('category')
        question_count = int(request.form.get('question_count', 5))
        mode = request.form.get('mode', 'random')
        
        # 선택한 카테고리의 문제 가져오기
        if category_id:
            # 선택한 카테고리의 모든 하위 카테고리 가져오기
            subcategories = Category.query.filter_by(parent_id=category_id).all()
            subcategory_ids = [sub.id for sub in subcategories]
            
            # 문제 쿼리 생성
            query = Question.query.filter(Question.category_id.in_(subcategory_ids))
            
            # 학습 모드에 따라 정렬
            if mode == 'difficult':
                # 사용자의 오답 기록을 기반으로 어려운 문제 우선 정렬
                # (실제 구현에서는 더 복잡한 로직이 필요할 수 있음)
                query = query.order_by(db.func.random())
            else:
                # 무작위 정렬
                query = query.order_by(db.func.random())
            
            # 문제 개수만큼 가져오기
            questions = query.limit(question_count).all()
            
            # 세션에 문제 ID 목록 저장
            session['question_ids'] = [q.id for q in questions]
            session['current_question_index'] = 0
            
            # 첫 번째 문제로 리다이렉트
            if questions:
                return redirect(url_for('study_question', question_id=questions[0].id))
            else:
                flash('선택한 카테고리에 문제가 없습니다.', 'error')
                return redirect(url_for('start_learning'))
        else:
            flash('카테고리를 선택해주세요.', 'error')
            return redirect(url_for('start_learning'))
    
    return render_template('start_learning.html', categories=categories)

@app.route('/study_question/<int:question_id>')
@login_required
def study_question(question_id):
    """
    학습 중인 문제를 보여주는 함수입니다.
    """
    # 세션에서 문제 ID 목록과 현재 문제 인덱스 가져오기
    question_ids = session.get('question_ids', [])
    current_index = session.get('current_question_index', 0)
    
    # 문제 ID 목록이 없거나 현재 문제가 목록에 없으면 학습 시작 페이지로 리다이렉트
    if not question_ids or question_id not in question_ids:
        return redirect(url_for('start_learning'))
    
    # 문제 가져오기
    question = Question.query.get_or_404(question_id)
    category = Category.query.get(question.category_id)
    
    # 현재 문제 인덱스 업데이트
    session['current_question_index'] = current_index
    
    return render_template('study_question.html',
                         question=question,
                         category=category,
                         current_index=current_index,
                         total_questions=len(question_ids))

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
    def is_admin():
        return current_user.is_authenticated and current_user.is_admin
    return dict(is_admin=is_admin)

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

# 프로그램이 직접 실행될 때만 실행되는 부분
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True) 