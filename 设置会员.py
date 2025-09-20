import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db

# 延迟导入User，避免在数据库表创建前查询
def get_user_model():
    from app import User
    return User

def set_vip_status():
    """设置用户会员状态的GUI应用程序"""
    
    def search_user():
        """搜索用户"""
        username = username_entry.get().strip()
        if not username:
            messagebox.showwarning("警告", "请输入用户名")
            return
        
        with app.app_context():
            User = get_user_model()
            user = User.query.filter_by(username=username).first()
            if user:
                # 显示用户信息
                user_info_text.config(state=tk.NORMAL)
                user_info_text.delete(1.0, tk.END)
                user_info_text.insert(tk.END, f"用户名: {user.username}\n")
                user_info_text.insert(tk.END, f"邮箱: {user.email}\n")
                user_info_text.insert(tk.END, f"密码: {user.password}\n")
                user_info_text.insert(tk.END, f"当前会员状态: {'是' if user.is_vip else '否'}\n")
                if user.is_vip:
                    if not user.vip_expires_at:
                        user_info_text.insert(tk.END, f"会员等级: 永久会员\n")
                    else:
                        user_info_text.insert(tk.END, f"会员等级: {'超级会员' if user.vip_level == 1 else '普通会员'}\n")
                        user_info_text.insert(tk.END, f"会员过期时间: {user.vip_expires_at.strftime('%Y-%m-%d %H:%M:%S')}\n")
                user_info_text.insert(tk.END, f"管理员: {'是' if user.is_admin else '否'}\n")
                user_info_text.insert(tk.END, f"注册时间: {user.created_at}")
                user_info_text.config(state=tk.DISABLED)
                
                # 更新会员状态选择
                vip_status.set(user.is_vip)
                
                # 更新会员等级选择
                vip_level.set(user.vip_level)
                
                # 更新永久会员选项
                permanent_vip_var.set(not user.vip_expires_at if user.is_vip else False)
                
                # 更新过期时间显示
                if user.vip_expires_at:
                    expire_date_entry.delete(0, tk.END)
                    expire_date_entry.insert(0, user.vip_expires_at.strftime('%Y-%m-%d'))
                    expire_time_entry.delete(0, tk.END)
                    expire_time_entry.insert(0, user.vip_expires_at.strftime('%H:%M:%S'))
                else:
                    expire_date_entry.delete(0, tk.END)
                    expire_time_entry.delete(0, tk.END)
                
                # 启用操作按钮
                set_vip_button.config(state=tk.NORMAL)
                
            else:
                messagebox.showerror("错误", f"用户 '{username}' 不存在")
                user_info_text.config(state=tk.NORMAL)
                user_info_text.delete(1.0, tk.END)
                user_info_text.config(state=tk.DISABLED)
                set_vip_button.config(state=tk.DISABLED)
    
    def set_vip():
        """设置会员状态"""
        username = username_entry.get().strip()
        if not username:
            messagebox.showwarning("警告", "请输入用户名")
            return
        
        new_status = vip_status.get()
        new_level = vip_level.get()
        is_permanent = permanent_vip_var.get()
        
        # 处理过期时间
        expire_date = expire_date_entry.get().strip()
        expire_time = expire_time_entry.get().strip()
        vip_expires_at = None
        
        if new_status and not is_permanent and expire_date:
            try:
                from datetime import datetime
                if expire_time:
                    datetime_str = f"{expire_date} {expire_time}"
                    vip_expires_at = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
                else:
                    datetime_str = f"{expire_date} 23:59:59"
                    vip_expires_at = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
                
                # 检查时间是否已经过去
                from datetime import datetime
                if vip_expires_at < datetime.now():
                    messagebox.showwarning("警告", "过期时间不能是过去的时间")
                    return
                    
            except ValueError:
                messagebox.showwarning("警告", "日期时间格式错误，请使用 YYYY-MM-DD HH:MM:SS 格式")
                return
        
        with app.app_context():
            User = get_user_model()
            user = User.query.filter_by(username=username).first()
            if user:
                try:
                    user.is_vip = new_status
                    user.vip_level = new_level
                    user.vip_expires_at = vip_expires_at
                    db.session.commit()
                    
                    status_text = "会员" if new_status else "非会员"
                    if new_status:
                        if is_permanent:
                            level_text = "（永久会员）"
                        else:
                            level_text = f"（{'超级会员' if new_level == 1 else '普通会员'}）"
                    else:
                        level_text = ""
                    expire_text = f"，过期时间: {vip_expires_at.strftime('%Y-%m-%d %H:%M:%S')}" if vip_expires_at else ""
                    messagebox.showinfo("成功", f"已将用户 '{username}' 设置为{status_text}{level_text}{expire_text}")
                    
                    # 刷新用户信息显示
                    search_user()
                    
                except Exception as e:
                    db.session.rollback()
                    messagebox.showerror("错误", f"设置失败: {str(e)}")
            else:
                messagebox.showerror("错误", f"用户 '{username}' 不存在")
    
    def show_all_users():
        """显示所有用户"""
        with app.app_context():
            User = get_user_model()
            users = User.query.order_by(User.username).all()
            
            # 创建新窗口显示用户列表
            user_list_window = tk.Toplevel(root)
            user_list_window.title("所有用户列表")
            user_list_window.geometry("900x400")
            user_list_window.resizable(True, True)
            
            # 创建表格
            tree = ttk.Treeview(user_list_window, columns=("username", "email", "password", "is_vip", "vip_level", "vip_expires_at", "is_admin", "created_at"), show="headings")
            
            # 设置列标题
            tree.heading("username", text="用户名")
            tree.heading("email", text="邮箱")
            tree.heading("password", text="密码")
            tree.heading("is_vip", text="会员")
            tree.heading("vip_level", text="会员等级")
            tree.heading("vip_expires_at", text="会员过期时间")
            tree.heading("is_admin", text="管理员")
            tree.heading("created_at", text="注册时间")
            
            # 设置列宽
            tree.column("username", width=100)
            tree.column("email", width=150)
            tree.column("password", width=150)
            tree.column("is_vip", width=50)
            tree.column("vip_level", width=80)
            tree.column("vip_expires_at", width=120)
            tree.column("is_admin", width=50)
            tree.column("created_at", width=150)
            
            # 添加滚动条
            scrollbar = ttk.Scrollbar(user_list_window, orient=tk.VERTICAL, command=tree.yview)
            tree.configure(yscrollcommand=scrollbar.set)
            
            # 填充数据
            for user in users:
                tree.insert("", tk.END, values=(
                    user.username,
                    user.email,
                    user.password,
                    "是" if user.is_vip else "否",
                    "超级会员" if user.vip_level == 1 else "普通会员" if user.is_vip else "",
                    user.vip_expires_at.strftime('%Y-%m-%d %H:%M') if user.vip_expires_at else "",
                    "是" if user.is_admin else "否",
                    user.created_at.strftime('%Y-%m-%d %H:%M:%S') if user.created_at else ""
                ))
            
            # 布局
            tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # 双击事件
            def on_double_click(event):
                item = tree.selection()[0]
                username = tree.item(item, "values")[0]
                username_entry.delete(0, tk.END)
                username_entry.insert(0, username)
                search_user()
                user_list_window.destroy()
            
            tree.bind("<Double-1>", on_double_click)
    
    # 创建主窗口
    root = tk.Tk()
    root.title("会员管理系统")
    root.geometry("500x650")
    #root.resizable(False, False)
    
    # 设置样式
    style = ttk.Style()
    style.configure("TFrame", background="#f0f0f0")
    style.configure("TLabel", background="#f0f0f0", font=("微软雅黑", 10))
    style.configure("TButton", font=("微软雅黑", 9))
    style.configure("TEntry", font=("微软雅黑", 9))
    
    # 主框架
    main_frame = ttk.Frame(root, padding="20")
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # 标题
    title_label = ttk.Label(main_frame, text="会员管理系统", font=("微软雅黑", 16, "bold"))
    title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
    
    # 搜索区域
    search_frame = ttk.Frame(main_frame)
    search_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 10))
    
    ttk.Label(search_frame, text="用户名:").grid(row=0, column=0, sticky="w")
    username_entry = ttk.Entry(search_frame, width=20)
    username_entry.grid(row=0, column=1, padx=(5, 5))
    
    search_button = ttk.Button(search_frame, text="搜索用户", command=search_user)
    search_button.grid(row=0, column=2, padx=(5, 0))
    
    show_all_button = ttk.Button(search_frame, text="显示所有用户", command=show_all_users)
    show_all_button.grid(row=0, column=3, padx=(5, 0))
    
    # 用户信息显示
    ttk.Label(main_frame, text="用户信息:").grid(row=2, column=0, sticky="w", pady=(10, 5))
    
    user_info_text = tk.Text(main_frame, height=8, width=50, font=("微软雅黑", 9))
    user_info_text.grid(row=3, column=0, columnspan=2, pady=(0, 10))
    user_info_text.config(state=tk.DISABLED)
    
    # 会员设置区域
    vip_frame = ttk.Frame(main_frame)
    vip_frame.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(0, 10))
    
    ttk.Label(vip_frame, text="会员状态:").grid(row=0, column=0, sticky="w")
    
    vip_status = tk.BooleanVar()
    vip_yes = ttk.Radiobutton(vip_frame, text="会员", variable=vip_status, value=True)
    vip_no = ttk.Radiobutton(vip_frame, text="非会员", variable=vip_status, value=False)
    
    vip_yes.grid(row=0, column=1, padx=(5, 10))
    vip_no.grid(row=0, column=2)
    
    # 会员等级选择
    ttk.Label(vip_frame, text="会员等级:").grid(row=1, column=0, sticky="w", pady=(10, 0))
    
    vip_level = tk.IntVar()
    vip_normal = ttk.Radiobutton(vip_frame, text="普通会员", variable=vip_level, value=0)
    vip_super = ttk.Radiobutton(vip_frame, text="超级会员", variable=vip_level, value=1)
    
    vip_normal.grid(row=1, column=1, padx=(5, 10), pady=(10, 0))
    vip_super.grid(row=1, column=2, pady=(10, 0))
    
    # 永久会员选项
    permanent_vip_frame = ttk.Frame(main_frame)
    permanent_vip_frame.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(5, 5))
    
    permanent_vip_var = tk.BooleanVar()
    permanent_vip_checkbox = ttk.Checkbutton(permanent_vip_frame, text="设置为永久会员", variable=permanent_vip_var)
    permanent_vip_checkbox.grid(row=0, column=0, sticky="w")
    
    # 过期时间设置
    expire_frame = ttk.Frame(main_frame)
    expire_frame.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(10, 10))
    
    ttk.Label(expire_frame, text="过期日期:").grid(row=0, column=0, sticky="w")
    expire_date_entry = ttk.Entry(expire_frame, width=12)
    expire_date_entry.grid(row=0, column=1, padx=(5, 10))
    expire_date_entry.insert(0, "YYYY-MM-DD")
    
    ttk.Label(expire_frame, text="过期时间:").grid(row=0, column=2, sticky="w")
    expire_time_entry = ttk.Entry(expire_frame, width=10)
    expire_time_entry.grid(row=0, column=3, padx=(5, 0))
    expire_time_entry.insert(0, "HH:MM:SS")
    
    # 设置按钮
    set_vip_button = ttk.Button(main_frame, text="设置会员状态", command=set_vip, state=tk.DISABLED)
    set_vip_button.grid(row=7, column=0, columnspan=2, pady=(10, 0))
    
    # 状态栏
    status_bar = ttk.Label(main_frame, text="就绪", relief=tk.SUNKEN, anchor=tk.W)
    status_bar.grid(row=8, column=0, columnspan=2, sticky="ew", pady=(10, 0))
    
    # 配置网格权重
    main_frame.columnconfigure(0, weight=1)
    main_frame.columnconfigure(1, weight=1)
    search_frame.columnconfigure(1, weight=1)
    
    # 运行主循环
    root.mainloop()

if __name__ == "__main__":
    set_vip_status()