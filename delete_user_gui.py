import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import os
from datetime import datetime
import pytz

# 导入Flask和数据库相关模块
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

class DeleteUserGUI:
    def __init__(self, root):
        # 设置中文字体支持
        self.style = ttk.Style()
        self.style.configure('.', font=('SimHei', 10))
        self.style.configure('Treeview', font=('SimHei', 9))
        self.style.configure('Treeview.Heading', font=('SimHei', 10, 'bold'))
        
        self.root = root
        self.root.title('删除用户工具')
        self.root.geometry('800x600')
        self.root.resizable(True, True)
        
        # 设置主题色
        self.root.configure(bg='#f0f0f0')
        
        # 初始化Flask应用和数据库
        self.init_flask_app()
        
        # 创建界面
        self.create_widgets()
        
        # 刷新用户列表
        self.refresh_user_list()
    
    def init_flask_app(self):
        # 创建Flask应用
        self.app = Flask(__name__)
        
        # 配置数据库
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'app.db')
        self.app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
        self.app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        # 初始化数据库
        self.db = SQLAlchemy(self.app)
        
        # 定义最小化的User模型
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
        
        # 定义最小化的相关模型（用于级联删除）
        class Comment(self.db.Model):
            __tablename__ = 'comment'
            id = self.db.Column(self.db.Integer, primary_key=True)
            user_id = self.db.Column(self.db.Integer, self.db.ForeignKey('user.id'), nullable=False)
        
        class Favorite(self.db.Model):
            __tablename__ = 'favorite'
            id = self.db.Column(self.db.Integer, primary_key=True)
            user_id = self.db.Column(self.db.Integer, self.db.ForeignKey('user.id'), nullable=False)
        
        class Like(self.db.Model):
            __tablename__ = 'like'
            id = self.db.Column(self.db.Integer, primary_key=True)
            user_id = self.db.Column(self.db.Integer, self.db.ForeignKey('user.id'), nullable=False)
        
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
        
        # 存储模型引用
        self.User = User
        
        # 创建数据库表（如果不存在）
        with self.app.app_context():
            self.db.create_all()
    
    def create_widgets(self):
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 用户ID输入区域
        id_frame = ttk.Frame(main_frame, padding=10)
        id_frame.pack(fill=tk.X)
        
        ttk.Label(id_frame, text="用户ID:", width=10).pack(side=tk.LEFT, padx=5)
        self.user_id_var = tk.StringVar()
        self.user_id_entry = ttk.Entry(id_frame, textvariable=self.user_id_var, width=15)
        self.user_id_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(id_frame, text="查找用户", command=self.find_user_by_id).pack(side=tk.LEFT, padx=5)
        ttk.Button(id_frame, text="刷新列表", command=self.refresh_user_list).pack(side=tk.LEFT, padx=5)
        
        # 用户信息显示区域
        info_frame = ttk.LabelFrame(main_frame, text="用户信息", padding=10)
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
        list_frame = ttk.LabelFrame(main_frame, text="用户列表", padding=10)
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
        self.user_tree.column("email", width=200, anchor=tk.W)
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
        button_frame = ttk.Frame(main_frame, padding=10)
        button_frame.pack(fill=tk.X, pady=10)
        
        # 创建删除按钮
        self.delete_button = ttk.Button(button_frame, text="删除用户", command=self.confirm_delete_user, state=tk.DISABLED)
        self.delete_button.pack(side=tk.RIGHT, padx=5)
    
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
                # 开始事务
                # 在Flask-SQLAlchemy中，不需要手动调用begin()
                
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

if __name__ == "__main__":
    root = tk.Tk()
    app = DeleteUserGUI(root)
    root.mainloop()