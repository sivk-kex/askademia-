from django.urls import path
from . import views

urlpatterns = [
    path('', views.repository_home, name='repository_home'),
    path('folder/create/', views.create_folder, name='create_folder'),
    path('folder/<int:folder_id>/', views.folder_detail, name='folder_detail'),
    path('folder/<int:folder_id>/edit/', views.edit_folder, name='edit_folder'),
    path('folder/<int:folder_id>/delete/', views.delete_folder, name='delete_folder'),
    path('content/create/', views.create_content, name='create_content'),
    path('content/<int:content_id>/', views.content_detail, name='content_detail'),
    path('content/<int:content_id>/edit/', views.edit_content, name='edit_content'),
    path('content/<int:content_id>/delete/', views.delete_content, name='delete_content'),
]