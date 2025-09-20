#!/usr/bin/env python3
"""
初始化数据库脚本
独立于主应用，避免导入时的数据库查询问题
"""

import sys
import os
from datetime import datetime
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

# 模型定义
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(pytz.utc))
    is_admin = db.Column(db.Boolean, default=False)
    is_vip = db.Column(db.Boolean, default=False)
    is_banned = db.Column(db.Boolean, default=False)
    vip_expires_at = db.Column(db.DateTime)
    vip_level = db.Column(db.Integer, default=0)
    
    # 关系
    articles = db.relationship('Article', backref='author', lazy=True)
    comments = db.relationship('Comment', backref='author', lazy=True)
    favorites = db.relationship('Favorite', backref='user', lazy=True)
    likes = db.relationship('Like', backref='user', lazy=True)
    user_points = db.relationship('UserPoints', backref='user', uselist=False, lazy=True)

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
    
    # 关系
    comments = db.relationship('Comment', backref='article', lazy=True, cascade='all, delete-orphan')
    favorites = db.relationship('Favorite', backref='article', lazy=True, cascade='all, delete-orphan')
    likes = db.relationship('Like', backref='article', lazy=True, cascade='all, delete-orphan')

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(pytz.utc))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    article_id = db.Column(db.Integer, db.ForeignKey('article.id'), nullable=False)
    is_pinned = db.Column(db.Boolean, default=False)

