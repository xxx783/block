from app import app, db
from app import User
import datetime

with app.app_context():
    user = User.query.filter_by(username='admin').first()
    print(f'用户名: {user.username}')
    print(f'is_vip: {user.is_vip}')
    print(f'vip_level: {user.vip_level}')
    print(f'vip_expires_at: {user.vip_expires_at}')
    # 检查当前时间和有效期的比较
    if user.vip_expires_at:
        current_time = datetime.datetime.now(datetime.timezone.utc)
        if user.vip_expires_at.tzinfo is None:
            vip_expires_at_utc = user.vip_expires_at.replace(tzinfo=datetime.timezone.utc)
        else:
            vip_expires_at_utc = user.vip_expires_at
        print(f'会员是否有效: {vip_expires_at_utc > current_time}')