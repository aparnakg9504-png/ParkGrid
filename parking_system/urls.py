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
    'parkgrid-admin/managers/',
    views.admin_managers,
    name='admin_managers'
),

path(
    'parkgrid-admin/managers/<int:user_id>/approve/',
    views.approve_manager,
    name='approve_manager'
),

path(
    'parkgrid-admin/managers/<int:user_id>/reject/',
    views.reject_manager,
    name='reject_manager'
),


path(
    'parkgrid-admin/users/',
    views.admin_users,
    name='admin_users'
),

path(
    'parkgrid-admin/users/<int:user_id>/approve/',
    views.approve_user,
    name='approve_user'
),

path(
    'parkgrid-admin/users/<int:user_id>/reject/',
    views.reject_user,
    name='reject_user'
),


    path(
        'parkgrid-admin/dashboard/',
        views.admin_dashboard,
        name='admin_dashboard'
    ),
   
    path(
    'parkgrid-admin/users/',
    views.admin_users,
    name='admin_users'
    ),
path(
    'parkgrid-admin/users/<int:user_id>/deactivate/',
    views.deactivate_user,
    name='deactivate_user'
),

path(
    'parkgrid-admin/users/<int:user_id>/activate/',
    views.activate_user,
    name='activate_user'
),

]