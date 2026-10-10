import pymysql

conn = pymysql.connect(host='127.0.0.1', port=3306, user='root', password='', database='nexthire_db')
with conn.cursor() as cur:
    cur.execute("SHOW COLUMNS FROM resumes LIKE 'extracted_skills'")
    if not cur.fetchone():
        cur.execute("ALTER TABLE resumes ADD COLUMN extracted_skills JSON NULL")
        print("Added extracted_skills column to resumes")

    cur.execute("SHOW COLUMNS FROM resumes LIKE 'extracted_text'")
    if not cur.fetchone():
        cur.execute("ALTER TABLE resumes ADD COLUMN extracted_text LONGTEXT NULL")
        print("Added extracted_text column to resumes")

conn.commit()
conn.close()
print("Migration completed successfully!")
