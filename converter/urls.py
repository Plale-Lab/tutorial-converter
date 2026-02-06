from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('convert/', views.convert, name='convert'),
    path('logs/', views.logs, name='logs'),
    path('api/settings/', views.save_settings, name='save_settings'),
    path('api/index/', views.index_documents, name='index_documents'),
]
