from django.urls import path
from . import views

app_name = 'bookings'

urlpatterns = [
    path('rooms/', views.room_list, name='room_list'),
    path('book/<int:room_id>/', views.book_room, name='book_room'),
    path('my-bookings/', views.my_bookings, name='my_bookings'),
    path('admin/approve/', views.admin_approve_list, name='admin_approve_list'),
    path('admin/approve/<int:booking_id>/<str:action>/', views.approve_booking, name='approve_booking'),
    
    # Room Management
    path('manage-rooms/', views.manage_rooms, name='manage_rooms'),
    path('manage-rooms/add/', views.add_room, name='add_room'),
    path('manage-rooms/<int:room_id>/edit/', views.edit_room, name='edit_room'),
    path('manage-rooms/<int:room_id>/delete/', views.delete_room, name='delete_room'),
]
