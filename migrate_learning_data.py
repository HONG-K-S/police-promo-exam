import sqlite3
import os
from datetime import datetime

def migrate_learning_data():
    # 백업 DB와 새 DB 연결
    backup_conn = sqlite3.connect('instance/police_promo_backup.db')
    new_conn = sqlite3.connect('instance/police_promo.db')
    
    backup_cursor = backup_conn.cursor()
    new_cursor = new_conn.cursor()
    
    try:
        # 기존 학습 세션 데이터 삭제
        new_cursor.execute("DELETE FROM learning_session")
        new_cursor.execute("DELETE FROM answer_record")
        print("기존 학습 기록 데이터 삭제 완료")
        
        # 학습 세션 마이그레이션
        backup_cursor.execute("""
            SELECT id, user_id, start_topic_id, total_questions, correct_count, 
                   wrong_count, is_completed, created_at, completed_at 
            FROM learning_session
        """)
        sessions = backup_cursor.fetchall()
        
        for session in sessions:
            new_cursor.execute("""
                INSERT INTO learning_session (
                    id, user_id, topic_id, total_questions, correct_answers,
                    start_time, end_time
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                session[0], session[1], session[2], session[3], session[4],
                session[7], session[8] if session[6] else None
            ))
        
        print(f"학습 세션 마이그레이션 완료: {len(sessions)}개의 세션이 이전되었습니다.")
        
        # 답변 기록 마이그레이션
        backup_cursor.execute("""
            SELECT id, user_id, question_id, category_id, selected_answer,
                   is_correct, created_at 
            FROM answer_record
        """)
        records = backup_cursor.fetchall()
        
        for record in records:
            # selected_answer를 selected_statement_id로 사용
            # 정답인 경우 selected_answer를 correct_statement_id로도 사용
            new_cursor.execute("""
                INSERT INTO answer_record (
                    id, user_id, question_id, category_id, 
                    selected_statement_id, correct_statement_id,
                    is_correct, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record[0], record[1], record[2], record[3],
                record[4], record[4] if record[5] else None,
                record[5], record[6]
            ))
        
        # 변경사항 저장
        new_conn.commit()
        print(f"답변 기록 마이그레이션 완료: {len(records)}개의 기록이 이전되었습니다.")
        
    except Exception as e:
        print(f"마이그레이션 중 오류 발생: {e}")
        new_conn.rollback()
    finally:
        backup_conn.close()
        new_conn.close()

if __name__ == "__main__":
    migrate_learning_data() 