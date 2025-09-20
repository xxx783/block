#!/usr/bin/env python3
"""
创建VIP会员兑换选项表的脚本
"""

import sys
import os
from datetime import datetime, timedelta
import pytz

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# 创建临时应用实例
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.abspath(os.path.join('instance', 'app.db')).replace('\\', '/')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# 定义VipOption模型
class VipOption(db.Model):
    __tablename__ = 'vip_option'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    days = db.Column(db.Integer, nullable=False)
    points = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(pytz.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(pytz.utc), onupdate=lambda: datetime.now(pytz.utc))

def create_vip_option_table():
    with app.app_context():
        try:
            # 检查VipOption表是否已存在
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            if 'vip_option' not in inspector.get_table_names():
                # 创建表
                db.create_all()
                print("✓ VIP会员兑换选项表创建成功!")
                
                # 添加初始数据（如果需要）
                initial_options = [
                    VipOption(name='7天会员', days=7, points=100, description='体验一周会员特权'),
                    VipOption(name='30天会员', days=30, points=300, description='一个月会员特权'),
                    VipOption(name='90天会员', days=90, points=750, description='三个月会员特权，享9折优惠'),
                    VipOption(name='365天会员', days=365, points=2800, description='一年会员特权，享7折优惠')
                ]
                
                for option in initial_options:
                    db.session.add(option)
                db.session.commit()
                print("✓ 初始VIP兑换选项添加成功!")
            else:
                print("✓ VIP会员兑换选项表已存在")
                
            # 显示当前的VIP兑换选项
            print("\n当前的VIP兑换选项:")
            options = VipOption.query.all()
            for option in options:
                status = "激活" if option.is_active else "禁用"
                print(f"ID: {option.id}, 名称: {option.name}, 天数: {option.days}, 积分: {option.points}, 状态: {status}")
                
            return True
        except Exception as e:
            print(f"✗ 创建VIP会员兑换选项表失败: {str(e)}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            return False

if __name__ == "__main__":
    create_vip_option_table()