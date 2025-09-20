# MySQL数据库配置指南

本指南将帮助您配置和连接到MySQL数据库，解决在连接过程中可能遇到的问题。

## 目录
- [检查MySQL服务运行状态](#检查mysql服务运行状态)
- [验证数据库用户和权限](#验证数据库用户和权限)
- [创建数据库和表结构](#创建数据库和表结构)
- [运行应用程序](#运行应用程序)
- [常见问题及解决方案](#常见问题及解决方案)
- [备份和恢复数据](#备份和恢复数据)

## 检查MySQL服务运行状态

### Windows系统
1. 按下 `Win + R` 键，输入 `services.msc` 并按回车
2. 在服务列表中找到 `MySQL` 或 `MariaDB` 服务
3. 确保服务状态为 "正在运行"
4. 如果未运行，右键点击服务并选择 "启动"

### 命令行检查
打开命令提示符（CMD）并执行以下命令：
```cmd
net start | findstr /i mysql
```
如果显示服务名称，则表示MySQL服务正在运行。

## 验证数据库用户和权限

### 使用MySQL命令行工具
1. 打开命令提示符（CMD）
2. 输入以下命令连接到MySQL服务器：
   ```cmd
   mysql -u mggp84017 -p
   ```
3. 输入密码：`NCLH1KJmgEvo`
4. 如果连接成功，您将看到MySQL提示符

### 检查数据库访问权限
在MySQL提示符下，执行以下命令检查用户权限：
```sql
SHOW GRANTS FOR 'mggp84017'@'localhost';
```
确保用户至少有 `SELECT`, `INSERT`, `UPDATE`, `DELETE`, `CREATE`, `ALTER` 等权限。

## 创建数据库和表结构

### 方法一：使用提供的初始化脚本
1. 确保MySQL服务正在运行
2. 打开命令提示符，导航到项目目录
3. 执行以下命令运行初始化脚本：
   ```cmd
   python init_mysql_db.py
   ```
4. 如果成功，您将看到 `✅ 数据库表创建成功!` 的消息

### 方法二：手动创建数据库
如果自动脚本失败，您可以尝试手动创建数据库：
1. 连接到MySQL服务器（使用上述方法）
2. 执行以下SQL命令创建数据库：
   ```sql
   CREATE DATABASE IF NOT EXISTS mggp84017 CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   USE mggp84017;
   ```
3. 然后再次运行初始化脚本创建表结构

## 运行应用程序

1. 确保数据库配置正确（已在app.py中设置）
2. 打开命令提示符，导航到项目目录
3. 执行以下命令启动应用程序：
   ```cmd
   python app.py
   ```
4. 如果一切正常，您将看到应用程序启动的消息

## 常见问题及解决方案

### 1. 访问被拒绝错误（Access denied）
**错误信息**：
```
(pymysql.err.OperationalError) (1045, "Access denied for user 'mggp84017'@'localhost' (using password: YES)")
```

**解决方案**：
- 确认用户名和密码是否正确
- 确认用户是否有足够的权限访问数据库
- 尝试重置用户密码：
  ```sql
  ALTER USER 'mggp84017'@'localhost' IDENTIFIED BY 'NCLH1KJmgEvo';
  FLUSH PRIVILEGES;
  ```

### 2. 无法连接到MySQL服务器
**错误信息**：
```
(pymysql.err.OperationalError) (2003, "Can't connect to MySQL server on 'localhost' ([WinError 10061] 由于目标计算机积极拒绝，无法连接。)")
```

**解决方案**：
- 确认MySQL服务是否正在运行
- 检查防火墙设置是否阻止了3306端口
- 确认MySQL配置是否允许本地连接

### 3. 数据库不存在
**错误信息**：
```
(pymysql.err.OperationalError) (1049, "Unknown database 'mggp84017'")
```

**解决方案**：
- 使用MySQL命令行工具手动创建数据库
- 确保app.py中的数据库名称与实际创建的数据库名称一致

### 4. 表结构不存在
**错误信息**：
```
(pymysql.err.ProgrammingError) (1146, "Table 'mggp84017.article' doesn't exist")
```

**解决方案**：
- 运行初始化脚本创建表结构：`python init_mysql_db.py`
- 检查脚本是否有错误输出

## 备份和恢复数据

### 备份数据库
打开命令提示符，执行以下命令：
```cmd
mysqldump -u mggp84017 -p mggp84017 > backup.sql
```
输入密码后，数据库将被备份到当前目录下的backup.sql文件中。

### 恢复数据库
```cmd
mysql -u mggp84017 -p mggp84017 < backup.sql
```

## 联系支持
如果您在配置过程中遇到任何问题，请记录详细的错误信息，并联系技术支持。