from app import app, db
from sqlalchemy import text
from datetime import datetime
import pytz

print("开始更新Collection表结构...")

with app.app_context():
    try:
        # 获取数据库引擎
        engine = db.engine
        connection = engine.connect()
        
        # 检查表是否存在
        inspector = db.inspect(engine)
        table_exists = inspector.has_table('collection')
        
        if table_exists:
            # 检查字段是否存在
            columns = [col['name'] for col in inspector.get_columns('collection')]
            
            # 执行SQL语句来添加缺失的字段
            if 'is_public' not in columns:
                print("添加is_public字段...")
                connection.execute(text("ALTER TABLE collection ADD COLUMN is_public BOOLEAN DEFAULT 0"))
                
            if 'updated_at' not in columns:
                print("添加updated_at字段...")
                connection.execute(text("ALTER TABLE collection ADD COLUMN updated_at DATETIME"))
                
                # 为现有记录设置updated_at值
                print("更新现有记录的updated_at值...")
                connection.execute(text("UPDATE collection SET updated_at = created_at"))
                
            # 提交更改
            connection.commit()
            print("Collection表结构更新成功！")
        else:
            print("collection表不存在，将创建完整表结构")
            db.create_all()
            print("表结构创建成功！")
    except Exception as e:
        print(f"更新失败: {str(e)}")
    finally:
        connection.close()

print("迁移脚本执行完毕。")