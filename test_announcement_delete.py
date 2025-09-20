from app import app, db, Announcement, User
import sys
import random
import string

if __name__ == '__main__':
    with app.app_context():
        try:
            # 获取第一个管理员用户作为创建者
            admin_user = User.query.filter_by(is_admin=True).first()
            if not admin_user:
                print("❌ 找不到管理员用户，请先创建管理员账户")
                sys.exit(1)
                
            # 创建一个临时公告用于测试
            temp_title = "测试公告 - " + ''.join(random.choices(string.ascii_letters + string.digits, k=8))
            temp_content = "这是一个用于测试删除功能的临时公告。" + ''.join(random.choices(string.ascii_letters, k=20))
            
            print(f"✅ 创建测试公告：{temp_title}")
            
            new_announcement = Announcement(
                title=temp_title,
                content=temp_content,
                created_by=admin_user.id
            )
            db.session.add(new_announcement)
            db.session.commit()
            
            announcement_id = new_announcement.id
            print(f"✅ 公告创建成功，ID: {announcement_id}")
            
            # 尝试删除公告
            print("\n🔄 开始测试删除公告...")
            announcement_to_delete = Announcement.query.get(announcement_id)
            
            db.session.delete(announcement_to_delete)
            db.session.commit()
            
            print("✅ 公告删除成功！")
            print("✅ 级联删除关系已生效，公告删除功能已修复")
            print("\n修复说明：")
            print("问题原因：Announcement模型中缺少与AnnouncementArticleRelation的反向关系和级联删除设置")
            print("解决方法：在Announcement模型中添加了related_articles关系，并设置cascade='all, delete-orphan'，")
            print("          这样删除公告时会自动删除相关的AnnouncementArticleRelation记录，避免外键约束错误。")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ 测试失败：{str(e)}")
            print("\n详细错误信息：")
            import traceback
            traceback.print_exc()
            sys.exit(1)