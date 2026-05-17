# bookings/forms.py

from datetime import datetime as dt

from django import forms
from django.utils import timezone
from .models import Booking, Room

DAYS_CHOICES = [
    ('0', 'จันทร์'),
    ('1', 'อังคาร'),
    ('2', 'พุธ'),
    ('3', 'พฤหัสบดี'),
    ('4', 'ศุกร์'),
]

class BookingForm(forms.ModelForm):
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
        label='วันที่จอง',
    )
    start_time_only = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-input'}),
        label='เวลาเริ่มต้น',
    )
    end_time_only = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-input'}),
        label='เวลาสิ้นสุด',
    )
    days_of_week = forms.MultipleChoiceField(
        choices=DAYS_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'day-checkbox'}),
        required=False,
        label='วันที่ต้องการจอง',
    )

    def __init__(self, *args, **kwargs):
        self.room = kwargs.pop('room', None)
        super().__init__(*args, **kwargs)

    class Meta:
        model = Booking
        fields = [
            'objective_type',
            'purpose',
            'class_code', 'class_name', 'curriculum',
            'training_topic',
            'is_recurring', 'recurring_end_date', 'days_of_week',
        ]
        widgets = {
            'objective_type': forms.Select(attrs={
                'class': 'form-input',
                'id': 'id_objective_type',
            }),
            'purpose': forms.Textarea(attrs={
                'rows': 4,
                'class': 'form-input',
                'placeholder': 'ระบุวัตถุประสงค์ในการใช้งานห้องประชุม...',
            }),
            'class_code': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'เช่น CS101',
            }),
            'class_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'เช่น Introduction to Computer Science',
            }),
            'curriculum': forms.Select(attrs={
                'class': 'form-input',
            }),
            'training_topic': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'ระบุหัวข้อการอบรม/ติว',
            }),
            'is_recurring': forms.CheckboxInput(attrs={
                'id': 'id_is_recurring',
            }),
            'recurring_end_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-input',
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        objective_type = cleaned_data.get('objective_type')
        is_recurring = cleaned_data.get('is_recurring')

        # Every booking is single-day: end_date always equals start_date
        s_date = cleaned_data.get('start_date')
        s_time = cleaned_data.get('start_time_only')
        e_time = cleaned_data.get('end_time_only')

        start_time = None
        end_time = None
        if s_date and s_time:
            start_time = timezone.make_aware(dt.combine(s_date, s_time))
            cleaned_data['start_time'] = start_time
        if s_date and e_time:
            end_time = timezone.make_aware(dt.combine(s_date, e_time))
            cleaned_data['end_time'] = end_time

        if start_time and end_time:
            if start_time >= end_time:
                raise forms.ValidationError("เวลาเริ่มต้นต้องมาก่อนเวลาสิ้นสุด")

            # Conflict check only for single bookings; recurring conflicts checked in view
            if self.room and not is_recurring:
                conflicts = Booking.objects.filter(
                    room=self.room,
                    status__in=['Pending', 'Approved'],
                    start_time__lt=end_time,
                    end_time__gt=start_time,
                )
                if conflicts.exists():
                    conflict = conflicts.first()
                    raise forms.ValidationError(
                        f"ไม่สามารถจองได้ ห้องนี้มีการจองทับซ้อนในช่วง "
                        f"{conflict.start_time.strftime('%d/%m/%Y %H:%M')} – "
                        f"{conflict.end_time.strftime('%H:%M')} น. "
                        f"(สถานะ: {conflict.get_status_display()})"
                    )

        if objective_type == 'TEACHING':
            if not cleaned_data.get('class_code'):
                self.add_error('class_code', 'กรุณากรอกรหัสวิชา')
            if not cleaned_data.get('class_name'):
                self.add_error('class_name', 'กรุณากรอกชื่อวิชา')
            if not cleaned_data.get('curriculum'):
                self.add_error('curriculum', 'กรุณาเลือกหลักสูตร')

        if objective_type == 'TRAINING':
            if not cleaned_data.get('training_topic'):
                self.add_error('training_topic', 'กรุณากรอกหัวข้ออบรม')

        if is_recurring:
            if not cleaned_data.get('days_of_week'):
                self.add_error('days_of_week', 'กรุณาเลือกอย่างน้อยหนึ่งวัน')
            recurring_end_date = cleaned_data.get('recurring_end_date')
            if not recurring_end_date:
                self.add_error('recurring_end_date', 'กรุณาระบุวันสิ้นสุด')
            elif start_time and recurring_end_date <= start_time.date():
                self.add_error('recurring_end_date', 'วันสิ้นสุดต้องอยู่หลังวันเริ่มต้น')

        return cleaned_data

class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ['name', 'room_code', 'description', 'capacity', 'location', 'room_type', 'image', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'ชื่อห้อง (เช่น ห้องประชุม 1)'}),
            'room_code': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'รหัสห้อง (ถ้ามี)'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': 'รายละเอียดห้อง...'}),
            'capacity': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': 'จำนวนความจุ (คน)'}),
            'location': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'สถานที่ (เช่น ชั้น 1 อาคารเรียนรวม)'}),
            'room_type': forms.Select(attrs={'class': 'form-input'}),
            'image': forms.FileInput(attrs={'class': 'form-input', 'accept': 'image/*'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }
