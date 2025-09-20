from flask import Flask, render_template, redirect, url_for, flash, request, session, jsonify
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import pytz
import markdown
import re
import os
import random
import string
from functools import wraps

# 初始化Flask应用
app = Flask(__name__)

# 配置 - 优先从环境变量获取，没有则使用默认值
import os
import logging

# SECRET_KEY配置 - 优先从环境变量获取
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# 数据库配置 - 支持多种数据库选项

# 1. 检查是否通过环境变量指定了数据库连接字符串
DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL:
    # 使用环境变量指定的数据库连接
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
else:
    # 默认使用SQLite数据库（使用绝对路径避免权限问题）
    # 确保instance目录存在
    base_dir = os.path.dirname(os.path.abspath(__file__))
    instance_dir = os.path.join(base_dir, 'instance')
    if not os.path.exists(instance_dir):
        try:
            os.makedirs(instance_dir)
            print(f"已创建instance目录: {instance_dir}")
        except Exception as e:
            print(f"创建instance目录失败: {str(e)}")

    # 构建绝对数据库路径
db_path = os.path.join(base_dir, 'instance', 'app.db')
print(f"数据库路径: {db_path}")
print(f"数据库文件是否存在: {os.path.exists(db_path)}")

    # 配置SQLAlchemy数据库URI
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'

# SQLAlchemy通用配置
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 增加SQLAlchemy引擎配置，处理并发和超时问题
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'connect_args': {
        'timeout': 30,  # 增加连接超时时间
        'check_same_thread': False  # 允许在不同线程中使用连接
    }
}

# 配置日志记录数据库操作
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('app')
logger.info(f"数据库已配置: {db_path}")

# 邮件配置 - 优先从环境变量获取
# 虚拟主机环境中，如果邮件功能不可用，可以通过环境变量禁用
app.config['MAIL_ENABLED'] = os.environ.get('MAIL_ENABLED', 'True').lower() == 'true'

if app.config['MAIL_ENABLED']:
    # 邮件服务器配置
    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.163.com')
    app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 465))
    app.config['MAIL_USE_SSL'] = os.environ.get('MAIL_USE_SSL', 'True').lower() == 'true'
    app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'False').lower() == 'true'
    
    # 邮箱认证信息 - 建议通过环境变量设置
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', 'your-email@example.com')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', 'your-password-or-app-password')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', app.config['MAIL_USERNAME'])
    
    logger.info(f"邮件功能已启用，服务器: {app.config['MAIL_SERVER']}")
else:
    logger.info("邮件功能已禁用")

# 初始化扩展
db = SQLAlchemy(app)
mail = Mail(app)

# 过滤器将在后续使用装饰器方式定义

# 辅助函数：生成随机验证码
def generate_verification_code(length=6):
    """生成指定长度的随机验证码"""
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

# 辅助函数：发送验证码邮件
def send_verification_email(email):
    """向指定邮箱发送验证码"""
    if not app.config.get('MAIL_ENABLED'):
        return False, "邮件功能未开启"
    
    try:
        # 生成验证码
        code = generate_verification_code()
        # 保存验证码到会话，有效期5分钟
        session['verification_code'] = code
        session['verification_email'] = email
        session['verification_time'] = datetime.now().timestamp()
        
        # 创建邮件消息
        msg = Message('注册验证码', recipients=[email])
        
        # 纯文本部分（用于不支持HTML的邮件客户端）
        msg.body = f"""您的注册验证码是：{code}

验证码有效期为5分钟，请尽快完成注册。

如非本人操作，请忽略此邮件。"""
        
        # HTML部分（美化邮件样式）
        msg.html = f"""<html>
<head>
    <meta charset="UTF-8">
    <title>注册验证码</title>
    <style>
        body {{
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            margin: 0;
            padding: 0;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 600px;
            margin: 20px auto;
            background-color: #ffffff;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 24px;
        }}
        .content {{
            padding: 30px;
        }}
        .verification-code {{
            font-size: 36px;
            font-weight: bold;
            text-align: center;
            color: #667eea;
            letter-spacing: 5px;
            margin: 20px 0;
            padding: 15px;
            background-color: #f8f9fa;
            border-radius: 8px;
            border: 2px dashed #e9ecef;
        }}
        .info-box {{
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
            border-left: 4px solid #667eea;
        }}
        .footer {{
            background-color: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #666;
            font-size: 14px;
            border-top: 1px solid #e9ecef;
        }}
        .highlight {{
            color: #667eea;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>注册验证码</h1>
        </div>
        <div class="content">
            <p>您好，</p>
            <p>感谢您注册我们的服务！您的验证码如下：</p>
            
            <div class="verification-code">{code}</div>
            
            <div class="info-box">
                <p>• 验证码有效期为 <span class="highlight">5分钟</span></p>
                <p>• 请在有效期内完成注册</p>
                <p>• 如非本人操作，请忽略此邮件</p>
            </div>
            
            <p>如果您在使用过程中遇到任何问题，请随时联系我们的客服团队。</p>
            <p>祝您使用愉快！</p>
        </div>
        <div class="footer">
            <p>此邮件为系统自动发送，请勿回复</p>
        </div>
    </div>
</body>
</html>"""
        
        # 发送邮件
        mail.send(msg)
        return True, "验证码已发送到您的邮箱"
    except Exception as e:
        app.logger.error(f"发送验证码失败: {str(e)}")
        return False, f"发送验证码失败，请稍后重试"

# 辅助函数：验证验证码
def verify_code(email, code):
    """验证邮箱和验证码是否匹配"""
    # 检查会话中是否有验证码
    if 'verification_code' not in session or 'verification_email' not in session or 'verification_time' not in session:
        return False, "验证码已过期，请重新获取"
        
    # 检查邮箱是否匹配
    if session['verification_email'] != email:
        return False, "验证码与邮箱不匹配"
    
    # 检查验证码是否匹配
    if session['verification_code'] != code:
        return False, "验证码错误"
    
    # 检查验证码是否过期（5分钟）
    current_time = datetime.now().timestamp()
    if current_time - session['verification_time'] > 5 * 60:
        return False, "验证码已过期，请重新获取"
    
    # 验证成功，清除会话中的验证码
    session.pop('verification_code', None)
    session.pop('verification_email', None)
    session.pop('verification_time', None)
    
    return True, "验证成功"

# 辅助函数：修改用户积分
def modify_user_points(user_id, points_change, reason='管理员修改积分'):
    """修改用户的积分，并确保积分不会变为负数"""
    try:
        # 获取用户积分记录
        user_points = UserPoints.query.filter_by(user_id=user_id).first()
        if not user_points:
            # 如果用户没有积分记录，创建一个
            user_points = UserPoints(user_id=user_id, total_points=0, available_points=0)
            db.session.add(user_points)
            
        # 更新用户积分
        user_points.total_points += points_change
        user_points.available_points += points_change
        user_points.updated_at = datetime.now(pytz.utc)
        
        # 确保积分不会变成负数
        if user_points.total_points < 0:
            user_points.total_points = 0
        if user_points.available_points < 0:
            user_points.available_points = 0
            
        db.session.commit()
        return True, f"积分修改成功，用户ID: {user_id}, 变动: {points_change}, 原因: {reason}"
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"修改用户积分失败: {str(e)}")
        return False, f"修改积分失败: {str(e)}"

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
    # 使用Article模型中定义的backref名称
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
    # 审核相关字段
    is_approved = db.Column(db.Boolean, default=False)  # 默认为待审核状态
    reject_reason = db.Column(db.Text, nullable=True)  # 拒绝原因，可以为null
    reviewed_at = db.Column(db.DateTime, nullable=True)  # 审核时间
    reviewed_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # 审核人ID
    
    # 关系
    comments = db.relationship('Comment', backref='article', lazy=True, cascade='all, delete-orphan')
    favorites = db.relationship('Favorite', backref='article', lazy=True, cascade='all, delete-orphan')
    likes = db.relationship('Like', backref='article', lazy=True, cascade='all, delete-orphan')
    # 明确指定外键的关系
    author = db.relationship('User', foreign_keys=[user_id], backref='authored_articles', lazy=True)
    reviewer = db.relationship('User', foreign_keys=[reviewed_by], backref='reviewed_articles', lazy=True)

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
    article_relations = db.relationship('AnnouncementArticleRelation', lazy=True, cascade='all, delete-orphan')

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
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(pytz.utc), onupdate=lambda: datetime.now(pytz.utc))
    is_public = db.Column(db.Boolean, default=False)
    
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

