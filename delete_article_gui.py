#!/usr/bin/env python3
"""
删除文章工具 - 图形界面版
使用tkinter创建的图形界面，用于删除文章
"""

import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pytz

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class DeleteArticleApp:
    def __init__(self, root):
        # 主窗口设置
        self.root = root
        self.root.title("删除文章工具")
        self.root.geometry("600x400")
        self.root.resizable(True, True)
        
        # 设置中文字体支持
        self.style = ttk.Style()
        self.style.configure('.', font=('SimHei', 10))
        
        # 初始化数据库连接
        self.init_database()
        
        # 创建GUI组件
        self.create_widgets()
        
        # 加载文章列表
        self.load_articles()
        
    def init_database(self):
        """初始化数据库连接"""
        try:
            # 创建Flask应用实例
            self.app = Flask(__name__)
            
            # 配置数据库 - 使用绝对路径确保能正确打开数据库文件
            db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'app.db')
            self.app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
            self.app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
            
            # 初始化数据库
            self.db = SQLAlchemy(self.app)
            
            # 定义必要的模型（最小化定义，仅用于删除操作）
            class User(self.db.Model):
                __tablename__ = 'user'
                id = self.db.Column(self.db.Integer, primary_key=True)
                username = self.db.Column(self.db.String(50), unique=True, nullable=False)
                is_admin = self.db.Column(self.db.Boolean, default=False)
            
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
                article_id = self.db.Column(self.db.Integer, self.db.ForeignKey('article.id'), nullable=False)
            
            class Favorite(self.db.Model):
                __tablename__ = 'favorite'
                id = self.db.Column(self.db.Integer, primary_key=True)
                article_id = self.db.Column(self.db.Integer, self.db.ForeignKey('article.id'), nullable=False)
            
            class Like(self.db.Model):
                __tablename__ = 'like'
                id = self.db.Column(self.db.Integer, primary_key=True)
                article_id = self.db.Column(self.db.Integer, self.db.ForeignKey('article.id'), nullable=False)
            
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
            
            messagebox.showinfo("数据库连接", "成功连接到数据库")
            
        except Exception as e:
            messagebox.showerror("数据库错误", f"连接数据库时出错: {str(e)}")
            self.root.destroy()
            sys.exit(1)
    
    def create_widgets(self):
        """创建GUI组件"""
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 顶部：用户ID输入区域
        user_frame = ttk.Frame(main_frame)
        user_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(user_frame, text="用户ID（可选，用于权限检查）:").pack(side=tk.LEFT, padx=(0, 5))
        self.user_id_var = tk.StringVar()
        user_id_entry = ttk.Entry(user_frame, textvariable=self.user_id_var, width=10)
        user_id_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        # 文章列表区域
        list_frame = ttk.LabelFrame(main_frame, text="文章列表", padding="10")
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
        self.article_tree.column("title", width=200, anchor=tk.W)
        self.article_tree.column("author", width=100, anchor=tk.CENTER)
        self.article_tree.column("created_at", width=120, anchor=tk.CENTER)
        self.article_tree.column("status", width=80, anchor=tk.CENTER)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.article_tree.yview)
        self.article_tree.configure(yscroll=scrollbar.set)
        
        # 布局Treeview和滚动条
        self.article_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 底部：操作按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.delete_single_btn = ttk.Button(button_frame, text="删除选中文章", command=self.delete_selected_article)
        self.delete_single_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.delete_batch_btn = ttk.Button(button_frame, text="批量删除", command=self.delete_batch_articles)
        self.delete_batch_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.refresh_btn = ttk.Button(button_frame, text="刷新列表", command=self.load_articles)
        self.refresh_btn.pack(side=tk.RIGHT)
        
        # 状态信息区域
        self.status_var = tk.StringVar()
        self.status_var.set("就绪")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
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
                
            self.status_var.set(f"共加载 {len(articles)} 篇文章")
            
        except Exception as e:
            messagebox.showerror("加载错误", f"加载文章列表时出错: {str(e)}")
            self.status_var.set("加载文章列表失败")
            
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
            user_id_str = self.user_id_var.get().strip()
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
                user_id_str = self.user_id_var.get().strip()
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

if __name__ == '__main__':
    # 创建主窗口
    root = tk.Tk()
    
    # 创建应用实例
    app = DeleteArticleApp(root)
    
    # 运行主循环
    root.mainloop()