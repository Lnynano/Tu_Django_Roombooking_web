from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('statistics/', views.ReportStatisticsView.as_view(), name='statistics'),
    path('export/csv/', views.ExportStatisticsCSVView.as_view(), name='export_csv'),
]
