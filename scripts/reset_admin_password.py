#!/usr/bin/env python3
"""
سكربت لإعادة تعيين كلمة مرور الأدمن.
استخدام: python scripts/reset_admin_password.py
أو: python scripts/reset_admin_password.py 01012345678 123456789
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from routers.users_common import engine, hash_password

def main():
    if len(sys.argv) >= 3:
        phone = sys.argv[1].strip()
        new_password = sys.argv[2]
    else:
        phone = input("رقم تليفون الأدمن: ").strip()
        new_password = input("كلمة المرور الجديدة: ")

    if not phone or not new_password:
        print("خطأ: رقم التليفون وكلمة المرور مطلوبان")
        return

    hashed = hash_password(new_password)
    with engine.begin() as conn:
        r = conn.execute(
            text("UPDATE public.admins SET password = :pw WHERE phone_number = :pn"),
            {"pw": hashed, "pn": phone}
        )
        if r.rowcount == 0:
            print(f"لم يُعثر على أدمن برقم {phone}")
        else:
            print(f"تم تحديث كلمة المرور بنجاح لـ {phone}")

if __name__ == "__main__":
    main()
