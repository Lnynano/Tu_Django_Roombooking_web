import csv
import calendar
from datetime import datetime, date
from django.utils import timezone
from django.shortcuts import render
from django.views.generic import View
from django.db.models import Count, Q
from django.db.models.functions import TruncDate, TruncMonth, TruncYear
from django.http import HttpResponse
from django.contrib.auth.mixins import UserPassesTestMixin

from bookings.models import Booking, Room

class IsAdminMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == 'Admin'

class ReportStatisticsView(IsAdminMixin, View):
    template_name = 'reports/statistics.html'

    def get(self, request, *args, **kwargs):
        # 1. All reservations (approved or not)
        base_qs = Booking.objects.all()

        # 2. Show reservations in years (e.g. 2022, 2023, 2024, etc., including 0)
        current_year = timezone.now().year
        all_years = list(range(2022, current_year + 2))
        yearly_dict = {str(y): 0 for y in all_years}
        
        yearly_qs = base_qs.annotate(
            year=TruncYear('start_time')
        ).values('year').annotate(
            total=Count('id')
        ).order_by('year')

        for item in yearly_qs:
            if item['year']:
                y_str = str(item['year'].year)
                if y_str in yearly_dict:
                    yearly_dict[y_str] += item['total']
                else:
                    yearly_dict[y_str] = item['total']
        
        yearly_stats = [{'year': k, 'total': v} for k, v in sorted(yearly_dict.items())]

        # 3. Show reservations by month (select specific year)
        filter_year = request.GET.get('filter_year')
        monthly_stats = []
        if filter_year:
            try:
                y = int(filter_year)
                m_qs = base_qs.filter(start_time__year=y).annotate(
                    month=TruncMonth('start_time')
                ).values('month').annotate(
                    total=Count('id')
                ).order_by('month')
                
                month_dict = {str(m): 0 for m in range(1, 13)}
                for item in m_qs:
                    if item['month']:
                        m_str = str(item['month'].month)
                        month_dict[m_str] += item['total']
                
                monthly_stats = [{'month': k, 'total': v} for k, v in month_dict.items()]
            except ValueError:
                pass

        # 4. Show reservations in days (select specific month)
        filter_month = request.GET.get('filter_month') # format YYYY-MM
        daily_stats = []
        if filter_month:
            try:
                m_year, m_month = filter_month.split('-')
                m_year = int(m_year)
                m_month = int(m_month)
                num_days = calendar.monthrange(m_year, m_month)[1]
                
                d_qs = base_qs.filter(start_time__year=m_year, start_time__month=m_month).annotate(
                    date=TruncDate('start_time')
                ).values('date').annotate(
                    total=Count('id')
                ).order_by('date')
                
                day_dict = {str(d): 0 for d in range(1, num_days + 1)}
                for item in d_qs:
                    if item['date']:
                        d_str = str(item['date'].day)
                        day_dict[d_str] += item['total']
                
                daily_stats = [{'day': k, 'total': v} for k, v in day_dict.items()]
            except ValueError:
                pass

        # 5. Reservations on one specific date: room from most to least reserved
        filter_date = request.GET.get('filter_date') # format YYYY-MM-DD
        specific_date_room_stats = []
        if filter_date:
            rooms = Room.objects.all()
            room_dict = {r.name: 0 for r in rooms}
            
            r_qs = base_qs.filter(start_time__date=filter_date).values(
                'room__name'
            ).annotate(
                total=Count('id')
            )
            for item in r_qs:
                if item['room__name'] in room_dict:
                    room_dict[item['room__name']] += item['total']
                    
            sorted_rooms = sorted(room_dict.items(), key=lambda x: x[1], reverse=True)
            specific_date_room_stats = [{'room': k, 'total': v} for k, v in sorted_rooms]

        # Breakdown by objective type
        OBJECTIVE_DISPLAY = {
            'TEACHING': 'สอนปกติ/ชดเชย/เสริม',
            'TRAINING': 'จัดอบรม/จัดติว',
            'GENERAL':  'ใช้งานทั่วไป',
        }
        total_bookings = base_qs.count()
        obj_qs = base_qs.values('objective_type').annotate(total=Count('id')).order_by('-total')
        objective_breakdown = []
        for item in obj_qs:
            obj_type = item['objective_type']
            count = item['total']
            pct = round(count / total_bookings * 100, 1) if total_bookings > 0 else 0
            objective_breakdown.append({
                'type': obj_type,
                'label': OBJECTIVE_DISPLAY.get(obj_type, obj_type),
                'total': count,
                'percentage': pct,
            })

        # Get list of all reservations to show in template
        all_reservations = base_qs.select_related('user', 'room').order_by('-start_time')

        context = {
            'yearly_stats': yearly_stats,
            'monthly_stats': monthly_stats,
            'daily_stats': daily_stats,
            'specific_date_room_stats': specific_date_room_stats,

            'objective_breakdown': objective_breakdown,
            'total_bookings': total_bookings,

            'filter_year': filter_year,
            'filter_month': filter_month,
            'filter_date': filter_date,

            'all_reservations': all_reservations,
        }

        return render(request, self.template_name, context)

class ExportStatisticsCSVView(IsAdminMixin, View):
    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="reservation_list.csv"'
        response.write(u'\ufeff'.encode('utf8')) # BOM for Excel

        writer = csv.writer(response)
        
        # --- 1. Breakdown by Usage Type (Objective Type) ---
        writer.writerow(['สรุปการจองแยกตามประเภทการใช้งาน (Usage Type Breakdown)'])
        writer.writerow(['ประเภท (Type)', 'จำนวน (Total)', 'สัดส่วน (Percentage)'])
        
        total_bookings = Booking.objects.count()
        obj_qs = Booking.objects.values('objective_type').annotate(total=Count('id')).order_by('-total')
        
        OBJECTIVE_DISPLAY = dict(Booking.OBJECTIVE_TYPE_CHOICES)
        
        for item in obj_qs:
            obj_type = item['objective_type']
            count = item['total']
            pct = round(count / total_bookings * 100, 1) if total_bookings > 0 else 0
            writer.writerow([
                OBJECTIVE_DISPLAY.get(obj_type, obj_type),
                f"{count} ครั้ง",
                f"{pct}%"
            ])
            
        writer.writerow([]) # Empty row for spacing
        writer.writerow([])
        
        # --- 2. List of All Reservation History ---
        writer.writerow(['รายการประวัติการจองทั้งหมด (All Reservation History)'])
        writer.writerow([
            'ID', 'ผู้จอง (User)', 'ห้อง (Room)', 'เวลาเริ่มต้น (Start Time)', 'เวลาสิ้นสุด (End Time)', 
            'ประเภท (Objective)', 'รายละเอียด (Purpose)', 'สถานะ (Status)', 'สร้างเมื่อ (Created At)'
        ])

        # All reservations
        bookings = Booking.objects.all().order_by('-start_time')
        
        for b in bookings:
            writer.writerow([
                b.id,
                f"{b.user.first_name} {b.user.last_name}",
                b.room.name if b.room else "N/A",
                timezone.localtime(b.start_time).strftime('%Y-%m-%d %H:%M') if b.start_time else "N/A",
                timezone.localtime(b.end_time).strftime('%Y-%m-%d %H:%M') if b.end_time else "N/A",
                b.get_objective_type_display(),
                b.purpose,
                b.get_status_display(),
                timezone.localtime(b.created_at).strftime('%Y-%m-%d %H:%M') if b.created_at else "N/A",
            ])

        return response
