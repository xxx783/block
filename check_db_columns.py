import sqlite3
import os

# 检查数据库文件是否存在
db_path = 'site.db'
print(f"数据库文件路径: {db_path}")
print(f"文件是否存在: {os.path.exists(db_path)}")

# 如果文件存在，检查文件大小
if os.path.exists(db_path):
    print(f"数据库文件大小: {os.path.getsize(db_path)} 字节")

# 尝试连接到数据库并查看所有表
try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 查看数据库中的所有表
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print("\n数据库中的表:")
    for table in tables:
        print(f"- {table[0]}")
    
    # 关闭连接
    conn.close()
    
except Exception as e:
    print(f"连接数据库时出错: {e}")