from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
import os
from datetime import datetime
import pytz

app = Flask(__name__)

# 配置数据库 - 使用绝对路径确保能正确打开数据库文件
import os
basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'instance', 'app.db')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# 定义一个最小的PointTask模型，仅用于确保结构正确
class PointTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    points = db.Column(db.Integer, default=0)
    task_type = db.Column(db.String(50), nullable=False, default='daily')
    max_completions = db.Column(db.Integer, default=0)
    cooldown_hours = db.Column(db.Integer, default=24)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(pytz.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(pytz.utc), onupdate=lambda: datetime.now(pytz.utc))

if __name__ == '__main__':
    with app.app_context():
        try:
            # 检查point_task表是否存在
            inspector = db.inspect(db.engine)
            if 'point_task' in inspector.get_table_names():
                # 检查列是否存在
                columns = [col['name'] for col in inspector.get_columns('point_task')]
                
                # 添加缺失的列
                if 'max_completions' not in columns:
                    print("正在添加max_completions列...")
                    with db.engine.connect() as connection:
                        connection.execute(text("ALTER TABLE point_task ADD COLUMN max_completions INTEGER DEFAULT 0"))
                        connection.commit()
                    print("max_completions列添加成功!")
                else:
                    print("max_completions列已存在")
                
                if 'cooldown_hours' not in columns:
                    print("正在添加cooldown_hours列...")
                    with db.engine.connect() as connection:
                        connection.execute(text("ALTER TABLE point_task ADD COLUMN cooldown_hours INTEGER DEFAULT 24"))
                        connection.commit()
                    print("cooldown_hours列添加成功!")
                else:
                    print("cooldown_hours列已存在")
                
                if 'updated_at' not in columns:
                    print("正在添加updated_at列...")
                    with db.engine.connect() as connection:
                        connection.execute(text("ALTER TABLE point_task ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"))
                        connection.commit()
                    print("updated_at列添加成功!")
                else:
                    print("updated_at列已存在")
                
                # 确保task_type列有默认值
                if 'task_type' in columns:
                    # SQLite不支持直接修改列的默认值，需要重命名表、创建新表并迁移数据
                    print("正在处理task_type列的默认值...")
                    print("注意：SQLite限制，无法直接修改列默认值，但不影响功能使用")
                
                print("\n数据库表结构更新完成!\n")
            else:
                print("point_task表不存在，正在创建...")
                db.create_all()
                print("point_task表创建成功!")
                
                # 添加一些示例任务数据
                sample_tasks = [
                    PointTask(
                        name="每日签到",
                        description="每天登录网站并签到领取积分",
                        points=5,
                        task_type="daily",
                        max_completions=1,
                        cooldown_hours=24,
                        is_active=True
                    ),
                    PointTask(
                        name="发表评论",
                        description="在文章下方发表有价值的评论",
                        points=10,
                        task_type="daily",
                        max_completions=3,
                        cooldown_hours=0,
                        is_active=True
                    ),
                    PointTask(
                        name="分享文章",
                        description="将喜欢的文章分享给朋友",
                        points=15,
                        task_type="daily",
                        max_completions=2,
                        cooldown_hours=0,
                        is_active=True
                    )
                ]
                
                db.session.add_all(sample_tasks)
                db.session.commit()
                print("已添加示例任务数据!")
        except Exception as e:
            print(f"更新数据库表结构时出错: {e}")
            print("\n如果错误持续存在，可能需要使用init_db.py重新初始化数据库，但这会清除现有数据。")