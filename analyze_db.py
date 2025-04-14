import sqlite3
import os

def analyze_db(db_path):
    if not os.path.exists(db_path):
        print(f"데이터베이스 파일이 존재하지 않습니다: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 테이블 목록 조회
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print(f"\n=== {db_path} 분석 ===")
    print("\n테이블 목록:")
    for table in tables:
        table_name = table[0]
        print(f"\n테이블: {table_name}")
        
        # 테이블 스키마 조회
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        print("컬럼:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        
        # 레코드 수 조회
        cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
        count = cursor.fetchone()[0]
        print(f"레코드 수: {count}")
        
        # 샘플 데이터 조회 (최대 5개)
        if count > 0:
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 5;")
            samples = cursor.fetchall()
            print("샘플 데이터:")
            for sample in samples:
                print(f"  {sample}")
    
    conn.close()

# 현재 데이터베이스와 백업 데이터베이스 분석
analyze_db("instance/police_promo.db")
analyze_db("instance/police_promo_backup.db") 