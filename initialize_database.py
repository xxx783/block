#!/usr/bin/env python3
"""
数据库初始化脚本
负责创建数据库表、添加示例数据和默认用户账号
"""

import sys
import os
from datetime import datetime, timedelta
import pytz
from werkzeug.security import generate_password_hash

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
# 先定义基础模型，然后再定义关系
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

class VersionUpdate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    version = db.Column(db.String(20), nullable=False)
    release_date = db.Column(db.DateTime, default=lambda: datetime.now(pytz.utc))
    content = db.Column(db.Text, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(pytz.utc))

class Collection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(pytz.utc))

class UserVersionConfirm(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    version = db.Column(db.String(20), nullable=False)
    confirmed_at = db.Column(db.DateTime, default=lambda: datetime.now(pytz.utc))
    
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

class ArticleRelation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    source_article_id = db.Column(db.Integer, db.ForeignKey('article.id'), nullable=False)
    target_article_id = db.Column(db.Integer, db.ForeignKey('article.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(pytz.utc))
    
    # 唯一约束，防止重复关联
    __table_args__ = (db.UniqueConstraint('source_article_id', 'target_article_id', name='unique_article_relation'),)

class AnnouncementArticleRelation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    announcement_id = db.Column(db.Integer, db.ForeignKey('announcement.id'), nullable=False)
    article_id = db.Column(db.Integer, db.ForeignKey('article.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(pytz.utc))
    
    # 唯一约束，防止重复关联
    __table_args__ = (db.UniqueConstraint('announcement_id', 'article_id', name='unique_announcement_article'),)

# 定义关系（在所有模型定义之后）
# User.articles关系已在Article模型中通过backref定义为authored_articles
User.comments = db.relationship('Comment', backref='author', lazy=True)
User.favorites = db.relationship('Favorite', backref='user', lazy=True)
User.likes = db.relationship('Like', backref='user', lazy=True)
User.user_points = db.relationship('UserPoints', backref='user', uselist=False, lazy=True)
User.collections = db.relationship('Collection', backref='user', lazy=True)
User.version_confirms = db.relationship('UserVersionConfirm', backref='user', lazy=True)

Article.comments = db.relationship('Comment', backref='article', lazy=True, cascade='all, delete-orphan')
Article.favorites = db.relationship('Favorite', backref='article', lazy=True, cascade='all, delete-orphan')
Article.likes = db.relationship('Like', backref='article', lazy=True, cascade='all, delete-orphan')
Article.source_article_collections = db.relationship('SourceArticleCollection', backref='article', lazy=True, cascade='all, delete-orphan')

# 关联模型的关系定义
# 避免backref名称冲突，使用不同的名称
SourceArticleCollection.article_rel = db.relationship('Article', backref='collections_associated')
SourceArticleCollection.collection_rel = db.relationship('Collection', backref='articles_associated')

Announcement.creator = db.relationship('User', backref='announcements')
VersionUpdate.creator = db.relationship('User', backref='version_updates')
Announcement.related_articles = db.relationship('Article', secondary='announcement_article_relation', backref='related_announcements')

# 创建管理员账号和普通用户账号
def create_default_users():
    try:
        # 检查instance目录是否存在，如果不存在则创建
        instance_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
        if not os.path.exists(instance_dir):
            os.makedirs(instance_dir)
            print(f"✓ 创建instance目录成功: {instance_dir}")
        
        # 创建所有数据库表
        db.create_all()
        print("✓ 数据库表创建成功!")
        
        # 检查管理员账号是否已存在
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            # 创建管理员账号
            admin_hashed_password = generate_password_hash('admin123')
            admin_user = User(
                username='admin',
                email='admin@example.com',
                password=admin_hashed_password,
                is_admin=True,
                is_vip=True,
                vip_level=1,
                vip_expires_at=datetime.now(pytz.utc) + timedelta(days=365),  # 会员有效期1年
                created_at=datetime.now(pytz.utc)
            )
            db.session.add(admin_user)
            db.session.commit()
            print("✓ 管理员账号创建成功!")
            print("   用户名: admin")
            print("   密码: admin123")
        else:
            print("✓ 管理员账号已存在")
        
        # 检查普通用户账号是否已存在
        normal_user = User.query.filter_by(username='user1').first()
        if not normal_user:
            # 创建普通用户账号
            user_hashed_password = generate_password_hash('user123')
            normal_user = User(
                username='user1',
                email='user1@example.com',
                password=user_hashed_password,
                is_admin=False,
                is_vip=False,
                created_at=datetime.now(pytz.utc)
            )
            db.session.add(normal_user)
            db.session.commit()
            print("✓ 普通用户账号创建成功!")
            print("   用户名: user1")
            print("   密码: user123")
        else:
            print("✓ 普通用户账号已存在")
        
        # 为管理员和普通用户创建积分记录
        if admin_user and not hasattr(admin_user, 'user_points'):
            admin_points = UserPoints(user_id=admin_user.id, total_points=10000, available_points=10000)
            db.session.add(admin_points)
        
        if normal_user and not hasattr(normal_user, 'user_points'):
            normal_points = UserPoints(user_id=normal_user.id, total_points=1000, available_points=1000)
            db.session.add(normal_points)
        
        db.session.commit()
        print("✓ 用户积分记录创建成功!")
        
        print("============================================================")
        print("                  数据库初始化完成!")
        print("============================================================")
        print("现在您可以使用以下账号登录系统:")
        print("1. 管理员账号: 用户名='admin', 密码='admin123'")
        print("2. 普通用户账号: 用户名='user1', 密码='user123'")
        print("============================================================")
        return True
    except Exception as e:
        print(f"✗ 数据库初始化失败: {str(e)}")
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return False

if __name__ == "__main__":
    with app.app_context():
        create_default_users()