# Replit에서 실행되는 메인 파일입니다.
from app import app, init_db

if __name__ == '__main__':
    init_db()  # 데이터베이스 초기화
    app.run(host='0.0.0.0', port=8080)  # Replit에서 실행하기 위한 설정 