#!/usr/bin/env python3
"""
管理工具 - 图形界面版
整合删除文章和删除用户功能的综合管理工具
"""

import sys
import os
import tkinter as tk
import logging
from tkinter import ttk, messagebox, simpledialog
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pytz

# 配置日志
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    filename='admin_tool.log',
                    filemode='w')
logger = logging.getLogger(__name__)

# 添加控制台日志
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console.setFormatter(formatter)
logger.addHandler(console)

print("管理工具启动中...")

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
print(f"项目根目录已添加到路径: {os.path.dirname(os.path.abspath(__file__))}")

class AdminToolApp:
    def __init__(self, root):
        # 主窗口设置
        print("初始化主窗口...")
        self.root = root
        self.root.title("管理工具")
        self.root.geometry("900x600")
        self.root.resizable(True, True)
        
        print("配置字体支持...")
        # 设置中文字体支持
        self.style = ttk.Style()
        self.style.configure('.', font=('SimHei', 10))
        self.style.configure('Treeview', font=('SimHei', 9))
        self.style.configure('Treeview.Heading', font=('SimHei', 10, 'bold'))
        
        # 设置主题色
        self.root.configure(bg='#f0f0f0')
        
        print("创建状态栏...")
        # 创建状态栏（先创建状态栏以避免属性不存在的错误）
        self.create_status_bar()
        
        print("初始化数据库连接...")
        # 初始化Flask应用和数据库
        self.init_database()
        
        print("创建标签页控件...")
        # 创建标签页控件
        self.create_notebook()
        
        print("管理工具初始化完成")
        # 显示状态栏信息
        self.update_status("就绪")
    
    def init_database(self):
        """初始化数据库连接"""
        try:
            print("创建Flask应用实例...")
            # 创建Flask应用实例
            self.app = Flask(__name__)
            
            print("配置数据库连接...")
            # 配置数据库 - 使用绝对路径确保能正确打开数据库文件
            db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'app.db')
            print(f"数据库路径: {db_path}")
            self.app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
            self.app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
            
            print("初始化数据库...")
            # 初始化数据库
            self.db = SQLAlchemy(self.app)
            
            print("定义数据库模型...")
            # 定义必要的模型（合并两个文件的模型定义）
            class User(self.db.Model):
                __tablename__ = 'user'
                id = self.db.Column(self.db.Integer, primary_key=True)
                username = self.db.Column(self.db.String(50), unique=True, nullable=False)
                email = self.db.Column(self.db.String(100), unique=True, nullable=False)
                is_admin = self.db.Column(self.db.Boolean, default=False)
                is_banned = self.db.Column(self.db.Boolean, default=False)
                created_at = self.db.Column(self.db.DateTime, default=lambda: datetime.now(pytz.utc))
                
                # 定义级联删除关系
                comments = self.db.relationship('Comment', backref='author', lazy=True, cascade='all, delete-orphan')
                favorites = self.db.relationship('Favorite', backref='user', lazy=True, cascade='all, delete-orphan')
                likes = self.db.relationship('Like', backref='user', lazy=True, cascade='all, delete-orphan')
                user_points = self.db.relationship('UserPoints', backref='user', uselist=False, lazy=True, cascade='all, delete-orphan')
                collections = self.db.relationship('Collection', backref='user', lazy=True, cascade='all, delete-orphan')
                version_confirms = self.db.relationship('UserVersionConfirm', backref='user', lazy=True, cascade='all, delete-orphan')
                announcements = self.db.relationship('Announcement', backref='creator', lazy=True, cascade='all, delete-orphan')
                version_updates = self.db.relationship('VersionUpdate', backref='creator', lazy=True, cascade='all, delete-orphan')
                task_completions = self.db.relationship('PointTaskCompletion', backref='user', lazy=True, cascade='all, delete-orphan')
                
                # 用于显示的字符串表示
                def __str__(self):
                    return f"{self.id}: {self.username} ({'管理员' if self.is_admin else '普通用户'})"
            
            class Article(self.db.Model):
                __tablename__ = 'article'
                id = self.db.Column(self.db.Integer, primary_key=True)
                title = self.db.Column(self.db.String(200), nullable=False)
                user_id = self.db.Column(self.db.Integer, self.db.ForeignKey('user.id'), nullable=False)
                created_at = self.db.Column(self.db.DateTime, default=lambda: datetime.now(pytz.utc))
                is_approved = self.db.Column(self.db.Boolean, default=False)
                
                # 定义级联删除关系
                comments = self.db.relationship('Comment', backref='article', lazy=True, cascade='all, delete-orphan')
                favorites = self.db.relationship('Favorite', backref='article', lazy=True, cascade='all, delete-orphan')
                likes = self.db.relationship('Like', backref='article', lazy=True, cascade='all, delete-orphan')
                source_article_collections = self.db.relationship('SourceArticleCollection', backref='article', lazy=True, cascade='all, delete-orphan')
                related_articles_as_source = self.db.relationship('ArticleRelation', foreign_keys='ArticleRelation.source_article_id', backref='source_article', lazy=True, cascade='all, delete-orphan')
                related_articles_as_target = self.db.relationship('ArticleRelation', foreign_keys='ArticleRelation.target_article_id', backref='target_article', lazy=True, cascade='all, delete-orphan')
                related_announcements = self.db.relationship('AnnouncementArticleRelation', backref='article', lazy=True, cascade='all, delete-orphan')
                
                # 关联用户
                author = self.db.relationship('User')
            
            # 定义关联模型
            class Comment(self.db.Model):
                __tablename__ = 'comment'
                id = self.db.Column(self.db.Integer, primary_key=True)
                user_id = self.db.Column(self.db.Integer, self.db.ForeignKey('user.id'), nullable=False)
                article_id = self.db.Column(self.db.Integer, self.db.ForeignKey('article.id'), nullable=False)
            
            class Favorite(self.db.Model):
                __tablename__ = 'favorite'
                id = self.db.Column(self.db.Integer, primary_key=True)
                user_id = self.db.Column(self.db.Integer, self.db.ForeignKey('user.id'), nullable=False)
                article_id = self.db.Column(self.db.Integer, self.db.ForeignKey('article.id'), nullable=False)
            
            class Like(self.db.Model):
                __tablename__ = 'like'
                id = self.db.Column(self.db.Integer, primary_key=True)
                user_id = self.db.Column(self.db.Integer, self.db.ForeignKey('user.id'), nullable=False)
                article_id = self.db.Column(self.db.Integer, self.db.ForeignKey('article.id'), nullable=False)
            
            class UserPoints(self.db.Model):
                __tablename__ = 'user_points'
                id = self.db.Column(self.db.Integer, primary_key=True)
                user_id = self.db.Column(self.db.Integer, self.db.ForeignKey('user.id'), nullable=False)
            
            class Collection(self.db.Model):
                __tablename__ = 'collection'
                id = self.db.Column(self.db.Integer, primary_key=True)
                user_id = self.db.Column(self.db.Integer, self.db.ForeignKey('user.id'), nullable=False)
            
            class UserVersionConfirm(self.db.Model):
                __tablename__ = 'user_version_confirm'
                id = self.db.Column(self.db.Integer, primary_key=True)
                user_id = self.db.Column(self.db.Integer, self.db.ForeignKey('user.id'), nullable=False)
            
            class Announcement(self.db.Model):
                __tablename__ = 'announcement'
                id = self.db.Column(self.db.Integer, primary_key=True)
                created_by = self.db.Column(self.db.Integer, self.db.ForeignKey('user.id'), nullable=False)
            
            class VersionUpdate(self.db.Model):
                __tablename__ = 'version_update'
                id = self.db.Column(self.db.Integer, primary_key=True)
                created_by = self.db.Column(self.db.Integer, self.db.ForeignKey('user.id'), nullable=False)
            
            class PointTaskCompletion(self.db.Model):
                __tablename__ = 'point_task_completion'
                id = self.db.Column(self.db.Integer, primary_key=True)
                user_id = self.db.Column(self.db.Integer, self.db.ForeignKey('user.id'), nullable=False)
            
            class SourceArticleCollection(self.db.Model):
                __tablename__ = 'source_article_collection'
                id = self.db.Column(self.db.Integer, primary_key=True)
                article_id = self.db.Column(self.db.Integer, self.db.ForeignKey('article.id'), nullable=False)
            
            class ArticleRelation(self.db.Model):
                __tablename__ = 'article_relation'
                id = self.db.Column(self.db.Integer, primary_key=True)
                source_article_id = self.db.Column(self.db.Integer, self.db.ForeignKey('article.id'), nullable=False)
                target_article_id = self.db.Column(self.db.Integer, self.db.ForeignKey('article.id'), nullable=False)
            
            class AnnouncementArticleRelation(self.db.Model):
                __tablename__ = 'announcement_article_relation'
                id = self.db.Column(self.db.Integer, primary_key=True)
                article_id = self.db.Column(self.db.Integer, self.db.ForeignKey('article.id'), nullable=False)
            
            # 保存模型类引用
                self.User = User
                self.Article = Article
                
                print("创建数据库表（如果不存在）...")
                # 创建数据库表（如果不存在）
                with self.app.app_context():
                    self.db.create_all()
                
                print("成功连接到数据库")
                # 显示数据库连接成功消息
                self.update_status("成功连接到数据库")
                
        except Exception as e:
            print(f"连接数据库时出错: {str(e)}")
            messagebox.showerror("数据库错误", f"连接数据库时出错: {str(e)}")
            self.root.destroy()
            sys.exit(1)
    
    def create_notebook(self):
        """创建标签页控件"""
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建标签页控件
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # 创建删除文章标签页
        self.article_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.article_frame, text="删除文章")
        
        # 创建删除用户标签页
        self.user_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.user_frame, text="删除用户")
        
        # 初始化标签页内容
        self.init_article_tab()
        self.init_user_tab()
    
    def init_article_tab(self):
        """初始化删除文章标签页"""
        # 顶部：用户ID输入区域
        user_frame = ttk.Frame(self.article_frame)
        user_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(user_frame, text="用户ID（可选，用于权限检查）:").pack(side=tk.LEFT, padx=(0, 5))
        self.article_user_id_var = tk.StringVar()
        user_id_entry = ttk.Entry(user_frame, textvariable=self.article_user_id_var, width=10)
        user_id_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        # 文章列表区域
        list_frame = ttk.LabelFrame(self.article_frame, text="文章列表", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 创建Treeview来显示文章列表
        columns = ("id", "title", "author", "created_at", "status")
        self.article_tree = ttk.Treeview(list_frame, columns=columns, show="headings")
        
        # 设置列标题和宽度
        self.article_tree.heading("id", text="ID")
        self.article_tree.heading("title", text="标题")
        self.article_tree.heading("author", text="作者")
        self.article_tree.heading("created_at", text="创建时间")
        self.article_tree.heading("status", text="状态")
        
        self.article_tree.column("id", width=50, anchor=tk.CENTER)
        self.article_tree.column("title", width=250, anchor=tk.W)
        self.article_tree.column("author", width=120, anchor=tk.CENTER)
        self.article_tree.column("created_at", width=150, anchor=tk.CENTER)
        self.article_tree.column("status", width=80, anchor=tk.CENTER)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.article_tree.yview)
        self.article_tree.configure(yscroll=scrollbar.set)
        
        # 布局Treeview和滚动条
        self.article_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 底部：操作按钮区域
        button_frame = ttk.Frame(self.article_frame)
        button_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.delete_single_btn = ttk.Button(button_frame, text="删除选中文章", command=self.delete_selected_article)
        self.delete_single_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.delete_batch_btn = ttk.Button(button_frame, text="批量删除", command=self.delete_batch_articles)
        self.delete_batch_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.refresh_article_btn = ttk.Button(button_frame, text="刷新列表", command=self.load_articles)
        self.refresh_article_btn.pack(side=tk.RIGHT)
        
        # 加载文章列表
        self.load_articles()
    
    def init_user_tab(self):
        """初始化删除用户标签页"""
        # 用户ID输入区域
        id_frame = ttk.Frame(self.user_frame, padding=10)
        id_frame.pack(fill=tk.X)
        
        ttk.Label(id_frame, text="用户ID:", width=10).pack(side=tk.LEFT, padx=5)
        self.user_id_var = tk.StringVar()
        self.user_id_entry = ttk.Entry(id_frame, textvariable=self.user_id_var, width=15)
        self.user_id_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(id_frame, text="查找用户", command=self.find_user_by_id).pack(side=tk.LEFT, padx=5)
        ttk.Button(id_frame, text="刷新列表", command=self.refresh_user_list).pack(side=tk.LEFT, padx=5)
        
        # 用户信息显示区域
        info_frame = ttk.LabelFrame(self.user_frame, text="用户信息", padding=10)
        info_frame.pack(fill=tk.X, pady=10)
        
        # 创建标签网格来显示用户信息
        self.info_labels = {}
        info_fields = [
            ("ID:", "id"),
            ("用户名:", "username"),
            ("邮箱:", "email"),
            ("角色:", "role"),
            ("状态:", "status"),
            ("创建时间:", "created_at")
        ]
        
        for i, (label_text, field_name) in enumerate(info_fields):
            ttk.Label(info_frame, text=label_text, width=12).grid(row=i, column=0, sticky=tk.W, padx=5, pady=2)
            self.info_labels[field_name] = ttk.Label(info_frame, text="--")
            self.info_labels[field_name].grid(row=i, column=1, sticky=tk.W, padx=5, pady=2)
        
        # 用户列表
        list_frame = ttk.LabelFrame(self.user_frame, text="用户列表", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # 创建Treeview
        columns = ("id", "username", "email", "role", "status", "created_at")
        self.user_tree = ttk.Treeview(list_frame, columns=columns, show="headings")
        
        # 设置列标题
        self.user_tree.heading("id", text="ID")
        self.user_tree.heading("username", text="用户名")
        self.user_tree.heading("email", text="邮箱")
        self.user_tree.heading("role", text="角色")
        self.user_tree.heading("status", text="状态")
        self.user_tree.heading("created_at", text="创建时间")
        
        # 设置列宽
        self.user_tree.column("id", width=50, anchor=tk.CENTER)
        self.user_tree.column("username", width=150, anchor=tk.W)
        self.user_tree.column("email", width=250, anchor=tk.W)
        self.user_tree.column("role", width=80, anchor=tk.CENTER)
        self.user_tree.column("status", width=80, anchor=tk.CENTER)
        self.user_tree.column("created_at", width=150, anchor=tk.CENTER)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.user_tree.yview)
        self.user_tree.configure(yscroll=scrollbar.set)
        
        # 布局Treeview和滚动条
        self.user_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 绑定双击事件
        self.user_tree.bind("<Double-1>", self.on_tree_item_double_click)
        
        # 操作按钮区域
        button_frame = ttk.Frame(self.user_frame, padding=10)
        button_frame.pack(fill=tk.X, pady=10)
        
        # 创建删除按钮
        self.delete_button = ttk.Button(button_frame, text="删除用户", command=self.confirm_delete_user, state=tk.DISABLED)
        self.delete_button.pack(side=tk.RIGHT, padx=5)
        
        # 刷新用户列表
        self.refresh_user_list()
    
    def create_status_bar(self):
        """创建状态栏"""
        self.status_var = tk.StringVar()
        self.status_var.set("就绪")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def update_status(self, message):
        """更新状态栏信息"""
        self.status_var.set(message)
        self.root.update_idletasks()
    
    # ===== 删除文章相关方法 =====
    def load_articles(self):
        """加载文章列表到Treeview"""
        # 清空现有数据
        for item in self.article_tree.get_children():
            self.article_tree.delete(item)
        
        try:
            with self.app.app_context():
                # 查询所有文章
                articles = self.Article.query.order_by(self.Article.created_at.desc()).all()
                
                # 将文章数据添加到Treeview
                for article in articles:
                    # 获取作者名称
                    author_name = "未知" if not article.author else article.author.username
                    
                    # 格式化创建时间
                    created_at = article.created_at.strftime('%Y-%m-%d %H:%M') if article.created_at else "未知"
                    
                    # 获取文章状态
                    status = "已审核" if article.is_approved else "待审核"
                    
                    # 添加到Treeview
                    self.article_tree.insert("", tk.END, values=(article.id, article.title, author_name, created_at, status))
                
            self.update_status(f"共加载 {len(articles)} 篇文章")
            
        except Exception as e:
            messagebox.showerror("加载错误", f"加载文章列表时出错: {str(e)}")
            self.update_status("加载文章列表失败")
    
    def delete_selected_article(self):
        """删除选中的文章"""
        selected_items = self.article_tree.selection()
        
        if not selected_items:
            messagebox.showwarning("警告", "请先选择要删除的文章")
            return
            
        # 获取选中文章的ID
        selected_item = selected_items[0]
        article_id = self.article_tree.item(selected_item, "values")[0]
        article_title = self.article_tree.item(selected_item, "values")[1]
        
        # 确认删除
        confirm = messagebox.askyesno("确认删除", f"确定要删除文章《{article_title}》吗？\n此操作不可撤销！")
        
        if confirm:
            # 获取用户ID（如果有）
            user_id = None
            user_id_str = self.article_user_id_var.get().strip()
            if user_id_str:
                try:
                    user_id = int(user_id_str)
                except ValueError:
                    messagebox.showerror("输入错误", "用户ID必须是数字")
                    return
                    
            # 执行删除
            success, message = self.delete_article_by_id(article_id, user_id)
            
            if success:
                messagebox.showinfo("删除成功", message)
                # 刷新文章列表
                self.load_articles()
            else:
                messagebox.showerror("删除失败", message)
    
    def delete_batch_articles(self):
        """批量删除文章"""
        # 让用户输入要删除的文章ID列表
        article_ids_str = simpledialog.askstring("批量删除", "请输入要删除的文章ID，用逗号分隔：")
        
        if not article_ids_str:
            return
            
        try:
            # 解析文章ID列表
            article_ids = [int(id_str.strip()) for id_str in article_ids_str.split(',') if id_str.strip().isdigit()]
            
            if not article_ids:
                messagebox.showwarning("警告", "请输入有效的文章ID")
                return
                
            # 确认删除
            confirm = messagebox.askyesno("确认批量删除", f"确定要删除选中的 {len(article_ids)} 篇文章吗？\n此操作不可撤销！")
            
            if confirm:
                # 获取用户ID（如果有）
                user_id = None
                user_id_str = self.article_user_id_var.get().strip()
                if user_id_str:
                    try:
                        user_id = int(user_id_str)
                    except ValueError:
                        messagebox.showerror("输入错误", "用户ID必须是数字")
                        return
                        
                # 执行批量删除
                results = self.delete_multiple_articles(article_ids, user_id)
                
                # 显示删除结果
                result_msg = f"批量删除完成！\n成功删除: {results['success_count']} 篇\n删除失败: {results['failed_count']} 篇"
                
                if results['failed_articles']:
                    result_msg += "\n\n删除失败的文章："
                    for art in results['failed_articles']:
                        result_msg += f"\n- ID: {art['id']}, 错误: {art['error']}"
                        
                messagebox.showinfo("批量删除结果", result_msg)
                
                # 刷新文章列表
                self.load_articles()
                
        except Exception as e:
            messagebox.showerror("输入错误", f"解析文章ID时出错: {str(e)}")
    
    def delete_article_by_id(self, article_id, current_user_id=None):
        """
        根据文章ID删除文章
        
        参数:
            article_id: 要删除的文章ID
            current_user_id: 当前用户ID（可选），如果提供，则进行权限检查
        
        返回:
            tuple: (是否成功, 消息)
        """
        try:
            with self.app.app_context():
                # 查找文章
                article = self.Article.query.get(article_id)
                
                if not article:
                    return False, f"文章ID {article_id} 不存在"
                
                # 权限检查（如果提供了current_user_id）
                if current_user_id:
                    current_user = self.User.query.get(current_user_id)
                    if not current_user:
                        return False, "无效的用户ID"
                    
                    # 只有文章作者或管理员可以删除
                    if not (current_user.is_admin or article.user_id == current_user_id):
                        return False, "权限不足，只有文章作者或管理员可以删除文章"
                
                try:
                    # 记录要删除的文章信息
                    article_title = article.title
                    
                    # 直接删除文章，级联删除会自动处理关联记录
                    self.db.session.delete(article)
                    self.db.session.commit()
                    
                    return True, f"成功删除文章：{article_title}（ID: {article_id}）"
                    
                except Exception as e:
                    self.db.session.rollback()
                    return False, f"删除文章时发生错误: {str(e)}"
                    
        except Exception as e:
            return False, f"操作数据库时发生错误: {str(e)}"
    
    def delete_multiple_articles(self, article_ids, current_user_id=None):
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
            success, message = self.delete_article_by_id(article_id, current_user_id)
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
    
    # ===== 删除用户相关方法 =====
    def refresh_user_list(self):
        # 清空现有数据
        for item in self.user_tree.get_children():
            self.user_tree.delete(item)
        
        # 从数据库获取用户列表
        with self.app.app_context():
            try:
                users = self.User.query.order_by(self.User.id).all()
                
                # 添加到Treeview
                for user in users:
                    role = "管理员" if user.is_admin else "普通用户"
                    status = "已禁用" if user.is_banned else "正常"
                    # 转换时区并格式化时间
                    if user.created_at:
                        created_at = user.created_at.astimezone(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M')
                    else:
                        created_at = "--"
                    
                    self.user_tree.insert("", tk.END, values=(user.id, user.username, user.email, role, status, created_at))
                
            except Exception as e:
                messagebox.showerror("错误", f"获取用户列表时发生错误: {str(e)}")
    
    def find_user_by_id(self):
        user_id = self.user_id_var.get()
        if not user_id or not user_id.isdigit():
            messagebox.showwarning("警告", "请输入有效的用户ID")
            return
        
        user_id = int(user_id)
        
        # 在数据库中查找用户
        with self.app.app_context():
            try:
                user = self.User.query.get(user_id)
                if user:
                    self.display_user_info(user)
                    self.delete_button.config(state=tk.NORMAL)
                else:
                    messagebox.showinfo("信息", f"未找到ID为 {user_id} 的用户")
                    self.clear_user_info()
                    self.delete_button.config(state=tk.DISABLED)
            except Exception as e:
                messagebox.showerror("错误", f"查找用户时发生错误: {str(e)}")
    
    def display_user_info(self, user):
        # 显示用户信息
        self.info_labels["id"].config(text=str(user.id))
        self.info_labels["username"].config(text=user.username)
        self.info_labels["email"].config(text=user.email)
        self.info_labels["role"].config(text="管理员" if user.is_admin else "普通用户")
        self.info_labels["status"].config(text="已禁用" if user.is_banned else "正常")
        
        # 转换时区并格式化时间
        if user.created_at:
            created_at = user.created_at.astimezone(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')
            self.info_labels["created_at"].config(text=created_at)
        else:
            self.info_labels["created_at"].config(text="--")
            
        # 高亮显示Treeview中的对应行
        for item in self.user_tree.get_children():
            if self.user_tree.item(item, "values")[0] == str(user.id):
                self.user_tree.selection_set(item)
                self.user_tree.see(item)
                break
    
    def clear_user_info(self):
        # 清空用户信息显示
        for label in self.info_labels.values():
            label.config(text="--")
    
    def on_tree_item_double_click(self, event):
        # 获取选中的项
        item = self.user_tree.selection()
        if not item:
            return
        
        # 获取用户ID
        user_id = self.user_tree.item(item[0], "values")[0]
        self.user_id_var.set(user_id)
        self.find_user_by_id()
    
    def confirm_delete_user(self):
        user_id = self.info_labels["id"].cget("text")
        if user_id == "--":
            messagebox.showwarning("警告", "请先查找要删除的用户")
            return
        
        # 确认删除
        username = self.info_labels["username"].cget("text")
        is_admin = self.info_labels["role"].cget("text") == "管理员"
        
        # 警告管理员删除
        if is_admin:
            if not messagebox.askyesno("警告", f"确定要删除管理员用户 '{username}' 吗？此操作不可恢复！"):
                return
        else:
            if not messagebox.askyesno("确认", f"确定要删除用户 '{username}' 吗？此操作不可恢复！"):
                return
        
        # 执行删除
        self.delete_user(int(user_id))
    
    def delete_user(self, user_id):
        with self.app.app_context():
            try:
                # 查找用户
                user = self.User.query.get(user_id)
                if not user:
                    messagebox.showinfo("信息", "用户不存在或已被删除")
                    return
                
                # 禁止删除最后一个管理员
                admin_count = self.User.query.filter_by(is_admin=True).count()
                if user.is_admin and admin_count <= 1:
                    messagebox.showerror("错误", "不能删除最后一个管理员用户")
                    return
                
                # 记录要删除的用户名
                username = user.username
                
                # 删除用户
                self.db.session.delete(user)
                self.db.session.commit()
                
                messagebox.showinfo("成功", f"用户 '{username}' 已成功删除")
                
                # 清空用户信息并刷新列表
                self.clear_user_info()
                self.user_id_var.set("")
                self.refresh_user_list()
                self.delete_button.config(state=tk.DISABLED)
                
            except Exception as e:
                self.db.session.rollback()
                messagebox.showerror("错误", f"删除用户时发生错误: {str(e)}")

if __name__ == '__main__':
    try:
        print("程序主入口 - 创建主窗口")
        # 创建主窗口
        root = tk.Tk()
        
        print("创建应用实例")
        # 创建应用实例
        app = AdminToolApp(root)
        
        print("进入主循环")
        # 运行主循环
        root.mainloop()
    except Exception as e:
        print(f"程序运行出错: {str(e)}")
        import traceback
        traceback.print_exc()
        messagebox.showerror("程序错误", f"程序运行出错: {str(e)}")
        sys.exit(1)