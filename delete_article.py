#!/usr/bin/env python3
"""
删除文章工具脚本
用于独立删除指定ID的文章，处理所有相关的级联删除关系
"""

import sys
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pytz

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 创建Flask应用实例
app = Flask(__name__)

# 配置数据库 - 使用绝对路径确保能正确打开数据库文件
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'app.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化数据库
db = SQLAlchemy(app)

# 定义必要的模型（最小化定义，仅用于删除操作）
class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

class Article(db.Model):
    __tablename__ = 'article'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(pytz.utc))
    
    # 定义级联删除关系
    comments = db.relationship('Comment', backref='article', lazy=True, cascade='all, delete-orphan')
    favorites = db.relationship('Favorite', backref='article', lazy=True, cascade='all, delete-orphan')
    likes = db.relationship('Like', backref='article', lazy=True, cascade='all, delete-orphan')
    source_article_collections = db.relationship('SourceArticleCollection', backref='article', lazy=True, cascade='all, delete-orphan')
    related_articles_as_source = db.relationship('ArticleRelation', foreign_keys='ArticleRelation.source_article_id', backref='source_article', lazy=True, cascade='all, delete-orphan')
    related_articles_as_target = db.relationship('ArticleRelation', foreign_keys='ArticleRelation.target_article_id', backref='target_article', lazy=True, cascade='all, delete-orphan')
    related_announcements = db.relationship('AnnouncementArticleRelation', backref='article', lazy=True, cascade='all, delete-orphan')
    
    # 关联用户
    author = db.relationship('User')

# 定义关联模型
class Comment(db.Model):
    __tablename__ = 'comment'
    id = db.Column(db.Integer, primary_key=True)
    article_id = db.Column(db.Integer, db.ForeignKey('article.id'), nullable=False)

class Favorite(db.Model):
    __tablename__ = 'favorite'
    id = db.Column(db.Integer, primary_key=True)
    article_id = db.Column(db.Integer, db.ForeignKey('article.id'), nullable=False)

class Like(db.Model):
    __tablename__ = 'like'
    id = db.Column(db.Integer, primary_key=True)
    article_id = db.Column(db.Integer, db.ForeignKey('article.id'), nullable=False)

class SourceArticleCollection(db.Model):
    __tablename__ = 'source_article_collection'
    id = db.Column(db.Integer, primary_key=True)
    article_id = db.Column(db.Integer, db.ForeignKey('article.id'), nullable=False)

class ArticleRelation(db.Model):
    __tablename__ = 'article_relation'
    id = db.Column(db.Integer, primary_key=True)
    source_article_id = db.Column(db.Integer, db.ForeignKey('article.id'), nullable=False)
    target_article_id = db.Column(db.Integer, db.ForeignKey('article.id'), nullable=False)

class AnnouncementArticleRelation(db.Model):
    __tablename__ = 'announcement_article_relation'
    id = db.Column(db.Integer, primary_key=True)
    article_id = db.Column(db.Integer, db.ForeignKey('article.id'), nullable=False)

def delete_article_by_id(article_id, current_user_id=None):
    """
    根据文章ID删除文章
    
    参数:
        article_id: 要删除的文章ID
        current_user_id: 当前用户ID（可选），如果提供，则进行权限检查
    
    返回:
        tuple: (是否成功, 消息)
    """
    with app.app_context():
        try:
            # 查找文章
            article = Article.query.get(article_id)
            
            if not article:
                return False, f"文章ID {article_id} 不存在"
            
            # 权限检查（如果提供了current_user_id）
            if current_user_id:
                current_user = User.query.get(current_user_id)
                if not current_user:
                    return False, "无效的用户ID"
                
                # 只有文章作者或管理员可以删除
                if not (current_user.is_admin or article.user_id == current_user_id):
                    return False, "权限不足，只有文章作者或管理员可以删除文章"
            
            # 开始事务
            db.session.begin()
            
            try:
                # 记录要删除的文章信息
                article_title = article.title
                
                # 直接删除文章，级联删除会自动处理关联记录
                db.session.delete(article)
                db.session.commit()
                
                return True, f"成功删除文章：{article_title}（ID: {article_id}）"
                
            except Exception as e:
                db.session.rollback()
                return False, f"删除文章时发生错误: {str(e)}"
                
        except Exception as e:
            return False, f"操作数据库时发生错误: {str(e)}"

def delete_multiple_articles(article_ids, current_user_id=None):
    """
    批量删除多篇文章
    
    参数:
        article_ids: 文章ID列表
        current_user_id: 当前用户ID（可选）
    
    返回:
        dict: 包含成功和失败信息
    """
    results = {
        'success_count': 0,
        'failed_count': 0,
        'success_articles': [],
        'failed_articles': []
    }
    
    for article_id in article_ids:
        success, message = delete_article_by_id(article_id, current_user_id)
        if success:
            results['success_count'] += 1
            results['success_articles'].append({
                'id': article_id,
                'message': message
            })
        else:
            results['failed_count'] += 1
            results['failed_articles'].append({
                'id': article_id,
                'error': message
            })
    
    return results

def main():
    """
    命令行入口函数
    """
    print("===== 删除文章工具 =====")
    
    # 解析命令行参数
    if len(sys.argv) < 2:
        print("用法:")
        print(f"  python {sys.argv[0]} <文章ID> [用户ID]")
        print(f"  python {sys.argv[0]} --batch <文章ID1> <文章ID2> ... [用户ID]")
        sys.exit(1)
    
    # 批量删除模式
    if sys.argv[1] == '--batch':
        if len(sys.argv) < 3:
            print("批量删除模式需要至少一个文章ID")
            sys.exit(1)
            
        # 提取文章ID列表
        try:
            article_ids = [int(id_str) for id_str in sys.argv[2:] if id_str.isdigit()]
            # 检查是否有用户ID
            user_id_arg = None
            for arg in sys.argv[2:]:
                if not arg.isdigit():
                    try:
                        user_id_arg = int(arg)
                        break
                    except ValueError:
                        pass
            
            print(f"准备批量删除 {len(article_ids)} 篇文章")
            if user_id_arg:
                print(f"使用用户ID {user_id_arg} 进行权限检查")
                
            # 执行批量删除
            results = delete_multiple_articles(article_ids, user_id_arg)
            
            # 打印结果
            print("\n删除结果:")
            print(f"成功删除: {results['success_count']} 篇")
            print(f"删除失败: {results['failed_count']} 篇")
            
            if results['success_articles']:
                print("\n成功删除的文章:")
                for art in results['success_articles']:
                    print(f"- {art['message']}")
                    
            if results['failed_articles']:
                print("\n删除失败的文章:")
                for art in results['failed_articles']:
                    print(f"- ID: {art['id']}, 错误: {art['error']}")
                    
        except ValueError:
            print("错误：文章ID必须是数字")
            sys.exit(1)
            
    # 单篇删除模式
    else:
        try:
            article_id = int(sys.argv[1])
            user_id = int(sys.argv[2]) if len(sys.argv) > 2 else None
            
            print(f"准备删除文章 ID: {article_id}")
            if user_id:
                print(f"使用用户ID {user_id} 进行权限检查")
                
            # 执行删除
            success, message = delete_article_by_id(article_id, user_id)
            
            # 打印结果
            if success:
                print(f"\n✓ {message}")
            else:
                print(f"\n✗ {message}")
                
        except ValueError:
            print("错误：文章ID和用户ID必须是数字")
            sys.exit(1)

if __name__ == '__main__':
    main()