# WSGI入口点文件
# 用于uWSGI、Gunicorn等WSGI服务器部署Flask应用

from app import app

# 应用实例，WSGI服务器将导入这个变量
def application(environ, start_response):
    """
    WSGI应用入口函数
    
    Args:
        environ: 包含CGI环境变量的字典
        start_response: 用于开始HTTP响应的回调函数
        
    Returns:
        响应体的可迭代对象
    """
    return app(environ, start_response)

# 如果直接运行此文件（非通过WSGI服务器），则以开发模式启动应用
if __name__ == '__main__':
    # 注意：在生产环境中，应通过WSGI服务器运行，而不是直接运行此文件
    app.run(debug=False, host='0.0.0.0', port=5000)

# 配置说明：
# 1. 对于Gunicorn，使用命令：gunicorn --bind 0.0.0.0:5000 wsgi:application
# 2. 对于uWSGI，使用命令：uwsgi --http 0.0.0.0:5000 --wsgi-file wsgi.py --callable application
# 3. 对于虚拟主机控制面板（如cPanel、Plesk），设置启动文件为wsgi.py，入口点为application

# 生产环境建议：
# - 关闭debug模式
# - 使用多进程和多线程以提高性能
# - 配置适当的超时时间
# - 配置日志记录