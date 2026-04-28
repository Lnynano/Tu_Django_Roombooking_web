# bookings/forms.py

from django import forms
from .models import Booking, Room

class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['start_time', 'end_time', 'purpose']
        widgets = {
            'start_time': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-input'
            }),
            'end_time': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-input'
            }),
            'purpose': forms.Textarea(attrs={
                'rows': 4,
                'class': 'form-input',
                'placeholder': 'ระบุวัตถุประสงค์ในการใช้งานห้องประชุม...'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')

        if start_time and end_time:
            if start_time >= end_time:
                raise forms.ValidationError("เวลาเริ่มต้นต้องมาก่อนเวลาสิ้นสุด")
        
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
