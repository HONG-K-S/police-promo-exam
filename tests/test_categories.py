import unittest
from app import app, db
from models import User, Category, Question, AnswerRecord
from datetime import datetime

class CategoryTests(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app = app.test_client()
        
        with app.app_context():
            db.create_all()
            
            # 테스트 사용자 생성
            user = User(username='testuser', password='testpass')
            db.session.add(user)
            
            # 테스트 카테고리 생성
            category = Category(name='테스트 카테고리', description='테스트용 카테고리입니다.')
            db.session.add(category)
            
            # 테스트 문제 생성
            question = Question(
                title='테스트 문제',
                description='테스트용 문제입니다.',
                category_id=1
            )
            db.session.add(question)
            
            db.session.commit()
            
            # 로그인
            self.app.post('/login', data={
                'username': 'testuser',
                'password': 'testpass'
            }, follow_redirects=True)

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_category_list(self):
        response = self.app.get('/categories')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'테스트 카테고리', response.data)

    def test_category_detail(self):
        response = self.app.get('/category/1')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'테스트 카테고리', response.data)
        self.assertIn(b'테스트용 카테고리입니다', response.data)

    def test_category_api(self):
        # 카테고리 목록 API
        response = self.app.get('/api/categories')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['name'], '테스트 카테고리')

        # 카테고리 상세 API
        response = self.app.get('/api/categories/1')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['name'], '테스트 카테고리')

        # 카테고리 문제 목록 API
        response = self.app.get('/api/categories/1/questions')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['title'], '테스트 문제')

        # 카테고리 통계 API
        response = self.app.get('/api/categories/1/stats')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['total_questions'], 1)
        self.assertEqual(data['completed_questions'], 0)
        self.assertEqual(data['average_accuracy'], 0)

    def test_statistics_api(self):
        # 전체 통계 API
        response = self.app.get('/api/statistics/overall')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['total_questions'], 1)
        self.assertEqual(data['completed_questions'], 0)
        self.assertEqual(data['average_accuracy'], 0)

        # 카테고리별 통계 API
        response = self.app.get('/api/statistics/categories')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['name'], '테스트 카테고리')
        self.assertEqual(data[0]['total_questions'], 1)
        self.assertEqual(data[0]['completed_questions'], 0)
        self.assertEqual(data[0]['accuracy'], 0)
        self.assertEqual(data[0]['completion_rate'], 0)

if __name__ == '__main__':
    unittest.main() 