class Favorite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    article_id = db.Column(db.Integer, db.ForeignKey('article.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(pytz.utc))
    
    __table_args__ = (db.UniqueConstraint('user_id', 'article_id', name='unique_favorite'),)

class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    article_id = db.Column(db.Integer, db.ForeignKey('article.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(pytz.utc))
    
    __table_args__ = (db.UniqueConstraint('user_id', 'article_id', name='unique_like'),)

class UserPoints(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    total_points = db.Column(db.Integer, default=0)
    available_points = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(pytz.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(pytz.utc), onupdate=lambda: datetime.now(pytz.utc))

class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(pytz.utc))
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # 关系
    creator = db.relationship('User')

class VersionUpdate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    version = db.Column(db.String(20), nullable=False)
    release_date = db.Column(db.DateTime, default=lambda: datetime.now(pytz.utc))
    content = db.Column(db.Text, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(pytz.utc))
    
    # 关系
    creator = db.relationship('User')

class Collection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(pytz.utc))
    
    # 关系
    user = db.relationship('User', backref='collections')

class UserVersionConfirm(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    version = db.Column(db.String(20), nullable=False)
    confirmed_at = db.Column(db.DateTime, default=lambda: datetime.now(pytz.utc))
    
    # 关系
    user = db.relationship('User', backref='version_confirms')
    
    # 唯一约束，一个用户对一个版本只能确认一次
    __table_args__ = (db.UniqueConstraint('user_id', 'version'),)

class SourceArticleCollection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    article_id = db.Column(db.Integer, db.ForeignKey('article.id'), nullable=False)
    collection_id = db.Column(db.Integer, db.ForeignKey('collection.id'), nullable=False)
    added_at = db.Column(db.DateTime, default=lambda: datetime.now(pytz.utc))
    
    __table_args__ = (db.UniqueConstraint('article_id', 'collection_id', name='unique_article_collection'),)

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

class PointTaskCompletion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('point_task.id'), nullable=False)
    completed_at = db.Column(db.DateTime, default=lambda: datetime.now(pytz.utc))
    points_awarded = db.Column(db.Integer, default=0)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'task_id', name='unique_task_completion'),)

class PointRedemption(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    points_required = db.Column(db.Integer, default=0)
    type = db.Column(db.String(50), nullable=False)
    value = db.Column(db.String(200), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(pytz.utc))

class ArticleRelation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    source_article_id = db.Column(db.Integer, db.ForeignKey('article.id'), nullable=False)
    target_article_id = db.Column(db.Integer, db.ForeignKey('article.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(pytz.utc))
    
    # 关系
    source_article = db.relationship('Article', foreign_keys=[source_article_id], backref='related_articles_as_source')
    target_article = db.relationship('Article', foreign_keys=[target_article_id], backref='related_articles_as_target')
    
    # 唯一约束，防止重复关联
    __table_args__ = (db.UniqueConstraint('source_article_id', 'target_article_id', name='unique_article_relation'),)

class AnnouncementArticleRelation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    announcement_id = db.Column(db.Integer, db.ForeignKey('announcement.id'), nullable=False)
    article_id = db.Column(db.Integer, db.ForeignKey('article.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(pytz.utc))
    
    # 关系
    announcement = db.relationship('Announcement', backref='related_articles')
    article = db.relationship('Article')
    
    # 唯一约束，防止重复关联
    __table_args__ = (db.UniqueConstraint('announcement_id', 'article_id', name='unique_announcement_article_relation'),)

# 在文件末尾的if __name__ == "__main__":块内替换现有的检查代码
if __name__ == "__main__":
    with app.app_context():
        print("正在创建数据库表...")
        db.create_all()
        print("数据库表创建完成！")
        
        # 检查表结构
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        print(f"数据库中的表: {tables}")
        
        # 需要检查的表和它们的关键列
        tables_to_check = {
            'user': ['id', 'username', 'email', 'password', 'is_banned'],
            'article': ['id', 'title', 'content', 'user_id', 'views'],
            'source_article_collection': ['id', 'article_id', 'collection_id'],
            'article_relation': ['id', 'source_article_id', 'target_article_id'],
            'collection': ['id', 'name', 'user_id'],
            'point_task': ['id', 'name', 'points', 'task_type']
        }
        
        # 检查每个表的结构
        for table_name, required_columns in tables_to_check.items():
            if table_name in tables:
                columns = inspector.get_columns(table_name)
                column_names = [col['name'] for col in columns]
                
                print(f"\n{table_name}表的列:")
                for col in columns:
                    print(f"  - {col['name']}: {col['type']}")
                
                # 检查所有必需的列是否存在
                missing_columns = [col for col in required_columns if col not in column_names]
                if missing_columns:
                    print(f"✗ 缺少必需的列: {', '.join(missing_columns)}")
                    print(f"✗ 建议操作: 请重命名或删除现有的instance/app.db文件，然后重新运行此脚本以创建正确的表结构")
                else:
                    print(f"✓ 所有必需的列都已存在")
            else:
                print(f"\n✗ {table_name}表不存在，将在重启后创建")
        
        # 修改前代码（文件末尾部分）
        if 'user' in tables:
            columns = inspector.get_columns('user')
            print("User表的列:")
            for col in columns:
                print(f"  - {col['name']}: {col['type']}")
            
            # 检查is_banned字段是否存在
            column_names = [col['name'] for col in columns]
            if 'is_banned' in column_names:
                print("✓ is_banned字段已成功添加")
            else:
                print("✗ is_banned字段未找到，请检查模型定义")
        
        # 修改后代码
        # 检查User表结构
        if 'user' in tables:
            columns = inspector.get_columns('user')
            print("User表的列:")
            for col in columns:
                print(f"  - {col['name']}: {col['type']}")
            
            # 检查is_banned字段是否存在
            column_names = [col['name'] for col in columns]
            if 'is_banned' in column_names:
                print("✓ is_banned字段已成功添加")
            else:
                print("✗ is_banned字段未找到，请检查模型定义")
        
        # 检查source_article_collection表结构
        if 'source_article_collection' in tables:
            columns = inspector.get_columns('source_article_collection')
            print("SourceArticleCollection表的列:")
            for col in columns:
                print(f"  - {col['name']}: {col['type']}")
            
            # 检查id字段是否存在
            column_names = [col['name'] for col in columns]
            if 'id' in column_names:
                print("✓ id字段已成功添加")
            else:
                print("✗ id字段未找到，需要重新创建表")
        else:
            print("✗ source_article_collection表不存在，将在重启后创建")