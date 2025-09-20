from app import app, db, User, Article
import sys

if __name__ == '__main__':
    with app.app_context():
        try:
            # 测试修复后的查询
            articles = Article.query.join(User, Article.user_id == User.id).filter(User.is_banned == False).order_by(Article.created_at.desc()).all()
            
            print(f"✅ 查询成功！找到 {len(articles)} 篇文章")
            print("✅ AmbiguousForeignKeysError错误已修复")
            print("\n修复说明：")
            print("在Article模型和User模型之间有两个外键关系(user_id和reviewed_by)，")
            print("导致SQLAlchemy无法确定连接条件。通过在join()方法中显式指定连接条件\n"\n                  "Article.user_id == User.id，解决了这个问题。")
        except Exception as e:
            print(f"❌ 查询失败：{str(e)}")
            sys.exit(1)
        
        # 显示前5篇文章作为示例
        print("\n示例文章：")
        for i, article in enumerate(articles[:5]):
            print(f"{i+1}. {article.title} (作者: {article.author.username})")