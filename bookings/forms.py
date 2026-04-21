# bookings/forms.py

from django import forms
from .models import Booking

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
