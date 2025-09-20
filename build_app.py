import os
import sys
import shutil
import subprocess

# 打包辅助脚本，帮助正确打包应用程序

def ensure_dependencies():
    """确保所有依赖已安装"""
    print("===== 检查依赖项 =====")
    try:
        # 检查PyInstaller是否已安装
        import PyInstaller
        print("PyInstaller已安装")
    except ImportError:
        print("正在安装PyInstaller...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller'], check=True)
        print("PyInstaller安装成功")
    
    # 安装项目依赖
    print("正在安装项目依赖...")
    subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], check=True)
    print("项目依赖安装成功")

def backup_database():
    """备份数据库文件"""
    print("\n===== 备份数据库 =====")
    instance_dir = os.path.join(os.getcwd(), 'instance')
    if os.path.exists(instance_dir):
        # 创建备份目录
        backup_dir = os.path.join(os.getcwd(), 'db_backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        # 复制数据库文件到备份目录
        import datetime
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        
        for file in os.listdir(instance_dir):
            src = os.path.join(instance_dir, file)
            if os.path.isfile(src) and file.startswith('app.db'):
                dst = os.path.join(backup_dir, f"{file}.{timestamp}.bak")
                shutil.copy2(src, dst)
                print(f"已备份: {file} -> {os.path.basename(dst)}")
    else:
        print("警告: instance目录不存在，跳过数据库备份")

def clean_build_files():
    """清理之前的构建文件"""
    print("\n===== 清理构建文件 =====")
    build_dir = os.path.join(os.getcwd(), 'build')
    dist_dir = os.path.join(os.getcwd(), 'dist')
    
    # 删除build目录
    if os.path.exists(build_dir):
        shutil.rmtree(build_dir)
        print(f"已删除: {build_dir}")
    
    # 删除dist目录
    if os.path.exists(dist_dir):
        shutil.rmtree(dist_dir)
        print(f"已删除: {dist_dir}")
    
    # 删除.spec文件（除了优化版本）
    for file in os.listdir(os.getcwd()):
        if file.endswith('.spec') and file != 'app_optimized.spec':
            os.remove(os.path.join(os.getcwd(), file))
            print(f"已删除: {file}")

def build_with_pyinstaller():
    """使用PyInstaller和优化的spec文件打包应用"""
    print("\n===== 开始打包应用 =====")
    
    # 使用优化的spec文件打包
    cmd = [
        sys.executable,
        '-m', 'PyInstaller',
        'app_optimized.spec'
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print("打包成功！")
        
        # 打包完成后的操作
        final_setup()
        
    except subprocess.CalledProcessError as e:
        print(f"打包失败: {e}")
        print("请查看上面的错误信息，解决问题后重新运行此脚本")
        sys.exit(1)

def final_setup():
    """打包完成后的最终设置"""
    print("\n===== 完成最终设置 =====")
    
    # 检查dist目录是否存在
    dist_app_dir = os.path.join(os.getcwd(), 'dist', 'app')
    if os.path.exists(dist_app_dir):
        # 复制instance目录到dist/app目录（如果有数据库文件）
        source_instance = os.path.join(os.getcwd(), 'instance')
        target_instance = os.path.join(dist_app_dir, 'instance')
        
        if os.path.exists(source_instance) and os.listdir(source_instance):
            # 如果目标instance目录已存在则删除
            if os.path.exists(target_instance):
                shutil.rmtree(target_instance)
            # 复制instance目录
            shutil.copytree(source_instance, target_instance)
            print(f"已复制数据库文件到: {target_instance}")
        else:
            # 如果源instance目录为空或不存在，创建空的instance目录
            os.makedirs(target_instance, exist_ok=True)
            print(f"已创建空的instance目录: {target_instance}")
        
        # 创建运行脚本
        create_run_script(dist_app_dir)
        
        print("\n===== 打包完成！ =====")
        print(f"应用已打包到: {dist_app_dir}")
        print("运行方式:")
        print("1. 双击 dist/app/app.exe 直接运行")
        print("2. 或使用生成的运行脚本")
        print("\n注意事项:")
        print("- 确保app.exe与instance目录在同一文件夹下")
        print("- 如果遇到权限问题，尝试以管理员身份运行")
        print("- 查看运行指南.txt了解更多信息")

def create_run_script(dist_app_dir):
    """创建Windows批处理文件用于运行应用"""
    run_bat_path = os.path.join(dist_app_dir, '运行应用.bat')
    
    # 批处理文件内容
    bat_content = """@echo off

REM 运行应用的批处理脚本
cd /d %~dp0

REM 检查instance目录是否存在
if not exist "instance" (
    echo 创建instance目录...
    mkdir "instance"
)

REM 检查数据库文件是否存在
if not exist "instance\app.db" (
    echo 警告: 未找到数据库文件 instance\app.db
    echo 应用可能无法正常运行，请确保数据库文件已正确放置
    pause
)

REM 运行应用程序
echo 正在启动应用程序...
echo 请勿关闭此窗口，关闭此窗口将终止应用
echo.

app.exe

pause
"""
    
    with open(run_bat_path, 'w', encoding='utf-8') as f:
        f.write(bat_content)
    
    print(f"已创建运行脚本: {run_bat_path}")

def main():
    """主函数"""
    print("===== 应用打包辅助脚本 =====")
    
    try:
        # 1. 确保所有依赖已安装
        ensure_dependencies()
        
        # 2. 备份数据库
        backup_database()
        
        # 3. 清理之前的构建文件
        clean_build_files()
        
        # 4. 使用PyInstaller打包
        build_with_pyinstaller()
        
    except Exception as e:
        print(f"发生错误: {e}")
        import traceback
        traceback.print_exc()
        input("\n按Enter键退出...")
        sys.exit(1)

if __name__ == '__main__':
    main()