class VipOption(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    days = db.Column(db.Integer, nullable=False)
    points = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(pytz.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(pytz.utc), onupdate=lambda: datetime.now(pytz.utc))

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
    article = db.relationship('Article', backref='related_announcements')
    
    # 唯一约束，防止重复关联
    __table_args__ = (db.UniqueConstraint('announcement_id', 'article_id', name='unique_announcement_article'),)

# 自定义过滤器和上下文处理器
@app.template_filter('utc_to_beijing')
def utc_to_beijing_filter(dt):
    # 在函数内部导入模块，确保在任何上下文中都能正常工作
    import pytz
    if dt:
        beijing_tz = pytz.timezone('Asia/Shanghai')
        return dt.astimezone(beijing_tz)
    return dt

# 额外添加：直接注册到Jinja2环境中，确保在任何上下文中都能访问
app.jinja_env.filters['utc_to_beijing'] = utc_to_beijing_filter

@app.template_filter('markdown')
def markdown_filter(text):
    return markdown.markdown(text)

@app.template_filter('format_date')
def format_date_filter(dt, format_str='%Y-%m-%d %H:%M'):
    if dt:
        return dt.strftime(format_str)
    return ''

@app.context_processor
def inject_global_vars():
    # 创建一个简单的匿名用户类，确保即使未登录时也能访问属性而不报错
    class AnonymousUser:
        def __init__(self):
            self.is_vip = False
            self.vip_level = 0
            self.vip_expires_at = None
    
    user = AnonymousUser()  # 默认使用匿名用户对象
    is_logged_in = False
    is_admin = False
    is_vip = False
    vip_expires_at = None
    
    if 'user_id' in session:
        db_user = User.query.get(session['user_id'])
        if db_user and not db_user.is_banned:
            user = db_user  # 登录状态下使用实际用户对象
            is_logged_in = True
            is_admin = user.is_admin
            # 确保VIP到期时间比较时时区一致
            now_utc = datetime.now(pytz.utc)
            if user.vip_expires_at:
                # 如果vip_expires_at没有时区信息，则添加UTC时区
                if user.vip_expires_at.tzinfo is None:
                    vip_expires_at_utc = user.vip_expires_at.replace(tzinfo=pytz.utc)
                else:
                    vip_expires_at_utc = user.vip_expires_at
                is_vip = user.is_vip and (vip_expires_at_utc > now_utc)
            else:
                # 如果没有设置过期时间，则VIP状态由user.is_vip决定
                is_vip = user.is_vip
            vip_expires_at = user.vip_expires_at
    
    # 获取最新公告
    latest_announcement = Announcement.query.order_by(Announcement.created_at.desc()).first()
    
    return {
        'is_logged_in': is_logged_in,
        'current_user': user,
        'is_admin': is_admin,
        'is_vip': is_vip,
        'vip_expires_at': vip_expires_at,
        'latest_announcement': latest_announcement,
        'now': datetime.now(pytz.utc)
    }

@app.context_processor
def inject_functions():
    def get_vip_type(user):
        if user and user.is_vip:
            if user.vip_expires_at:
                now_utc = datetime.now(pytz.utc)
                # 检查user.vip_expires_at是否有时区信息
                if user.vip_expires_at.tzinfo is None or user.vip_expires_at.tzinfo.utcoffset(user.vip_expires_at) is None:
                    # 为无时区信息的时间对象添加UTC时区
                    user_vip_expires_at_utc = user.vip_expires_at.replace(tzinfo=pytz.utc)
                    if user_vip_expires_at_utc < now_utc:
                        return '会员已过期'
                else:
                    # 转换到UTC时区进行比较
                    user_vip_expires_at_utc = user.vip_expires_at.astimezone(pytz.utc)
                    if user_vip_expires_at_utc < now_utc:
                        return '会员已过期'
            if user.vip_level == 1:
                return '超级会员'
            return '会员'
        return ''
    
    def get_article_stats(article):
        comments_count = len(article.comments) if article.comments else 0
        likes_count = len(article.likes) if article.likes else 0
        favorites_count = len(article.favorites) if article.favorites else 0
        return {'comments': comments_count, 'likes': likes_count, 'favorites': favorites_count}
    
    return {
        'get_vip_type': get_vip_type,
        'get_article_stats': get_article_stats
    }

# 添加空的csrf_token上下文处理器，避免模板中调用csrf_token()出错
@app.context_processor
def inject_csrf_token():
    def csrf_token():
        return ''
    return {'csrf_token': csrf_token}

# 装饰器
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('请先登录', 'warning')
            return redirect(url_for('login', next=request.url))
        user = User.query.get(session['user_id'])
        if not user:
            session.pop('user_id', None)
            flash('您的账户不存在', 'danger')
            return redirect(url_for('login'))
        # 新增检查：如果用户被封禁，清除会话并提示
        if user.is_banned:
            session.pop('user_id', None)
            session.pop('username', None)
            session.pop('is_admin', None)
            session.pop('is_vip', None)
            flash('您的账户已被禁用', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# 验证用户未被封禁的装饰器
def user_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('请先登录', 'warning')
            return redirect(url_for('login', next=request.url))
        user = User.query.get(session['user_id'])
        if not user:
            session.pop('user_id', None)
            flash('您的账户不存在', 'danger')
            return redirect(url_for('login'))
        if user.is_banned:
            flash('您的账户已被封禁，无法执行此操作', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# 管理员装饰器保持不变
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('请先登录', 'warning')
            return redirect(url_for('login', next=request.url))
        user = User.query.get(session['user_id'])
        if not user or not user.is_admin:
            flash('您没有权限访问此页面', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def vip_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('请先登录', 'warning')
            return redirect(url_for('login', next=request.url))
        
        user = User.query.get(session['user_id'])
        # 被封禁用户：允许查看（不清除会话、不跳转登录），但禁止操作（提示并拦截）
        if user.is_banned:  # 假设User模型用is_banned标记封禁状态
            flash('您的账户已被封禁，仅可查看，无法执行操作', 'danger')
            return redirect(url_for('index'))  # 跳转首页（或其他允许查看的页面）
        
        # 确保比较的datetime对象都有时区信息
        current_time = datetime.datetime.now(pytz.utc)  # 修正datetime调用
        # VIP权限判断：非VIP或VIP过期，禁止操作
        if not user.is_vip or (user.vip_expires_at and (
            (user.vip_expires_at.tzinfo is not None and user.vip_expires_at.astimezone(pytz.utc) < current_time) or
            (user.vip_expires_at.tzinfo is None and pytz.utc.localize(user.vip_expires_at) < current_time)
        )):
            flash('此功能需要会员权限', 'warning')
            return redirect(url_for('index'))
        
        return f(*args, **kwargs)
    return decorated_function

# 路由
@app.route('/')
def index():
    # 获取最新已审核通过的文章，不包括被禁用户的文章
    articles = Article.query.join(Article.author).filter(User.is_banned == False, Article.is_approved == True).order_by(Article.created_at.desc()).limit(20).all()
    
    # 处理文章内容中的换行符，确保在模板中正确显示
    for article in articles:
        article.content = article.content.replace('\n', '<br>')
        
    return render_template('index.html', articles=articles)

@app.route('/community')
def community():
    # 获取所有未被封禁的作者的已审核通过的文章
    articles = Article.query.join(Article.author).filter(User.is_banned == False, Article.is_approved == True).order_by(Article.created_at.desc()).limit(20).all()
    
    # 获取热门标签（这里假设标签功能会在后续实现，暂时用文章标题中的关键词代替）
    popular_tags = ['电影', '音乐', '科技', '旅行', '美食', '生活', '读书', '健身']
    
    # 获取最新公告
    latest_announcement = Announcement.query.order_by(Announcement.created_at.desc()).first()
    
    # 处理文章内容中的换行符，确保在模板中正确显示
    for article in articles:
        article.content = article.content.replace('\n', '<br>')
    
    return render_template('community.html', articles=articles, popular_tags=popular_tags, latest_announcement=latest_announcement)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/my_collections')
@login_required
def my_collections():
    user = User.query.get(session['user_id'])
    collections = Collection.query.filter_by(user_id=user.id).order_by(Collection.created_at.desc()).all()
    
    # 计算每个合集的文章数量
    for collection in collections:
        collection.article_count = SourceArticleCollection.query.filter_by(collection_id=collection.id).count()
        
    return render_template('my_collections.html', collections=collections)

@app.route('/collection/<int:collection_id>')
def view_collection(collection_id):
    # 获取合集信息
    collection = Collection.query.get_or_404(collection_id)
    
    # 获取合集中的文章关联
    article_relations = SourceArticleCollection.query.filter_by(collection_id=collection_id).order_by(SourceArticleCollection.added_at.desc()).all()
    
    # 获取文章ID列表
    article_ids = [relation.article_id for relation in article_relations]
    
    # 查询所有文章，排除被禁用户的文章
    articles = Article.query.filter(Article.id.in_(article_ids), Article.author.has(is_banned=False)).all()
    
    # 按添加到合集的时间排序文章
    article_dict = {article.id: article for article in articles}
    sorted_articles = [article_dict[article_id] for article_id in article_ids if article_id in article_dict]
    
    # 处理文章内容中的换行符，确保在模板中正确显示
    for article in sorted_articles:
        article.content = article.content.replace('\n', '<br>')
        
    # 将文章列表添加到collection对象上，使模板可以通过collection.articles访问
    collection.articles = sorted_articles
    
    return render_template('view_collection.html', collection=collection, articles=sorted_articles)

@app.route('/remove_from_collection/<int:collection_id>/<int:article_id>', methods=['POST'])
@login_required
def remove_from_collection(collection_id, article_id):
    """从合集中移除文章"""
    collection = Collection.query.get_or_404(collection_id)
    user = User.query.get(session['user_id'])
    
    # 检查权限：只有合集创建者或管理员可以移除文章
    if collection.user_id != user.id and not user.is_admin:
        flash('您没有权限执行此操作', 'danger')
        return redirect(url_for('view_collection', collection_id=collection_id))
    
    try:
        # 查找并删除关联记录
        article_collection = SourceArticleCollection.query.filter_by(
            article_id=article_id, 
            collection_id=collection_id
        ).first()
        
        if article_collection:
            db.session.delete(article_collection)
            db.session.commit()
            flash('文章已成功从合集中移除', 'success')
        else:
            flash('文章不在此合集中', 'warning')
    except Exception as e:
        db.session.rollback()
        flash('操作失败，请稍后重试', 'danger')
    
    return redirect(url_for('view_collection', collection_id=collection_id))

@app.route('/create_collection', methods=['GET', 'POST'])
@login_required
@user_required
def create_collection():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        is_public = request.form.get('is_public') == 'on'
        
        # 验证输入
        if not name or len(name.strip()) == 0:
            flash('合集名称不能为空', 'danger')
            return redirect(url_for('create_collection'))
            
        # 创建新合集
        new_collection = Collection(
            name=name.strip(),
            description=description.strip() if description else '',
            is_public=is_public,
            user_id=session['user_id'],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.session.add(new_collection)
        db.session.commit()
        
        flash('合集创建成功！', 'success')
        return redirect(url_for('my_collections'))
        
    return render_template('create_collection.html')

@app.route('/edit_collection/<int:collection_id>', methods=['GET', 'POST'])
@login_required
def edit_collection(collection_id):
    collection = Collection.query.get_or_404(collection_id)
    
    # 检查权限
    if collection.user_id != session['user_id'] and not session.get('is_admin'):
        flash('您没有权限编辑此合集', 'danger')
        return redirect(url_for('my_collections'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        is_public = request.form.get('is_public') == 'on'
        
        # 验证输入
        if not name or len(name.strip()) == 0:
            flash('合集名称不能为空', 'danger')
            return redirect(url_for('edit_collection', collection_id=collection_id))
            
        # 更新合集信息
        collection.name = name.strip()
        collection.description = description.strip() if description else ''
        collection.is_public = is_public
        collection.updated_at = datetime.utcnow()
        
        try:
            db.session.commit()
            flash('合集更新成功！', 'success')
            return redirect(url_for('view_collection', collection_id=collection.id))
        except Exception as e:
            db.session.rollback()
            flash('合集更新失败，请稍后重试', 'danger')
            return redirect(url_for('edit_collection', collection_id=collection_id))
    
    return render_template('edit_collection.html', collection=collection)

@app.route('/delete_collection/<int:collection_id>', methods=['POST'])
@login_required
def delete_collection(collection_id):
    collection = Collection.query.get_or_404(collection_id)
    
    # 检查权限
    if collection.user_id != session['user_id'] and not session.get('is_admin'):
        flash('您没有权限删除此合集', 'danger')
        return redirect(url_for('my_collections'))
    
    try:
        # 删除合集与文章的关联
        SourceArticleCollection.query.filter_by(collection_id=collection_id).delete()
        # 删除合集
        db.session.delete(collection)
        db.session.commit()
        flash('合集删除成功！', 'success')
    except Exception as e:
        db.session.rollback()
        flash('合集删除失败，请稍后重试', 'danger')
    
    return redirect(url_for('my_collections'))

@app.route('/my_favorites')
@login_required
def my_favorites():
    user = User.query.get(session['user_id'])
    
    # 查询用户收藏的文章
    favorites = Favorite.query.filter_by(user_id=user.id).order_by(Favorite.created_at.desc()).all()
    
    # 获取收藏的文章ID列表
    article_ids = [favorite.article_id for favorite in favorites]
    
    # 查询所有收藏的文章
    articles = Article.query.filter(Article.id.in_(article_ids), Article.author.has(is_banned=False)).all()
    
    # 按收藏时间排序文章
    article_dict = {article.id: article for article in articles}
    sorted_articles = [article_dict[article_id] for article_id in article_ids if article_id in article_dict]
    
    # 为每篇文章计算点赞数和收藏数，并检查是否已点赞，处理内容换行
    for article in sorted_articles:
        article.like_count = Like.query.filter_by(article_id=article.id).count()
        article.favorite_count = Favorite.query.filter_by(article_id=article.id).count()
        
        # 检查当前用户是否已点赞
        article.is_liked = Like.query.filter_by(user_id=user.id, article_id=article.id).first() is not None
        
        # 将文章内容中的换行符替换为<br>标签以确保正确显示
        article.content = article.content.replace('\n', '<br>')
    
    return render_template('my_favorites.html', articles=sorted_articles)

@app.route('/points_center')
@login_required
def points_center():
    user = User.query.get(session['user_id'])
    
    # 获取用户积分信息
    user_points = UserPoints.query.filter_by(user_id=user.id).first()
    if not user_points:
        # 如果用户没有积分记录，创建一个
        user_points = UserPoints(user_id=user.id, total_points=0, available_points=0)
        db.session.add(user_points)
        db.session.commit()
    
    # 获取所有可用的任务
    tasks = PointTask.query.filter_by(is_active=True).all()
    
    # 为每个任务检查用户是否可以完成
    for task in tasks:
        can_complete, message = can_complete_task(user.id, task.id)
        task.can_complete = can_complete
        task.message = message
    
    # 从数据库获取VIP兑换选项
    vip_options = VipOption.query.filter_by(is_active=True).all()
    
    return render_template('points.html', 
                           user_points=user_points, 
                           tasks=tasks, 
                           vip_options=vip_options)

def can_complete_task(user_id, task_id):
    """检查用户是否可以完成指定任务"""
    task = PointTask.query.get(task_id)
    if not task or not task.is_active:
        return False, "任务不存在或已关闭"
    
    # 检查用户是否已经完成过此任务
    existing_completion = PointTaskCompletion.query.filter_by(
        user_id=user_id, 
        task_id=task_id
    ).first()
    
    # 对于每日任务，需要检查是否在24小时内已经完成
    if task.task_type == 'daily':
        # 如果任务已经完成，检查是否超过24小时
        if existing_completion:
            # 处理SQLite丢失时区信息的问题
            # 比较时使用相同的时区处理方式
            now = datetime.now()
            if existing_completion.completed_at.tzinfo is None:
                # 如果数据库中的时间不带时区，使用相同的不带时区的时间进行比较
                time_since_completion = now - existing_completion.completed_at
            else:
                # 如果数据库中的时间带时区，确保当前时间也带时区
                time_since_completion = datetime.now(pytz.utc) - existing_completion.completed_at
            
            if time_since_completion < timedelta(hours=24):
                hours_left = 24 - time_since_completion.total_seconds() / 3600
                return False, f"请在{int(hours_left)}小时后再来完成此任务"
            return True, "可以再次完成此任务"
        return True, "可以完成此任务"
    
    # 对于一次性任务，检查是否已经完成过
    elif task.task_type == 'one_time':
        if existing_completion:
            return False, "此任务只能完成一次"
        return True, "可以完成此任务"
    
    # 其他类型的任务默认可以完成
    return True, "可以完成此任务"

@app.route('/complete_task/<int:task_id>', methods=['POST'])
@login_required
def complete_task(task_id):
    user_id = session['user_id']
    user = User.query.get(user_id)
    
    # 检查用户是否可以完成此任务
    can_complete, message = can_complete_task(user_id, task_id)
    if not can_complete:
        return jsonify({'success': False, 'message': message})
    
    task = PointTask.query.get(task_id)
    
    try:
        # 获取用户积分记录
        user_points = UserPoints.query.filter_by(user_id=user_id).first()
        if not user_points:
            user_points = UserPoints(user_id=user_id, total_points=0, available_points=0)
            db.session.add(user_points)
        
        # 更新用户积分
        user_points.total_points += task.points
        user_points.available_points += task.points
        user_points.updated_at = datetime.now(pytz.utc)
        
        # 记录任务完成情况
        # 对于每日任务，先删除之前的完成记录
        if task.task_type == 'daily':
            existing_completion = PointTaskCompletion.query.filter_by(
                user_id=user_id, 
                task_id=task_id
            ).first()
            if existing_completion:
                db.session.delete(existing_completion)
        
        # 创建新的任务完成记录
        completion = PointTaskCompletion(
            user_id=user_id,
            task_id=task_id,
            points_awarded=task.points
        )
        db.session.add(completion)
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'任务完成！获得{task.points}积分',
            'new_points': user_points.available_points
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': '操作失败，请稍后重试'})

@app.route('/redeem_vip/<int:days>', methods=['POST'])
@login_required
def redeem_vip(days):
    user_id = session['user_id']
    user = User.query.get(user_id)
    
    # 从数据库获取VIP选项信息
    vip_option = VipOption.query.filter_by(days=days, is_active=True).first()
    if not vip_option:
        return jsonify({'success': False, 'message': '无效的会员选项'})
    
    points_required = vip_option.points
    
    # 获取用户积分记录
    user_points = UserPoints.query.filter_by(user_id=user_id).first()
    if not user_points or user_points.available_points < points_required:
        return jsonify({'success': False, 'message': '积分不足'})
    
    try:
        # 扣除积分
        user_points.available_points -= points_required
        user_points.updated_at = datetime.now(pytz.utc)
        
        # 设置会员状态
        user.is_vip = True
        user.vip_level = 1  # 默认设置为普通会员
        
        # 如果用户已有会员，将会员有效期延长
        if user.vip_expires_at and user.vip_expires_at > datetime.now(pytz.utc):
            user.vip_expires_at += timedelta(days=days)
        else:
            user.vip_expires_at = datetime.now(pytz.utc) + timedelta(days=days)
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'成功兑换{days}天会员！',
            'new_points': user_points.available_points,
            'vip_expires_at': user.vip_expires_at.strftime('%Y-%m-%d %H:%M:%S')
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': '操作失败，请稍后重试'})

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('请输入用户名和密码', 'danger')
            return redirect(url_for('login'))
        
        user = User.query.filter_by(username=username).first()
        if not user or not check_password_hash(user.password, password):
            flash('用户名或密码错误', 'danger')
            return redirect(url_for('login'))
        
        if user.is_banned:
            flash('您的账户已被禁用', 'danger')
            return redirect(url_for('login'))
        
        # 登录成功，设置会话
        session['user_id'] = user.id
        session['username'] = user.username
        session['is_admin'] = user.is_admin
        # 确保VIP到期时间比较时时区一致
        now_utc = datetime.now(pytz.utc)
        if user.vip_expires_at:
            # 如果vip_expires_at没有时区信息，则添加UTC时区
            if user.vip_expires_at.tzinfo is None:
                vip_expires_at_utc = user.vip_expires_at.replace(tzinfo=pytz.utc)
            else:
                vip_expires_at_utc = user.vip_expires_at
            session['is_vip'] = user.is_vip and (vip_expires_at_utc > now_utc)
        else:
            # 如果没有设置过期时间，则VIP状态由user.is_vip决定
            session['is_vip'] = user.is_vip
        
        flash('登录成功', 'success')
        next_url = request.args.get('next')
        return redirect(next_url or url_for('index'))
    
    return render_template('login.html')

# 发送验证码路由
@app.route('/send_verification_code', methods=['POST'])
def send_verification_code():
    try:
        data = request.get_json()
        email = data.get('email')
        
        if not email:
            return jsonify({'success': False, 'message': '请输入邮箱地址'})
        
        # 不验证邮箱格式，按用户要求
        
        # 检查邮箱是否已注册
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({'success': False, 'message': '该邮箱已被注册'})
        
        # 发送验证码
        success, message = send_verification_email(email)
        return jsonify({'success': success, 'message': message})
    except Exception as e:
        app.logger.error(f"发送验证码时发生错误: {str(e)}")
        return jsonify({'success': False, 'message': '系统错误，请稍后重试'})

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        verification_code = request.form.get('verification_code')
        
        # 检查必填字段
        if not username or not email or not password or not confirm_password or not verification_code:
            flash('请填写所有必填字段', 'danger')
            return redirect(url_for('register'))
        
        # 检查密码是否一致
        if password != confirm_password:
            flash('两次输入的密码不一致', 'danger')
            return redirect(url_for('register'))
        
        # 检查用户名是否已存在
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('用户名已被注册', 'danger')
            return redirect(url_for('register'))
        
        # 检查邮箱是否已存在
        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            flash('邮箱已被注册', 'danger')
            return redirect(url_for('register'))
        
        # 验证验证码
        success, message = verify_code(email, verification_code)
        if not success:
            flash(message, 'danger')
            return redirect(url_for('register'))
        
        # 创建新用户
        hashed_password = generate_password_hash(password)
        new_user = User(
            username=username,
            email=email,
            password=hashed_password,
            created_at=datetime.now(pytz.utc)
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        # 创建用户积分记录
        user_points = UserPoints(user_id=new_user.id)
        db.session.add(user_points)
        db.session.commit()
        
        flash('注册成功，请登录', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('已成功退出登录', 'success')
    return redirect(url_for('login'))

@app.route('/article/<int:article_id>')
def view_article(article_id):
    article = Article.query.get_or_404(article_id)
    
    # 增加观看计数
    article.views += 1
    db.session.commit()
    
    # 初始化预览相关变量
    is_preview = False
    preview_content = ''
    
    # 检查用户是否有权限查看
    if article.vip_only:
        user = None
        if 'user_id' in session:
            user = User.query.get(session['user_id'])
        
        if not user or user.is_banned:
            flash('请先登录查看此文章', 'warning')
            return redirect(url_for('login', next=request.url))
        
        # 确保比较的datetime对象都有时区信息
        current_time = datetime.now(pytz.utc)
        # vip_expires_at为None表示永久会员，不需要检查过期时间
        if not user.is_vip:
            flash('此文章需要会员权限', 'warning')
            return redirect(url_for('index'))
        
        # 如果设置了过期时间，则检查是否过期
        if user.vip_expires_at:
            if (user.vip_expires_at.tzinfo is not None and user.vip_expires_at < current_time) or \
               (user.vip_expires_at.tzinfo is None and pytz.utc.localize(user.vip_expires_at) < current_time):
                flash('会员已过期，请续费', 'warning')
                return redirect(url_for('index'))
        
        if article.vip_level_required > user.vip_level:
            flash('此文章需要超级会员权限', 'warning')
            return redirect(url_for('index'))
    
    # 获取评论
    comments = Comment.query.filter_by(article_id=article_id).order_by(Comment.is_pinned.desc(), Comment.created_at.desc()).all()
    
    # 检查是否已收藏和点赞
    is_favorited = False
    is_liked = False
    if 'user_id' in session:
        is_favorited = Favorite.query.filter_by(user_id=session['user_id'], article_id=article_id).first() is not None
        is_liked = Like.query.filter_by(user_id=session['user_id'], article_id=article_id).first() is not None
    
    # 计算点赞数和收藏数
    article.like_count = Like.query.filter_by(article_id=article_id).count()
    article.favorite_count = Favorite.query.filter_by(article_id=article_id).count()
    
    # 获取关联的文章
    related_articles = []
    # 首先查找以当前文章为源的关联
    source_relations = ArticleRelation.query.filter_by(source_article_id=article_id).all()
    for relation in source_relations:
        related_article = Article.query.get(relation.target_article_id)
        if related_article and not related_article.author.is_banned:
            # 确保用户有权限查看关联文章的预览
            can_view = True
            if related_article.vip_only:
                if not session.get('user_id'):
                    can_view = True  # 即使是VIP文章，也可以显示在相关文章列表中，点击后再检查权限
            if can_view:
                related_articles.append(related_article)
    
    # 然后查找以当前文章为目标的关联
    target_relations = ArticleRelation.query.filter_by(target_article_id=article_id).all()
    for relation in target_relations:
        related_article = Article.query.get(relation.source_article_id)
        if related_article and not related_article.author.is_banned and related_article not in related_articles:
            # 确保用户有权限查看关联文章的预览
            can_view = True
            if related_article.vip_only:
                if not session.get('user_id'):
                    can_view = True  # 即使是VIP文章，也可以显示在相关文章列表中，点击后再检查权限
            if can_view:
                related_articles.append(related_article)
    
    # 去重并限制数量
    related_articles = list(dict.fromkeys(related_articles))[:5]  # 最多显示5篇关联文章
    
    # 获取文章所属的合集
    article_collections = []
    source_collections = SourceArticleCollection.query.filter_by(article_id=article.id).all()
    for source_collection in source_collections:
        collection = Collection.query.get(source_collection.collection_id)
        if collection:
            article_collections.append(collection)
    
    # 将article.content中的转换为<br>以确保在渲染时正确显示换行
    article.content = article.content.replace('\n', '<br>')
    
    return render_template('view_article.html', article=article, comments=comments, is_favorited=is_favorited, is_liked=is_liked, related_articles=related_articles, article_collections=article_collections, is_preview=is_preview, preview_content=preview_content)

@app.route('/create_article', methods=['GET', 'POST'])
@login_required
@user_required
# @vip_required - 不需要VIP也可以创建普通文章
def create_article():
    user = User.query.get(session['user_id'])
    user_collections = Collection.query.filter_by(user_id=user.id).all()
    
    # 如果是管理员，获取所有文章供选择关联
    all_articles = []
    if user.is_admin:
        all_articles = Article.query.join(Article.author).filter(User.is_banned == False).order_by(Article.created_at.desc()).all()
    
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        vip_only = request.form.get('vip_only') == 'on'
        vip_level = int(request.form.get('vip_level', 0))
        collection_id = request.form.get('collection_id')
        
        # 获取选中的关联文章ID（如果是管理员）
        related_article_ids = []
        if user.is_admin:
            related_article_ids = request.form.getlist('related_articles')
        
        # 验证表单数据
        if not title or not content:
            flash('请填写标题和内容', 'danger')
            return redirect(url_for('create_article'))
        
        # 检查VIP权限
        # 确保比较的datetime对象都有时区信息
        current_time = datetime.now(pytz.utc)
        if vip_only and not (user.is_vip and (not user.vip_expires_at or (user.vip_expires_at.tzinfo is not None and user.vip_expires_at > current_time) or (user.vip_expires_at.tzinfo is None and pytz.utc.localize(user.vip_expires_at) > current_time))):
            flash('只有会员才能发布会员专属文章', 'danger')
            return redirect(url_for('create_article'))
        
        if vip_level == 1 and not (user.is_vip and user.vip_level == 1 and (not user.vip_expires_at or (user.vip_expires_at.tzinfo is not None and user.vip_expires_at > current_time) or (user.vip_expires_at.tzinfo is None and pytz.utc.localize(user.vip_expires_at) > current_time))):
            flash('只有超级会员才能发布超级会员专属文章', 'danger')
            return redirect(url_for('create_article'))
        
        # 创建新文章 - 发布时间增加8小时
        from datetime import timedelta
        publish_time = datetime.now(pytz.utc) + timedelta(hours=8)
        new_article = Article(
            title=title,
            content=content,
            user_id=user.id,
            vip_only=vip_only,
            vip_level_required=vip_level,
            created_at=publish_time,
            is_approved=False  # 默认为未审核状态
        )
        
        try:
            db.session.add(new_article)
            db.session.commit()
            
            # 添加到合集
            if collection_id and collection_id.isdigit():
                collection = Collection.query.get(int(collection_id))
                if collection and collection.user_id == user.id:
                    article_collection = SourceArticleCollection(article_id=new_article.id, collection_id=collection.id)
                    db.session.add(article_collection)
            
            # 添加关联文章（如果是管理员）
            if user.is_admin and related_article_ids:
                for article_id in related_article_ids:
                    if article_id.isdigit():
                        target_article = Article.query.get(int(article_id))
                        if target_article and target_article.id != new_article.id:  # 不能关联自己
                            # 检查关联是否已存在
                            existing_relation = ArticleRelation.query.filter_by(
                                source_article_id=new_article.id,
                                target_article_id=target_article.id
                            ).first()
                            if not existing_relation:
                                article_relation = ArticleRelation(
                                    source_article_id=new_article.id,
                                    target_article_id=target_article.id
                                )
                                db.session.add(article_relation)
            
            db.session.commit()
            flash('文章创建成功，等待管理员审核通过后将在社区显示', 'success')
            return redirect(url_for('view_article', article_id=new_article.id))
        except Exception as e:
            db.session.rollback()
            flash('文章创建失败，请稍后重试', 'danger')
            return redirect(url_for('create_article'))
    
    return render_template('create_article.html', user_collections=user_collections, all_articles=all_articles, is_admin=user.is_admin)

@app.route('/edit_article/<int:article_id>', methods=['GET', 'POST'])
@login_required
def edit_article(article_id):
    article = Article.query.get_or_404(article_id)
    user = User.query.get(session['user_id'])
    
    # 检查权限
    if article.user_id != user.id and not user.is_admin:
        flash('您没有权限编辑此文章', 'danger')
        return redirect(url_for('view_article', article_id=article_id))
    
    user_collections = Collection.query.filter_by(user_id=user.id).all()
    
    # 获取文章当前所在的合集
    current_collection = SourceArticleCollection.query.filter_by(article_id=article_id).first()
    current_collection_id = current_collection.collection_id if current_collection else None
    
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        vip_only = request.form.get('vip_only') == 'on'
        vip_level = int(request.form.get('vip_level', 0))
        collection_id = request.form.get('collection_id')
        
        # 验证表单数据
        if not title or not content:
            flash('请填写标题和内容', 'danger')
            return redirect(url_for('edit_article', article_id=article_id))
        
        # 检查VIP权限
        # 确保比较的datetime对象都有时区信息
        current_time = datetime.now(pytz.utc)
        if vip_only and not (user.is_vip and (not user.vip_expires_at or (user.vip_expires_at.tzinfo is not None and user.vip_expires_at > current_time) or (user.vip_expires_at.tzinfo is None and pytz.utc.localize(user.vip_expires_at) > current_time))) and not user.is_admin:
            flash('只有会员才能发布会员专属文章', 'danger')
            return redirect(url_for('edit_article', article_id=article_id))
        
        if vip_level == 1 and not (user.is_vip and user.vip_level == 1 and (not user.vip_expires_at or (user.vip_expires_at.tzinfo is not None and user.vip_expires_at > current_time) or (user.vip_expires_at.tzinfo is None and pytz.utc.localize(user.vip_expires_at) > current_time))) and not user.is_admin:
            flash('只有超级会员才能发布超级会员专属文章', 'danger')
            return redirect(url_for('edit_article', article_id=article_id))
        
        # 更新文章
        article.title = title
        article.content = content
        article.vip_only = vip_only
        article.vip_level_required = vip_level
        
        try:
            db.session.commit()
            
            # 处理合集关系
            if collection_id and collection_id.isdigit():
                # 先删除现有关系
                if current_collection:
                    db.session.delete(current_collection)
                    db.session.commit()
                
                # 添加新关系
                collection = Collection.query.get(int(collection_id))
                if collection and collection.user_id == user.id:
                    article_collection = SourceArticleCollection(article_id=article.id, collection_id=collection.id)
                    db.session.add(article_collection)
                    db.session.commit()
            elif current_collection:
                # 如果选择了不添加到任何合集，且之前有合集关系，则删除
                db.session.delete(current_collection)
                db.session.commit()
            
            flash('文章更新成功', 'success')
            return redirect(url_for('view_article', article_id=article.id))
        except Exception as e:
            db.session.rollback()
            flash('文章更新失败，请稍后重试', 'danger')
            return redirect(url_for('edit_article', article_id=article_id))
    
    return render_template('edit_article.html', article=article, user_collections=user_collections, current_collection_id=current_collection_id)

@app.route('/delete_article/<int:article_id>', methods=['POST'])
@login_required
@user_required
def delete_article(article_id):
    # 获取要删除的文章
    article = Article.query.get_or_404(article_id)
    
    # 获取当前登录用户
    user = User.query.get(session['user_id'])
    
    # 检查用户是否有权限删除这篇文章
    if article.user_id != user.id and not user.is_admin:
        flash('您没有权限删除这篇文章', 'danger')
        return redirect(url_for('view_article', article_id=article_id))
    
    try:
        db.session.delete(article)
        db.session.commit()
        flash('文章删除成功', 'success')
        return redirect(url_for('my_articles'))
    except Exception as e:
        db.session.rollback()
        flash('文章删除失败，请稍后重试', 'danger')
        return redirect(url_for('view_article', article_id=article_id))

@app.route('/my_articles')
@login_required
def my_articles():
    user = User.query.get(session['user_id'])
    articles = Article.query.filter_by(user_id=user.id).order_by(Article.created_at.desc()).all()
    
    # 获取每篇文章的点赞数和收藏数，并处理内容换行
    for article in articles:
        article.like_count = Like.query.filter_by(article_id=article.id).count()
        article.favorite_count = Favorite.query.filter_by(article_id=article.id).count()
        # 将文章内容中的换行符替换为<br>标签以确保正确显示
        article.content = article.content.replace('\n', '<br>')
        
    return render_template('my_articles.html', articles=articles)

@app.route('/user/<username>')
def user_profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    
    # 不显示被禁用户的文章
    articles = Article.query.filter_by(user_id=user.id).join(User, Article.user_id == User.id).filter(User.is_banned == False).order_by(Article.created_at.desc()).all()
    
    # 获取收藏和点赞数量
    favorite_count = Favorite.query.filter_by(user_id=user.id).count()
    like_count = Like.query.filter_by(user_id=user.id).count()
    
    # 处理文章内容中的换行符，确保在模板中正确显示
    for article in articles:
        article.content = article.content.replace('\n', '<br>')
        
    return render_template('user_profile.html', user=user, articles=articles, favorite_count=favorite_count, like_count=like_count)

@app.route('/user/settings', methods=['GET', 'POST'])
@login_required
def user_settings():
    """用户个人设置页面"""
    user = User.query.get(session['user_id'])
    
    # 创建vip_info对象
    now_utc = datetime.now(pytz.utc)
    if user.vip_expires_at:
        # 确保vip_expires_at有时区信息
        if user.vip_expires_at.tzinfo is None or user.vip_expires_at.tzinfo.utcoffset(user.vip_expires_at) is None:
            vip_expires_at_utc = user.vip_expires_at.replace(tzinfo=pytz.utc)
        else:
            vip_expires_at_utc = user.vip_expires_at.astimezone(pytz.utc)
        is_vip_valid = user.is_vip and (vip_expires_at_utc > now_utc)
    else:
        is_vip_valid = user.is_vip
    
    # 获取会员类型
    if is_vip_valid:
        if user.vip_level == 1:
            vip_type = '超级会员'
        else:
            vip_type = '会员'
    elif user.is_vip:
        vip_type = '会员已过期'
    else:
        vip_type = '非会员'
    
    vip_info = {
        'is_vip': is_vip_valid,
        'vip_type': vip_type,
        'expires_at': user.vip_expires_at
    }
    
    if request.method == 'POST':
        # 处理表单提交
        if 'email' in request.form:
            # 更新基本信息
            user.email = request.form['email']
            try:
                db.session.commit()
                flash('个人信息已更新', 'success')
            except Exception as e:
                db.session.rollback()
                flash('更新失败，请稍后重试', 'danger')
        elif 'current_password' in request.form:
            # 修改密码
            current_password = request.form['current_password']
            new_password = request.form['new_password']
            confirm_password = request.form['confirm_password']
            
            # 验证当前密码
            if not check_password_hash(user.password, current_password):
                flash('当前密码错误', 'danger')
                return redirect(url_for('user_settings'))
            
            # 验证新密码
            if len(new_password) < 6:
                flash('密码长度至少为6个字符', 'danger')
                return redirect(url_for('user_settings'))
            
            # 验证两次输入的密码是否一致
            if new_password != confirm_password:
                flash('两次输入的密码不一致', 'danger')
                return redirect(url_for('user_settings'))
            
            # 更新密码
            user.password = generate_password_hash(new_password)
            try:
                db.session.commit()
                flash('密码已更新', 'success')
            except Exception as e:
                db.session.rollback()
                flash('更新失败，请稍后重试', 'danger')
        
        return redirect(url_for('user_settings'))
    
    return render_template('settings.html', user=user, vip_info=vip_info)

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    users = User.query.order_by(User.created_at.desc()).all()
    articles = Article.query.order_by(Article.created_at.desc()).all()
    announcements = Announcement.query.order_by(Announcement.created_at.desc()).all()
    # 获取待审核的文章
    pending_articles = Article.query.filter_by(is_approved=False).order_by(Article.created_at.desc()).all()
    return render_template('admin/dashboard.html', users=users, articles=articles, announcements=announcements, pending_articles=pending_articles)

@app.route('/admin/point_tasks')
@admin_required
def admin_point_tasks():
    tasks = PointTask.query.order_by(PointTask.created_at.desc()).all()
    return render_template('admin/point_tasks.html', tasks=tasks)

@app.route('/admin/edit_points/<int:user_id>')
@admin_required
def admin_edit_points(user_id):
    """显示修改用户积分的表单"""
    user = User.query.get_or_404(user_id)
    
    # 获取用户积分信息
    user_points = UserPoints.query.filter_by(user_id=user.id).first()
    if not user_points:
        # 如果用户没有积分记录，创建一个
        user_points = UserPoints(user_id=user.id, total_points=0, available_points=0)
        db.session.add(user_points)
        db.session.commit()
        
    return render_template('admin/edit_points.html', user=user, user_points=user_points)

@app.route('/admin/update_points/<int:user_id>', methods=['POST'])
@admin_required
def admin_update_points(user_id):
    """处理修改用户积分的表单提交"""
    user = User.query.get_or_404(user_id)
    
    # 获取表单数据
    try:
        points_change = int(request.form.get('points_change', 0))
        reason = request.form.get('reason', '管理员修改积分')
        
        # 执行积分修改
        success, message = modify_user_points(user.id, points_change, reason)
        
        if success:
            flash(f'用户 {user.username} 的积分已成功修改', 'success')
        else:
            flash(f'修改积分失败: {message}', 'danger')
            
    except ValueError:
        flash('积分变动必须是有效的数字', 'danger')
    except Exception as e:
        flash(f'操作失败，请稍后重试: {str(e)}', 'danger')
        
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/edit_point_task/<int:task_id>', methods=['GET', 'POST'])
@admin_required
def edit_point_task(task_id):
    # 如果task_id为0，表示创建新任务
    if task_id == 0:
        task = None
    else:
        task = PointTask.query.get_or_404(task_id)
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        points = int(request.form.get('points'))
        max_completions = int(request.form.get('max_completions'))
        cooldown_hours = int(request.form.get('cooldown_hours'))
        task_type = request.form.get('task_type', 'daily')  # 默认值为'daily'
        is_active = request.form.get('is_active') == 'true'
        
        # 验证输入
        if not name or len(name.strip()) == 0:
            flash('任务名称不能为空', 'danger')
            return redirect(url_for('edit_point_task', task_id=task_id))
        
        if points <= 0:
            flash('积分奖励必须大于0', 'danger')
            return redirect(url_for('edit_point_task', task_id=task_id))
        
        if cooldown_hours < 0:
            flash('冷却时间不能为负数', 'danger')
            return redirect(url_for('edit_point_task', task_id=task_id))
        
        if task_type not in ['daily', 'one_time']:
            flash('无效的任务类型', 'danger')
            return redirect(url_for('edit_point_task', task_id=task_id))
        
        # 创建或更新任务
        try:
            if not task:
                new_task = PointTask(
                    name=name.strip(),
                    description=description.strip() if description else '',
                    points=points,
                    task_type=task_type,
                    max_completions=max_completions,
                    cooldown_hours=cooldown_hours,
                    is_active=is_active,
                    created_at=datetime.now(pytz.utc),
                    updated_at=datetime.now(pytz.utc)
                )
                db.session.add(new_task)
                flash('任务创建成功！', 'success')
            else:
                task.name = name.strip()
                task.description = description.strip() if description else ''
                task.points = points
                task.task_type = task_type
                task.max_completions = max_completions
                task.cooldown_hours = cooldown_hours
                task.is_active = is_active
                task.updated_at = datetime.now(pytz.utc)
                flash('任务更新成功！', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'创建任务失败：{str(e)}', 'danger')
            return redirect(url_for('edit_point_task', task_id=task_id))
        
        db.session.commit()
        return redirect(url_for('admin_point_tasks'))
    
    return render_template('admin/edit_point_task.html', task=task)

@app.route('/admin/create_point_task', methods=['GET', 'POST'])
@admin_required
def create_point_task():
    # 重定向到编辑任务路由，传入task_id=0表示创建新任务
    return redirect(url_for('edit_point_task', task_id=0))

# 评论相关路由
@app.route('/article/<int:article_id>/comment', methods=['POST'])
@login_required
@user_required
def add_comment(article_id):
    article = Article.query.get_or_404(article_id)
    user = User.query.get(session['user_id'])
    
    content = request.form.get('content')
    if not content or len(content.strip()) == 0:
        flash('评论内容不能为空', 'danger')
        return redirect(url_for('view_article', article_id=article_id))
    
    new_comment = Comment(content=content, user_id=user.id, article_id=article_id)
    
    try:
        db.session.add(new_comment)
        db.session.commit()
        flash('评论发表成功', 'success')
    except Exception as e:
        db.session.rollback()
        flash('评论发表失败，请稍后重试', 'danger')
    
    return redirect(url_for('view_article', article_id=article_id))

@app.route('/comment/<int:comment_id>/delete', methods=['POST'])
@login_required
@user_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    user = User.query.get(session['user_id'])
    
    # 检查权限
    if comment.user_id != user.id and not user.is_admin and comment.article.user_id != user.id:
        flash('您没有权限删除此评论', 'danger')
        return redirect(url_for('view_article', article_id=comment.article_id))
    
    try:
        db.session.delete(comment)
        db.session.commit()
        flash('评论删除成功', 'success')
    except Exception as e:
        db.session.rollback()
        flash('评论删除失败，请稍后重试', 'danger')
    
    return redirect(url_for('view_article', article_id=comment.article_id))

@app.route('/comment/<int:comment_id>/pin', methods=['POST'])
@login_required
@user_required
def pin_comment(comment_id):
    """置顶或取消置顶评论"""
    comment = Comment.query.get_or_404(comment_id)
    user = User.query.get(session['user_id'])
    
    # 检查权限：只有文章作者或管理员可以置顶/取消置顶评论
    if comment.article.user_id != user.id and not user.is_admin:
        flash('您没有权限置顶/取消置顶此评论', 'danger')
        return redirect(url_for('view_article', article_id=comment.article_id))
    
    try:
        # 切换置顶状态
        comment.is_pinned = not comment.is_pinned
        db.session.commit()
        
        if comment.is_pinned:
            flash('评论已置顶', 'success')
        else:
            flash('已取消置顶评论', 'success')
    except Exception as e:
        db.session.rollback()
        flash('操作失败，请稍后重试', 'danger')
    
    return redirect(url_for('view_article', article_id=comment.article_id))

# 收藏和点赞相关路由
@app.route('/article/<int:article_id>/favorite', methods=['POST'])
@login_required
@user_required
def toggle_favorite(article_id):
    article = Article.query.get_or_404(article_id)
    user = User.query.get(session['user_id'])
    
    favorite = Favorite.query.filter_by(user_id=user.id, article_id=article_id).first()
    
    try:
        if favorite:
            db.session.delete(favorite)
            db.session.commit()
            flash('已取消收藏', 'success')
        else:
            new_favorite = Favorite(user_id=user.id, article_id=article_id)
            db.session.add(new_favorite)
            db.session.commit()
            flash('收藏成功', 'success')
    except Exception as e:
        db.session.rollback()
        flash('操作失败，请稍后重试', 'danger')
    
    return redirect(url_for('view_article', article_id=article_id))

@app.route('/article/<int:article_id>/like', methods=['POST'])
@login_required
@user_required
def toggle_like(article_id):
    article = Article.query.get_or_404(article_id)
    user = User.query.get(session['user_id'])
    
    like = Like.query.filter_by(user_id=user.id, article_id=article_id).first()
    
    try:
        if like:
            db.session.delete(like)
            db.session.commit()
            flash('已取消点赞', 'success')
        else:
            new_like = Like(user_id=user.id, article_id=article_id)
            db.session.add(new_like)
            db.session.commit()
            flash('点赞成功', 'success')
    except Exception as e:
        db.session.rollback()
        flash('操作失败，请稍后重试', 'danger')
    
    return redirect(url_for('view_article', article_id=article_id))

# 管理员用户管理路由
@app.route('/admin/user/<int:user_id>/ban', methods=['POST'])
@admin_required
def admin_ban_user(user_id):
    user = User.query.get_or_404(user_id)
    
    # 不能封禁管理员
    if user.is_admin:
        flash('不能封禁管理员', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    user.is_banned = True
    
    try:
        db.session.commit()
        flash(f'用户 {user.username} 已被封禁', 'success')
    except Exception as e:
        db.session.rollback()
        flash('操作失败，请稍后重试', 'danger')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/user/<int:user_id>/unban', methods=['POST'])
@admin_required
def admin_unban_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_banned = False
    
    try:
        db.session.commit()
        flash(f'用户 {user.username} 已被解封', 'success')
    except Exception as e:
        db.session.rollback()
        flash('操作失败，请稍后重试', 'danger')
    
    return redirect(url_for('admin_dashboard'))

# 文章审核相关路由
@app.route('/admin/article/<int:article_id>/approve', methods=['POST'])
@admin_required
def admin_approve_article(article_id):
    article = Article.query.get_or_404(article_id)
    user = User.query.get(session['user_id'])
    
    try:
        article.is_approved = True
        article.reviewed_at = datetime.now(pytz.utc)
        article.reviewed_by = user.id
        article.reject_reason = None
        
        db.session.commit()
        flash(f'文章 "{article.title}" 已审核通过', 'success')
    except Exception as e:
        db.session.rollback()
        flash('审核失败，请稍后重试', 'danger')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/article/<int:article_id>/reject', methods=['POST'])
@admin_required
def admin_reject_article(article_id):
    article = Article.query.get_or_404(article_id)
    user = User.query.get(session['user_id'])
    reject_reason = request.form.get('reject_reason')
    
    if not reject_reason or reject_reason.strip() == '':
        flash('请输入拒绝原因', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    try:
        article.is_approved = False
        article.reject_reason = reject_reason
        article.reviewed_at = datetime.now(pytz.utc)
        article.reviewed_by = user.id
        
        db.session.commit()
        flash(f'文章 "{article.title}" 已拒绝', 'success')
    except Exception as e:
        db.session.rollback()
        flash('操作失败，请稍后重试', 'danger')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/pending_articles')
@admin_required
def admin_pending_articles():
    # 获取所有待审核的文章（is_approved为False或null）
    pending_articles = Article.query.filter((Article.is_approved == False) | (Article.is_approved == None)).order_by(Article.created_at.desc()).all()
    return render_template('admin/pending_articles.html', articles=pending_articles)

@app.route('/admin/user/<int:user_id>/set_vip', methods=['POST'])
@admin_required
def admin_set_vip(user_id):
    user = User.query.get_or_404(user_id)
    vip_level = int(request.form.get('vip_level', 0))
    
    user.is_vip = True
    user.vip_level = vip_level
    # 设置会员有效期为30天
    user.vip_expires_at = datetime.now(pytz.utc) + timedelta(days=30)
    
    try:
        db.session.commit()
        vip_type = '超级会员' if vip_level == 1 else '会员'
        flash(f'用户 {user.username} 已设置为{vip_type}', 'success')
    except Exception as e:
        db.session.rollback()
        flash('操作失败，请稍后重试', 'danger')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/user/<int:user_id>/remove_vip', methods=['POST'])
@admin_required
def admin_remove_vip(user_id):
    user = User.query.get_or_404(user_id)
    
    user.is_vip = False
    user.vip_level = 0
    user.vip_expires_at = None
    
    try:
        db.session.commit()
        flash(f'已取消用户 {user.username} 的会员资格', 'success')
    except Exception as e:
        db.session.rollback()
        flash('操作失败，请稍后重试', 'danger')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
@admin_required
def admin_delete_user(user_id):
    user = User.query.get_or_404(user_id)
    
    # 不能删除管理员
    if user.is_admin:
        flash('不能删除管理员账户', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    try:
        # 删除用户，根据模型定义的级联关系，会自动删除关联的文章、评论等
        db.session.delete(user)
        db.session.commit()
        flash(f'用户 {{user.username}} 已成功删除', 'success')
    except Exception as e:
        db.session.rollback()
        flash('用户删除失败，请稍后重试', 'danger')
    
    return redirect(url_for('admin_dashboard'))

# 公告管理路由
@app.route('/admin/create_announcement', methods=['GET', 'POST'])
@admin_required
def admin_create_announcement():
    # 获取所有未封禁用户的文章
    all_articles = Article.query.join(User, Article.user_id == User.id).filter(User.is_banned == False).order_by(Article.created_at.desc()).all()
    
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        
        # 获取选中的关联文章ID
        related_article_ids = request.form.getlist('related_articles')
        
        if not title or not content:
            flash('请填写标题和内容', 'danger')
            return redirect(url_for('admin_create_announcement'))
        
        new_announcement = Announcement(
            title=title,
            content=content,
            created_by=session['user_id']
        )
        
        try:
            db.session.add(new_announcement)
            db.session.commit()
            
            # 创建公告与文章的关联
            if related_article_ids:
                for article_id in related_article_ids:
                    if article_id.isdigit():
                        # 检查关联是否已存在
                        existing_relation = AnnouncementArticleRelation.query.filter_by(
                            announcement_id=new_announcement.id,
                            article_id=int(article_id)
                        ).first()
                        
                        if not existing_relation:
                            new_relation = AnnouncementArticleRelation(
                                announcement_id=new_announcement.id,
                                article_id=int(article_id)
                            )
                            db.session.add(new_relation)
                            db.session.commit()
            
            flash('公告创建成功', 'success')
            return redirect(url_for('admin_dashboard'))
        except Exception as e:
            db.session.rollback()
            flash('公告创建失败，请稍后重试', 'danger')
            return redirect(url_for('admin_create_announcement'))
    
    return render_template('admin/create_announcement.html', all_articles=all_articles)

@app.route('/admin/delete_announcement/<int:announcement_id>', methods=['POST'])
@admin_required
def delete_announcement(announcement_id):
    """删除公告"""
    announcement = Announcement.query.get_or_404(announcement_id)
    
    try:
        db.session.delete(announcement)
        db.session.commit()
        flash(f'公告 "{announcement.title}" 已成功删除', 'success')
    except Exception as e:
        db.session.rollback()
        flash('公告删除失败，请稍后重试', 'danger')
    
    return redirect(url_for('admin_dashboard'))

# 版本更新管理路由
@app.route('/admin/delete_version/<int:version_id>', methods=['POST'])
@admin_required
def admin_delete_version(version_id):
    version = VersionUpdate.query.get_or_404(version_id)
    
    try:
        db.session.delete(version)
        db.session.commit()
        flash(f'版本 "{version.version}" 已成功删除', 'success')
    except Exception as e:
        db.session.rollback()
        flash('版本删除失败，请稍后重试', 'danger')
    
    return redirect(url_for('admin_versions'))

@app.route('/admin/create_version', methods=['GET', 'POST'])
@admin_required
def admin_create_version():
    if request.method == 'POST':
        version = request.form.get('version')
        content = request.form.get('content')
        
        if not version or not content:
            flash('请填写版本号和更新内容', 'danger')
            return redirect(url_for('admin_create_version'))
        
        # 停用所有旧版本
        VersionUpdate.query.update({'is_active': False})
        
        new_version = VersionUpdate(
            version=version,
            content=content,
            created_by=session['user_id'],
            is_active=True
        )
        
        try:
            db.session.add(new_version)
            db.session.commit()
            flash('版本更新记录创建成功', 'success')
            return redirect(url_for('admin_versions'))
        except Exception as e:
            db.session.rollback()
            flash('操作失败，请稍后重试', 'danger')
            return redirect(url_for('admin_create_version'))
    
    return render_template('admin/create_version.html')

@app.route('/admin/versions')
@admin_required
def admin_versions():
    versions = VersionUpdate.query.order_by(VersionUpdate.created_at.desc()).all()
    return render_template('admin/versions.html', versions=versions)

# VIP兑换选项管理路由
@app.route('/admin/vip_options')
@admin_required
def admin_vip_options():
    options = VipOption.query.order_by(VipOption.id.asc()).all()
    return render_template('admin/vip_options.html', options=options)

@app.route('/admin/edit_vip_option/<int:option_id>', methods=['GET', 'POST'])
@admin_required
def edit_vip_option(option_id):
    # 如果option_id为0，表示创建新选项
    if option_id == 0:
        option = None
    else:
        option = VipOption.query.get_or_404(option_id)
    
    if request.method == 'POST':
        name = request.form.get('name')
        days = int(request.form.get('days', 0))
        points = int(request.form.get('points', 0))
        description = request.form.get('description')
        is_active = request.form.get('is_active') == 'on'
        
        # 验证输入
        if not name or days <= 0 or points <= 0:
            flash('请填写所有必填字段，天数和积分必须为正整数', 'danger')
            return redirect(url_for('edit_vip_option', option_id=option_id))
        
        try:
            if not option:
                # 创建新选项
                option = VipOption(
                    name=name,
                    days=days,
                    points=points,
                    description=description,
                    is_active=is_active
                )
                db.session.add(option)
                flash('VIP兑换选项创建成功', 'success')
            else:
                # 更新现有选项
                option.name = name
                option.days = days
                option.points = points
                option.description = description
                option.is_active = is_active
                option.updated_at = datetime.now(pytz.utc)
                flash('VIP兑换选项更新成功', 'success')
            
            db.session.commit()
            return redirect(url_for('admin_vip_options'))
        except Exception as e:
            db.session.rollback()
            flash('操作失败，请稍后重试', 'danger')
            return redirect(url_for('edit_vip_option', option_id=option_id))
    
    return render_template('admin/edit_vip_option.html', option=option)

@app.route('/admin/delete_vip_option/<int:option_id>')
@admin_required
def delete_vip_option(option_id):
    """删除VIP兑换选项"""
    option = VipOption.query.get_or_404(option_id)
    
    try:
        db.session.delete(option)
        db.session.commit()
        flash('VIP兑换选项删除成功', 'success')
    except Exception as e:
        db.session.rollback()
        flash('删除失败，请稍后重试', 'danger')
    
    return redirect(url_for('admin_vip_options'))

# 版本推送路由
@app.route('/admin/push-version/<int:version_id>', methods=['POST'])
@admin_required
def admin_push_version(version_id):
    """处理版本推送功能"""
    version = VersionUpdate.query.get_or_404(version_id)
    push_type = request.form.get('push_type', 'all')
    
    try:
        # 根据推送类型处理
        if push_type == 'all':
            # 推送给所有用户
            users = User.query.all()
            
        elif push_type == 'vip':
            # 仅推送给VIP用户
            users = User.query.filter(
                User.is_vip == True,
                (User.vip_expires_at == None) | (User.vip_expires_at > datetime.now(pytz.utc))
            ).all()
            
        elif push_type == 'selected':
            # 推送给选定的用户
            user_ids = request.form.getlist('user_ids[]')
            if not user_ids:
                flash('请至少选择一个用户', 'danger')
                return redirect(url_for('admin_versions'))
            
            users = User.query.filter(User.id.in_(user_ids)).all()
            
        else:
            flash('无效的推送类型', 'danger')
            return redirect(url_for('admin_versions'))
        
        # 创建推送记录（这里只是模拟，实际应该创建推送记录到数据库）
        user_count = len(users)
        
        # 在实际应用中，这里应该将推送记录保存到数据库
        # 并可能触发推送通知系统
        
        flash(f'成功推送给 {user_count} 个用户', 'success')
        return redirect(url_for('admin_versions'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'推送失败: {str(e)}', 'danger')
        return redirect(url_for('admin_versions'))

# 错误处理
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

# API路由
@app.route('/api/articles', methods=['GET'])
def api_articles():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search_query = request.args.get('search', '', type=str)
    
    # 基础查询
    query = Article.query.join(User, Article.user_id == User.id).filter(User.is_banned == False)
    
    # 如果有搜索参数，添加模糊搜索条件
    if search_query:
        search_pattern = f'%{search_query}%'
        query = query.filter(
            db.or_(
                Article.title.like(search_pattern),
                Article.content.like(search_pattern)
            )
        )
    
    pagination = query.order_by(Article.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    articles = pagination.items
    
    result = {
        'articles': [{
            'id': article.id,
            'title': article.title,
            'author': article.author.username,
            'created_at': article.created_at.isoformat(),
            'vip_only': article.vip_only,
            'vip_level_required': article.vip_level_required,
            'comments_count': len(article.comments),
            'likes_count': len(article.likes)
        } for article in articles],
        'total': pagination.total,
        'pages': pagination.pages,
        'page': pagination.page
    }
    
    return jsonify(result)

@app.route('/api/get-user-version', methods=['GET'])
def api_get_user_version():
    """获取用户已确认的最新版本"""
    # 如果用户未登录，返回默认版本
    if 'user_id' not in session:
        return jsonify({'version': '1.0'})
    
    try:
        user_id = session['user_id']
        # 获取用户已确认的最新版本
        user_confirm = (UserVersionConfirm.query
                      .filter_by(user_id=user_id)
                      .order_by(UserVersionConfirm.confirmed_at.desc())
                      .first())
        
        if user_confirm:
            return jsonify({'version': user_confirm.version})
        else:
            # 如果用户没有确认过任何版本，返回默认版本
            return jsonify({'version': '1.0'})
    except Exception as e:
        app.logger.error(f"获取用户版本时出错: {str(e)}")
        return jsonify({'version': '1.0'})

@app.route('/api/latest-version', methods=['GET'])
def api_latest_version():
    """获取最新的版本更新信息"""
    try:
        # 获取最新的活动版本
        latest_version = VersionUpdate.query.filter_by(is_active=True).order_by(VersionUpdate.release_date.desc()).first()
        
        if latest_version:
            return jsonify({
                'version': latest_version.version,
                'content': latest_version.content,
                'release_date': latest_version.release_date.isoformat()
            })
        else:
            # 如果没有版本记录，返回默认版本
            return jsonify({'version': '1.0', 'content': '暂无版本更新信息'})
    except Exception as e:
        app.logger.error(f"获取最新版本时出错: {str(e)}")
        return jsonify({'version': '1.0', 'content': '获取版本信息失败'})

@app.route('/api/confirm-version/<version>', methods=['POST'])
def api_confirm_version(version):
    """标记版本为已阅读"""
    # 检查用户是否登录
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '请先登录'})
    
    try:
        user_id = session['user_id']
        
        # 检查版本是否存在
        version_record = VersionUpdate.query.filter_by(version=version).first()
        if not version_record:
            # 如果版本记录不存在，也允许用户确认（用于默认版本）
            pass
        
        # 检查用户是否已经确认过这个版本
        existing_confirm = UserVersionConfirm.query.filter_by(
            user_id=user_id, version=version).first()
        
        if existing_confirm:
            # 如果已经确认过，更新确认时间
            existing_confirm.confirmed_at = datetime.now(pytz.utc)
        else:
            # 创建新的确认记录
            new_confirm = UserVersionConfirm(
                user_id=user_id,
                version=version
            )
            db.session.add(new_confirm)
        
        db.session.commit()
        return jsonify({'success': True, 'message': '版本确认成功'})
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"确认版本时出错: {str(e)}")
        return jsonify({'success': False, 'message': '确认版本失败，请稍后重试'})

@app.route('/api/article/<int:article_id>', methods=['GET'])

def api_article(article_id):
    article = Article.query.get_or_404(article_id)
    
    result = {
        'id': article.id,
        'title': article.title,
        'content': article.content,
        'author': article.author.username,
        'created_at': article.created_at.isoformat(),
        'updated_at': article.updated_at.isoformat(),
        'vip_only': article.vip_only,
        'vip_level_required': article.vip_level_required,
        'comments_count': len(article.comments),
        'likes_count': len(article.likes),
        'favorites_count': len(article.favorites)
    }
    
    return jsonify(result)

# 确保数据库表存在（注意：这里不创建新表，只确保现有表可访问）
with app.app_context():
    # 不使用db.create_all()来避免创建新表，只初始化现有表
    pass

# 添加UTC时间过滤器测试路由
def test_utc_filter_route():
    from datetime import datetime
    import pytz
    test_time = datetime.now(pytz.utc)
    from flask import render_template_string
    return render_template_string(
        "<h1>UTC时间过滤器测试</h1>"
        "<p>原始UTC时间: {{ test_time }}</p>"
        "<p>转换后时间: {{ utc_to_beijing(test_time).strftime('%Y-%m-%d %H:%M:%S') }}</p>",
        test_time=test_time
    )

# 注册测试路由
app.add_url_rule('/test_utc_filter', 'test_utc_filter', test_utc_filter_route)

# 生产环境错误处理
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    # 记录错误信息到日志
    app.logger.error(f"服务器内部错误: {str(e)}")
    return render_template('500.html'), 500

# 应用启动配置 - 生产环境优化
if __name__ == '__main__':
    # 生产环境建议使用Gunicorn等WSGI服务器
    # 以下配置仅用于测试，生产环境应通过WSGI服务器启动
    app.run(
        debug=False,  # 生产环境关闭debug模式
        host='0.0.0.0', 
        port=5000,
        threaded=True,  # 启用多线程
        processes=1  # 进程数，根据虚拟主机资源调整
    )

# WSGI入口点 - 用于生产环境WSGI服务器
def application(environ, start_response):
    """WSGI应用入口点，用于uWSGI、Gunicorn等服务器"""
    return app(environ, start_response)