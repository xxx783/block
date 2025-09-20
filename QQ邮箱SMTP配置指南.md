# QQ邮箱SMTP配置指南

## 问题原因
您遇到的"Connection unexpectedly closed"错误通常是由于以下原因：
1. 邮箱配置仍然是示例值（your-email@qq.com）
2. 授权码不正确或未获取
3. SMTP服务未开启
4. 网络连接问题

## 配置步骤

### 1. 获取QQ邮箱授权码
1. 登录QQ邮箱网页版 (mail.qq.com)
2. 点击顶部"设置" → "账户"
3. 找到"POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV服务"
4. 开启"POP3/SMTP服务"
5. 按照提示发送短信验证
6. 获取16位授权码（不是登录密码！）

### 2. 修改app.py配置文件
打开 `app.py` 文件，找到邮件配置部分（约第16-21行）：

```python
# 邮件配置
app.config['MAIL_SERVER'] = 'smtp.qq.com'  # QQ邮箱SMTP服务器
app.config['MAIL_PORT'] = 587  # QQ邮箱SMTP端口
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your-email@qq.com'  # 替换为您的QQ邮箱
app.config['MAIL_PASSWORD'] = 'your-authorization-code'  # 替换为QQ邮箱授权码
app.config['MAIL_ENABLED'] = True  # 开启邮件功能
```

**重要：** 将 `your-email@qq.com` 替换为您的QQ邮箱地址，将 `your-authorization-code` 替换为刚刚获取的16位授权码。

### 3. 开启邮件功能
确保 `MAIL_ENABLED` 设置为 `True`：
```python
app.config['MAIL_ENABLED'] = True  # 开启邮件功能
```

## 测试配置

### 方法1：使用测试脚本
创建一个测试文件 `test_email.py`：

```python
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# 您的配置信息
your_email = "your-email@qq.com"  # 替换为您的QQ邮箱
your_password = "your-authorization-code"  # 替换为授权码

# 创建邮件
msg = MIMEMultipart('alternative')
msg['Subject'] = '测试邮件'
msg['From'] = your_email
msg['To'] = your_email

# 添加内容
html_content = """
<html>
<body>
    <h2>这是一封测试邮件</h2>
    <p>如果收到此邮件，说明SMTP配置成功！</p>
</body>
</html>
"""
msg.attach(MIMEText(html_content, 'html'))

# 发送邮件
try:
    with smtplib.SMTP('smtp.qq.com', 587) as server:
        server.starttls()
        server.login(your_email, your_password)
        server.send_message(msg)
    print("✅ 测试邮件发送成功！")
except Exception as e:
    print(f"❌ 发送失败: {e}")
```

运行测试：
```bash
python test_email.py
```

### 方法2：在Flask中测试
注册一个新用户，系统会自动发送欢迎邮件。

## 常见问题解决

### 1. 连接被拒绝
- 检查网络连接
- 确认SMTP服务器和端口正确
- 确认邮箱授权码正确

### 2. 认证失败
- 确认使用的是授权码而不是登录密码
- 确认授权码没有过期

### 3. 连接意外关闭
- 尝试使用SSL连接（端口465）
- 检查防火墙设置

## 备用配置（如果587端口不行）
```python
app.config['MAIL_SERVER'] = 'smtp.qq.com'
app.config['MAIL_PORT'] = 465  # 使用SSL端口
app.config['MAIL_USE_SSL'] = True  # 启用SSL
app.config['MAIL_USE_TLS'] = False  # 禁用TLS
```

## 安全建议
1. 不要将真实的邮箱配置信息提交到版本控制系统
2. 可以考虑使用环境变量来存储敏感信息
3. 定期更新邮箱授权码

## 获取帮助
如果仍然遇到问题，可以：
1. 查看QQ邮箱官方帮助文档
2. 检查QQ邮箱的SMTP服务状态
3. 联系QQ邮箱客服

配置完成后，重启Flask服务器即可正常使用邮件功能！