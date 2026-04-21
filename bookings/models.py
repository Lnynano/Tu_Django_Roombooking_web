# bookings/models.py

from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError

class Room(models.Model):
    ROOM_TYPE_CHOICES = [
        ('MEETING', 'ห้องประชุม'),
        ('CLASSROOM', 'ห้องเรียน'),
    ]

    name = models.CharField(max_length=100, verbose_name="ชื่อห้อง")
    room_code = models.CharField(max_length=20, verbose_name="รหัสห้อง", blank=True, null=True)
    description = models.TextField(blank=True, verbose_name="รายละเอียด")
    capacity = models.IntegerField(verbose_name="ความจุ (คน)")
    location = models.CharField(max_length=200, verbose_name="สถานที่")
    room_type = models.CharField(max_length=20, choices=ROOM_TYPE_CHOICES, default='MEETING', verbose_name="ประเภทห้อง")
    image = models.ImageField(upload_to='room_images/', blank=True, null=True, verbose_name="รูปภาพห้อง")
    is_active = models.BooleanField(default=True, verbose_name="เปิดใช้งาน")

    def __str__(self):
        return f"{self.room_code} - {self.name}" if self.room_code else self.name

    class Meta:
        verbose_name = "ห้อง"
        verbose_name_plural = "ห้อง"

class Booking(models.Model):
    OBJECTIVE_TYPE_CHOICES = [
        ('TEACHING', 'สอนปกติ/ชดเชย/เสริม'),
        ('TRAINING', 'จัดอบรม/จัดติว'),
        ('GENERAL', 'ใช้งานทั่วไป'),
    ]

    STATUS_CHOICES = [
        ('Pending', 'รอการอนุมัติ'),
        ('Approved', 'อนุมัติแล้ว'),
        ('Rejected', 'ปฏิเสธ'),
        ('Cancelled', 'ยกเลิก'),
    ]

    CURRICULUM_CHOICES = [
        ('BACHELOR_NORMAL', 'ปริญญาตรีภาคปกติ'),
        ('MASTER', 'ปริญญาโท'),
        ('TEP_TEPE', 'TEP-TEPE'),
        ('TU_PINE', 'TU-PINE'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookings', verbose_name="ผู้จอง")
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='bookings', verbose_name="ห้อง")
    
    # Core fields
    objective_type = models.CharField(max_length=20, choices=OBJECTIVE_TYPE_CHOICES, default='GENERAL', verbose_name="ประเภทวัตถุประสงค์")
    start_time = models.DateTimeField(verbose_name="เวลาเริ่มต้น")
    end_time = models.DateTimeField(verbose_name="เวลาสิ้นสุด")
    purpose = models.TextField(verbose_name="รายละเอียดวัตถุประสงค์")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending', verbose_name="สถานะ")
    
    # Recurring fields
    is_recurring = models.BooleanField(default=False, verbose_name="จองแบบรายสัปดาห์")
    recurring_end_date = models.DateField(null=True, blank=True, verbose_name="สิ้นสุดการจองรายสัปดาห์เมื่อ")
    days_of_week = models.JSONField(null=True, blank=True, verbose_name="วันที่ต้องการจอง (รายสัปดาห์)")
    
    # Teaching specific
    class_code = models.CharField(max_length=255, null=True, blank=True, verbose_name="รหัสวิชา")
    class_name = models.CharField(max_length=255, null=True, blank=True, verbose_name="ชื่อวิชา")
    curriculum = models.CharField(max_length=50, choices=CURRICULUM_CHOICES, null=True, blank=True, verbose_name="หลักสูตร")

    # Training specific
    training_topic = models.CharField(max_length=255, null=True, blank=True, verbose_name="หัวข้ออบรม")

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="สร้างเมื่อ")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="แก้ไขเมื่อ")
    admin_comment = models.TextField(blank=True, null=True, verbose_name="ความเห็นจากผู้ดูแล")

    def __str__(self):
        return f"{self.user.first_name} - {self.room.name} ({self.start_time.strftime('%d/%m/%Y %H:%M')})"

    def clean(self):
        # Validate datetime order
        if self.start_time and self.end_time:
            if self.start_time >= self.end_time:
                raise ValidationError("เวลาสิ้นสุดต้องอยู่หลังเวลาเริ่มต้น")

        # Validate teaching fields
        if self.objective_type == 'TEACHING':
            if not self.class_code or not self.class_name or not self.curriculum:
                raise ValidationError("กรุณากรอกข้อมูล รหัสวิชา, ชื่อวิชา และหลักสูตร สำหรับการจองเพื่อการสอน")

        # Validate training fields
        if self.objective_type == 'TRAINING':
            if not self.training_topic:
                raise ValidationError("กรุณากรอกหัวข้ออบรม สำหรับการจองเพื่อจัดอบรม")

        # Validate recurring fields
        if self.is_recurring:
            if not self.days_of_week or not self.recurring_end_date:
                raise ValidationError("กรุณาระบุวันที่ต้องการจองและวันสิ้นสุด สำหรับการจองรายสัปดาห์")

    class Meta:
        verbose_name = "การจอง"
        verbose_name_plural = "การจอง"
