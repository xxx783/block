from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import datetime
import pytz
import os

# 创建Flask应用
app = Flask(__name__)

# 使用绝对路径指定数据库位置，与主应用保持一致
import os
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'app.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化数据库
db = SQLAlchemy(app)

# 定义Article模型（只包含需要修改的部分）
class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(pytz.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(pytz.utc), onupdate=lambda: datetime.now(pytz.utc))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    vip_only = db.Column(db.Boolean, default=False)
    vip_level_required = db.Column(db.Integer, default=0)
    views = db.Column(db.Integer, default=0)
    # 添加审核相关字段
    is_approved = db.Column(db.Boolean, default=False)  # 默认为待审核状态
    reject_reason = db.Column(db.Text, nullable=True)  # 拒绝原因，可以为null
    reviewed_at = db.Column(db.DateTime, nullable=True)  # 审核时间
    reviewed_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # 审核人ID

# 定义User模型（最小化，只用于外键关联）
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)

# 创建修改表结构的函数
def update_article_table():
    with app.app_context():
        # 检查数据库连接
        try:
            # 获取当前的表结构信息
            from sqlalchemy import inspect, text
            inspector = inspect(db.engine)
            columns = inspector.get_columns('article')
            column_names = [col['name'] for col in columns]
            
            # 使用text()函数包装SQL语句
            if 'is_approved' not in column_names:
                db.session.execute(text("ALTER TABLE article ADD COLUMN is_approved BOOLEAN DEFAULT 0"))
                print("已添加is_approved字段")
            
            if 'reject_reason' not in column_names:
                db.session.execute(text("ALTER TABLE article ADD COLUMN reject_reason TEXT"))
                print("已添加reject_reason字段")
            
            if 'reviewed_at' not in column_names:
                db.session.execute(text("ALTER TABLE article ADD COLUMN reviewed_at DATETIME"))
                print("已添加reviewed_at字段")
            
            if 'reviewed_by' not in column_names:
                db.session.execute(text("ALTER TABLE article ADD COLUMN reviewed_by INTEGER"))
                print("已添加reviewed_by字段")
                # SQLite不支持通过ALTER TABLE添加外键约束，跳过这一步
                print("SQLite不支持通过ALTER TABLE添加外键约束，跳过此步骤")
            
            # 提交更改
            db.session.commit()
            
            print("数据库表更新成功！")
            
        except Exception as e:
            print(f"更新数据库表时出错: {e}")

if __name__ == '__main__':
    update_article_table()