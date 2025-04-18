# Police Promo 개발자 가이드

## 목차
1. [개발 환경 설정](#개발-환경-설정)
2. [프로젝트 구조](#프로젝트-구조)
3. [데이터베이스](#데이터베이스)
4. [API 개발](#api-개발)
5. [테스트](#테스트)
6. [배포](#배포)

## 개발 환경 설정

### 필수 요구사항
- Python 3.8 이상
- PostgreSQL 12 이상
- Node.js 14 이상 (프론트엔드 개발용)

### 설치 방법
1. 저장소 클론
```bash
git clone https://github.com/your-org/police-promo.git
cd police-promo
```

2. 가상환경 생성 및 활성화
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. 의존성 설치
```bash
pip install -r requirements.txt
```

4. 환경 변수 설정
`.env` 파일을 생성하고 다음 내용을 추가:
```
FLASK_APP=app.py
FLASK_ENV=development
DATABASE_URL=postgresql://username:password@localhost:5432/police_promo
SECRET_KEY=your-secret-key
```

## 프로젝트 구조

```
police-promo/
├── app.py                 # 애플리케이션 진입점
├── config.py             # 설정 파일
├── requirements.txt      # Python 의존성
├── models/              # 데이터베이스 모델
│   ├── __init__.py
│   ├── user.py
│   ├── category.py
│   ├── question.py
│   └── answer.py
├── templates/           # HTML 템플릿
│   ├── base.html
│   ├── auth/
│   ├── categories/
│   └── questions/
├── static/             # 정적 파일
│   ├── css/
│   ├── js/
│   └── img/
├── migrations/         # 데이터베이스 마이그레이션
├── tests/             # 테스트 코드
└── docs/              # 문서
```

## 데이터베이스

### 모델 관계
- User -> Category (다대다)
- Category -> Question (일대다)
- Question -> Answer (일대다)
- User -> Answer (일대다)

### 마이그레이션
1. 마이그레이션 생성
```bash
flask db migrate -m "description"
```

2. 마이그레이션 적용
```bash
flask db upgrade
```

3. 마이그레이션 롤백
```bash
flask db downgrade
```

## API 개발

### API 구조
- RESTful API 설계 원칙 준수
- JSON 응답 형식 사용
- 버전 관리: `/api/v1/`

### 인증
- JWT 토큰 기반 인증
- 토큰 만료 시간: 24시간
- Refresh 토큰 지원

### 에러 처리
- HTTP 상태 코드 사용
- 상세한 에러 메시지 제공
- 로깅 시스템 연동

## 테스트

### 테스트 실행
```bash
# 전체 테스트 실행
python -m pytest

# 특정 테스트 실행
python -m pytest tests/test_auth.py

# 커버리지 리포트 생성
python -m pytest --cov=app tests/
```

### 테스트 작성 가이드라인
1. 각 기능별 테스트 파일 생성
2. 테스트 케이스 명확한 설명
3. Fixture 활용
4. Mock 객체 사용

## 배포

### 배포 환경
- Python 3.8
- PostgreSQL 12
- Nginx
- Gunicorn

### 배포 단계
1. 코드 배포
```bash
git pull origin main
```

2. 의존성 설치
```bash
pip install -r requirements.txt
```

3. 데이터베이스 마이그레이션
```bash
flask db upgrade
```

4. 서버 재시작
```bash
sudo systemctl restart police-promo
```

### 모니터링
- Prometheus + Grafana 사용
- 로그 수집: ELK Stack
- 알림: Slack 웹훅

## 기여 가이드라인

### 코드 스타일
- PEP 8 준수
- Black 포맷터 사용
- isort로 import 정렬

### Pull Request 프로세스
1. 이슈 생성
2. 브랜치 생성
3. 코드 작성
4. 테스트 실행
5. PR 생성
6. 코드 리뷰
7. 머지

### 문서화
- 모든 함수에 docstring 작성
- README.md 업데이트
- API 문서 자동 생성 