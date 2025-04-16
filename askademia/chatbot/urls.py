from django.urls import path
from . import views

urlpatterns = [
    path('', views.chatbot_home, name='chatbot_home'),
    path('config/', views.chatbot_config, name='chatbot_config'),
    path('api/chat/', views.chat_api, name='chat_api'),
    path('embed-code/', views.embed_code, name='embed_code'),
    path('test/', views.chatbot_test, name='chatbot_test'),
    path('gaps/', views.knowledge_gaps, name='knowledge_gaps'),
    path('gaps/<int:gap_id>/resolve/', views.resolve_gap, name='resolve_gap'),
    path('widget/<str:username>/', views.chatbot_widget, name='chatbot_widget'),
]