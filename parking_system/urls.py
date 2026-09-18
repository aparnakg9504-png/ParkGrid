from django.contrib import admin
from django.urls import path
from parking import views

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', views.home, name='home'),

    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),

    path('register/', views.register, name='register'),

    path(
        'user/dashboard/',
        views.user_dashboard,
        name='user_dashboard'
    ),
path(
    'parking-list/',
    views.parking_list,
    name='parking_list'
),


    path(
        'manager/dashboard/',
        views.manager_dashboard,
        name='manager_dashboard'
    ),

    path(
        'parkgrid-admin/dashboard/',
        views.admin_dashboard,
        name='admin_dashboard'
    ),
]