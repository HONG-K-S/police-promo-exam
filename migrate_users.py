import sqlite3
import os
from werkzeug.security import generate_password_hash

def migrate_users():
    # 백업 DB와 새 DB 연결
    backup_conn = sqlite3.connect('instance/police_promo_backup.db')
    new_conn = sqlite3.connect('instance/police_promo.db')
    
    backup_cursor = backup_conn.cursor()
    new_cursor = new_conn.cursor()
    
    try:
        # 기존 사용자 데이터 삭제
        new_cursor.execute("DELETE FROM user")
        print("기존 사용자 데이터 삭제 완료")
        
        # 백업 DB에서 사용자 데이터 조회
        backup_cursor.execute("SELECT id, username, name, rank, department, email, phone, password, is_admin, is_active, created_at, last_login FROM user")
        users = backup_cursor.fetchall()
        
        # 새 DB에 사용자 데이터 삽입
        for user in users:
            # 비밀번호 해시 생성 (이미 해시된 비밀번호는 그대로 사용)
            password_hash = user[7] if user[7].startswith('scrypt:') else generate_password_hash(user[7])
            
            new_cursor.execute("""
                INSERT INTO user (id, username, name, rank, department, email, phone, password_hash, is_admin, is_active, created_at, last_login)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (user[0], user[1], user[2], user[3], user[4], user[5], user[6], password_hash, user[8], user[9], user[10], user[11]))
        
        # 변경사항 저장
        new_conn.commit()
        print(f"사용자 데이터 마이그레이션 완료: {len(users)}명의 사용자가 이전되었습니다.")
        
    except Exception as e:
        print(f"마이그레이션 중 오류 발생: {e}")
        new_conn.rollback()
    finally:
        backup_conn.close()
        new_conn.close()

if __name__ == "__main__":
    migrate_users() 