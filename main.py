# Replit과 로컬 환경에서 실행되는 메인 파일입니다.
from app import app
from models import init_db
import os

if __name__ == '__main__':
    with app.app_context():
        init_db(app)  # 데이터베이스 초기화
    
    # 환경 변수에 따라 실행 환경 구분
    is_replit = os.environ.get('REPL_ID') is not None
    
    if is_replit:
        # Replit 환경
        app.run(host='0.0.0.0', port=8080)
    else:
        # 로컬 환경
        app.run(host='127.0.0.1', port=5000, debug=True) 