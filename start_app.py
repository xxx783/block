#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
应用启动脚本
提供多种启动选项，方便在不同环境中运行Flask应用
"""

import os
import sys
import subprocess
import time
import argparse

def print_banner():
    """打印启动横幅"""
    banner = """
    ==================================
    |       Flask应用启动工具        |
    |       支持多种运行模式         |
    ==================================
    """
    print(banner)

def check_requirements():
    """检查基本依赖是否安装"""
    try:
        import flask
        return True
    except ImportError:
        print("错误: 未安装Flask。请先运行 'pip install -r requirements.txt'")
        return False

def install_dependencies():
    """安装项目依赖"""
    print("正在安装项目依赖...")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        print("依赖安装成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"依赖安装失败: {str(e)}")
        return False

def start_development():
    """启动开发服务器"""
    print("\n正在启动开发服务器...")
    print("注意: 此模式仅适用于开发环境，生产环境请使用WSGI服务器")
    
    # 设置开发环境变量
    os.environ['FLASK_ENV'] = 'development'
    os.environ['FLASK_APP'] = 'app.py'
    
    try:
        # 使用Flask内置开发服务器
        subprocess.call([sys.executable, 'app.py'])
    except KeyboardInterrupt:
        print("\n开发服务器已停止")

def start_with_gunicorn():
    """使用Gunicorn启动应用（推荐生产环境）"""
    print("\n正在使用Gunicorn启动应用...")
    
    # 检查Gunicorn是否安装
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'show', 'gunicorn'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError:
        print("Gunicorn未安装，正在安装...")
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'gunicorn'])
        except subprocess.CalledProcessError:
            print("Gunicorn安装失败，请手动安装")
            return
    
    # 设置生产环境变量
    os.environ['FLASK_ENV'] = 'production'
    
    # 配置Gunicorn参数
    workers = 2  # 工作进程数，可根据CPU核心数调整
    threads = 4  # 每个工作进程的线程数
    port = 5000  # 监听端口
    
    print(f"Gunicorn配置: {workers}个工作进程，每个进程{threads}个线程，监听端口{port}")
    
    try:
        # 启动Gunicorn
        cmd = [
            'gunicorn',
            f'--workers={workers}',
            f'--threads={threads}',
            f'--bind=0.0.0.0:{port}',
            'wsgi:application'
        ]
        
        print(f"执行命令: {' '.join(cmd)}")
        subprocess.call(cmd)
    except KeyboardInterrupt:
        print("\nGunicorn服务器已停止")

def start_test_mode():
    """启动测试模式（运行部署测试脚本）"""
    print("\n正在运行部署测试...")
    
    if os.path.exists('test_deploy.py'):
        try:
            subprocess.call([sys.executable, 'test_deploy.py'])
        except KeyboardInterrupt:
            print("\n测试已中断")
    else:
        print("错误: 测试脚本test_deploy.py不存在")

def main():
    """主函数"""
    print_banner()
    
    # 检查Python版本
    if sys.version_info < (3, 6):
        print("错误: 需要Python 3.6或更高版本")
        sys.exit(1)
    
    # 创建参数解析器
    parser = argparse.ArgumentParser(description='Flask应用启动工具')
    parser.add_argument('--mode', choices=['dev', 'prod', 'test', 'install'], 
                        help='启动模式: dev(开发), prod(生产), test(测试), install(安装依赖)')
    
    args = parser.parse_args()
    
    # 根据模式选择操作
    if args.mode == 'install' or not check_requirements():
        install_dependencies()
        return
    
    if args.mode == 'dev' or not args.mode:
        start_development()
    elif args.mode == 'prod':
        start_with_gunicorn()
    elif args.mode == 'test':
        start_test_mode()


if __name__ == '__main__':
    main()

# 使用说明:
# 1. 安装依赖: python start_app.py --mode install
# 2. 开发模式: python start_app.py --mode dev
# 3. 生产模式(Gunicorn): python start_app.py --mode prod
# 4. 运行部署测试: python start_app.py --mode test
# 5. 默认模式(开发): python start_app.py