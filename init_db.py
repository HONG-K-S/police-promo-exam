from app import app, db, User

def init_db():
    with app.app_context():
        # 데이터베이스 테이블 생성
        db.create_all()
        
        # 테스트 사용자가 존재하지 않으면 생성
        if not User.query.filter_by(username='admin').first():
            user = User(username='admin')
            user.set_password('admin123')
            db.session.add(user)
            db.session.commit()
            print('테스트 사용자가 생성되었습니다.')
            print('아이디: admin')
            print('비밀번호: admin123')
        else:
            print('테스트 사용자가 이미 존재합니다.')

if __name__ == '__main__':
    init_db() 