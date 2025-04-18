# Police Promo API 문서

## 목차
1. [인증](#인증)
2. [카테고리 API](#카테고리-api)
3. [문제 API](#문제-api)
4. [통계 API](#통계-api)
5. [사용자 API](#사용자-api)

## 인증

### 로그인
- **URL**: `/api/auth/login`
- **Method**: `POST`
- **요청 본문**:
```json
{
    "username": "string",
    "password": "string"
}
```
- **응답**:
```json
{
    "access_token": "string",
    "refresh_token": "string",
    "expires_in": 86400
}
```

### 토큰 갱신
- **URL**: `/api/auth/refresh`
- **Method**: `POST`
- **요청 본문**:
```json
{
    "refresh_token": "string"
}
```
- **응답**:
```json
{
    "access_token": "string",
    "expires_in": 86400
}
```

## 카테고리 API

### 카테고리 목록 조회
- **URL**: `/api/categories`
- **Method**: `GET`
- **인증**: 필요
- **응답**:
```json
[
    {
        "id": 1,
        "name": "행정법",
        "description": "행정법 관련 문제",
        "parent_id": null,
        "order": 1,
        "created_at": "2024-03-15T00:00:00Z",
        "updated_at": "2024-03-15T00:00:00Z"
    }
]
```

### 카테고리 상세 조회
- **URL**: `/api/categories/<id>`
- **Method**: `GET`
- **인증**: 필요
- **응답**:
```json
{
    "id": 1,
    "name": "행정법",
    "description": "행정법 관련 문제",
    "parent_id": null,
    "order": 1,
    "created_at": "2024-03-15T00:00:00Z",
    "updated_at": "2024-03-15T00:00:00Z",
    "subcategories": [
        {
            "id": 2,
            "name": "행정절차법",
            "description": "행정절차법 관련 문제",
            "parent_id": 1,
            "order": 1
        }
    ]
}
```

### 카테고리별 문제 목록 조회
- **URL**: `/api/categories/<id>/questions`
- **Method**: `GET`
- **인증**: 필요
- **응답**:
```json
[
    {
        "id": 1,
        "title": "행정처분의 효력",
        "description": "행정처분의 효력에 관한 문제입니다.",
        "difficulty": "보통",
        "category_id": 1,
        "created_at": "2024-03-15T00:00:00Z",
        "updated_at": "2024-03-15T00:00:00Z"
    }
]
```

### 카테고리 통계 조회
- **URL**: `/api/categories/<id>/stats`
- **Method**: `GET`
- **인증**: 필요
- **응답**:
```json
{
    "total_questions": 10,
    "completed_questions": 5,
    "average_accuracy": 80.5,
    "study_time": 3600,
    "last_studied": "2024-03-15T00:00:00Z"
}
```

## 문제 API

### 문제 상세 조회
- **URL**: `/api/questions/<id>`
- **Method**: `GET`
- **인증**: 필요
- **응답**:
```json
{
    "id": 1,
    "title": "행정처분의 효력",
    "description": "행정처분의 효력에 관한 문제입니다.",
    "difficulty": "보통",
    "category_id": 1,
    "category_name": "행정법",
    "statements": [
        {
            "id": 1,
            "content": "행정처분은 상대방에게 통지한 때로부터 효력이 발생한다.",
            "is_correct": true
        }
    ],
    "created_at": "2024-03-15T00:00:00Z",
    "updated_at": "2024-03-15T00:00:00Z"
}
```

### 답안 제출
- **URL**: `/api/questions/<id>/submit`
- **Method**: `POST`
- **인증**: 필요
- **요청 본문**:
```json
{
    "answers": [
        {
            "statement_id": 1,
            "is_correct": true
        }
    ]
}
```
- **응답**:
```json
{
    "accuracy": 80.5,
    "feedback": "잘 작성하셨습니다.",
    "correct_count": 4,
    "total_count": 5,
    "category_id": 1
}
```

## 통계 API

### 전체 통계 조회
- **URL**: `/api/statistics/overall`
- **Method**: `GET`
- **인증**: 필요
- **응답**:
```json
{
    "total_questions": 100,
    "completed_questions": 50,
    "average_accuracy": 75.5,
    "total_study_time": 36000,
    "study_days": 30,
    "last_studied": "2024-03-15T00:00:00Z"
}
```

### 카테고리별 통계 조회
- **URL**: `/api/statistics/categories`
- **Method**: `GET`
- **인증**: 필요
- **응답**:
```json
[
    {
        "id": 1,
        "name": "행정법",
        "total_questions": 10,
        "completed_questions": 5,
        "accuracy": 80.5,
        "study_time": 3600,
        "last_studied": "2024-03-15T00:00:00Z"
    }
]
```

### 시간대별 학습 통계
- **URL**: `/api/statistics/time-distribution`
- **Method**: `GET`
- **인증**: 필요
- **응답**:
```json
{
    "morning": 30,
    "afternoon": 45,
    "evening": 25
}
```

## 사용자 API

### 사용자 정보 조회
- **URL**: `/api/users/me`
- **Method**: `GET`
- **인증**: 필요
- **응답**:
```json
{
    "id": 1,
    "username": "user1",
    "name": "홍길동",
    "email": "user1@example.com",
    "created_at": "2024-03-15T00:00:00Z",
    "updated_at": "2024-03-15T00:00:00Z"
}
```

### 사용자 정보 수정
- **URL**: `/api/users/me`
- **Method**: `PUT`
- **인증**: 필요
- **요청 본문**:
```json
{
    "name": "홍길동",
    "email": "user1@example.com"
}
```
- **응답**:
```json
{
    "id": 1,
    "username": "user1",
    "name": "홍길동",
    "email": "user1@example.com",
    "updated_at": "2024-03-15T00:00:00Z"
}
```

### 비밀번호 변경
- **URL**: `/api/users/me/password`
- **Method**: `PUT`
- **인증**: 필요
- **요청 본문**:
```json
{
    "current_password": "string",
    "new_password": "string"
}
```
- **응답**:
```json
{
    "accuracy": 80.5,
    "feedback": "잘 작성하셨습니다.",
    "category_id": 1
}
``` 