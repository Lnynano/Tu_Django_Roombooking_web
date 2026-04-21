# TU ECE Room Booking System

ระบบจองห้องประชุม ภาควิชาวิศวกรรมไฟฟ้าและคอมพิวเตอร์ (TU ECE)

##  Docker Command Guide

ใช้สำหรับรันโปรเจกต์ผ่าน Docker

###  การเริ่มทำงาน (Start)
รันคำสั่งนี้เพื่อเริ่มระบบทั้งหมด (Django + PostgreSQL) ใน Background:
```bash
docker-compose up -d
```
*หมายเหตุ: หากมีการแก้ไข `requirements.txt` หรือ `Dockerfile` ให้ใช้ `--build` เพื่ออัปเดต Image:*
```bash
docker-compose up -d --build
```

###  การหยุดทำงาน (Stop)
หยุดการทำงานและลบ Container:
```bash
docker-compose down
```

###  การจัดการฐานข้อมูล (Database)
รันคำสั่งเหล่านี้หลังจากมีการแก้ไข `models.py`:

1. **สร้างไฟล์ Migration**:
   ```bash
   docker-compose exec web python manage.py makemigrations
   ```
2. **อัปเดตฐานข้อมูล**:
   ```bash
   docker-compose exec web python manage.py migrate
   ```

###  การจัดการผู้ใช้ (Users)
สร้างบัญชีผู้ดูแลระบบ (Admin) เพื่อเข้าหน้า [http://localhost:8000/admin](http://localhost:8000/admin):
```bash
docker-compose exec web python manage.py createsuperuser
```

###  การดู Logs
ดู Log การทำงานของระบบแบบ Real-time:
```bash
docker-compose logs -f web
```

---
**Note:** อย่าลืมตั้งค่าไฟล์ `.env` เพื่อให้ระบบเชื่อมต่อกับ TU REST API ได้
