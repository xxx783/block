#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
部署测试脚本
用于验证Flask应用在虚拟主机环境中的基本功能是否正常
"""

import os
import sys
import time

def test_environment():
    """测试Python环境和基本依赖"""
    print("===== 环境测试 =====")
    print(f"Python版本: {sys.version}")
    
    # 检查关键模块是否可导入
    required_modules = ['flask', 'flask_sqlalchemy', 'flask_mail', 'pytz', 'markdown']
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"✓ 成功导入模块: {module}")
        except ImportError:
            print(f"✗ 无法导入模块: {module}")
            print(f"  请运行: pip install {module}")

    print("\n当前工作目录:", os.getcwd())


def test_app_config():
    """测试应用配置和数据库连接"""
    print("\n===== 应用配置测试 =====")
    
    try:
        # 导入应用实例
        from app import app, db
        print("✓ 成功导入应用和数据库实例")
        
        # 打印关键配置
        print(f"\n应用配置:")
        print(f"- DEBUG模式: {app.config.get('DEBUG', '未设置')}")
        print(f"- 数据库URI: {app.config.get('SQLALCHEMY_DATABASE_URI', '未设置')}")
        print(f"- 邮件功能: {'已启用' if app.config.get('MAIL_ENABLED', False) else '已禁用'}")
        
        # 测试数据库连接
        with app.app_context():
            try:
                # 执行简单查询验证连接
                result = db.engine.execute('SELECT 1')
                row = result.fetchone()
                print(f"✓ 数据库连接成功，测试结果: {row}")
            except Exception as e:
                print(f"✗ 数据库连接失败: {str(e)}")
                print("  请检查数据库配置和权限")
                
    except Exception as e:
        print(f"✗ 应用初始化失败: {str(e)}")
        import traceback
        traceback.print_exc()


def test_static_files():
    """测试静态文件目录是否存在"""
    print("\n===== 静态文件测试 =====")
    
    # 检查templates目录
    templates_dir = os.path.join(os.getcwd(), 'templates')
    if os.path.exists(templates_dir):
        print(f"✓ 模板目录存在: {templates_dir}")
        # 检查关键模板文件
        key_templates = ['base.html', 'index.html', 'login.html']
        for template in key_templates:
            if os.path.exists(os.path.join(templates_dir, template)):
                print(f"  - 存在模板文件: {template}")
            else:
                print(f"  - 缺少模板文件: {template}")
    else:
        print(f"✗ 模板目录不存在: {templates_dir}")
    
    # 检查static目录
    static_dir = os.path.join(os.getcwd(), 'static')
    if os.path.exists(static_dir):
        print(f"✓ 静态文件目录存在: {static_dir}")
    else:
        print(f"✗ 静态文件目录不存在: {static_dir}")


def test_wsgi_entry():
    """测试WSGI入口文件"""
    print("\n===== WSGI入口测试 =====")
    
    # 检查wsgi.py文件是否存在
    wsgi_file = os.path.join(os.getcwd(), 'wsgi.py')
    if os.path.exists(wsgi_file):
        print(f"✓ WSGI入口文件存在: {wsgi_file}")
        
        try:
            # 尝试导入WSGI应用
            import importlib.util
            spec = importlib.util.spec_from_file_location("wsgi", wsgi_file)
            wsgi_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(wsgi_module)
            
            if hasattr(wsgi_module, 'application'):
                print("✓ 成功导入WSGI应用实例")
            else:
                print("✗ WSGI文件中缺少application对象")
        except Exception as e:
            print(f"✗ 导入WSGI文件失败: {str(e)}")
    else:
        print("✗ WSGI入口文件不存在")
        print("  对于虚拟主机部署，建议创建wsgi.py文件")


def print_deployment_tips():
    """打印部署提示"""
    print("\n===== 部署提示 =====")
    print("1. 确保在生产环境中关闭DEBUG模式")
    print("2. 使用环境变量设置敏感信息（如SECRET_KEY、邮件密码等）")
    print("3. 对于虚拟主机，推荐使用WSGI服务器（如Gunicorn）运行应用")
    print("4. 确保instance目录存在且有写权限")
    print("5. 检查虚拟主机的防火墙设置，确保应用端口可访问")
    print("6. 查看虚拟主机(无命令行)部署指南.md获取详细配置步骤")


def main():
    """主函数"""
    print("===== Flask应用部署测试工具 =====")
    print(f"运行时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    test_environment()
    test_app_config()
    test_static_files()
    test_wsgi_entry()
    print_deployment_tips()
    
    print("\n===== 测试完成 =====")


if __name__ == '__main__':
    main()