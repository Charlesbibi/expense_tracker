from django.urls import path
from . import views

app_name = 'expenses'

urlpatterns = [
    path('', views.home, name='home'),
    path('expenses/', views.expense_list, name='list'), # <-- 这个名字是 'list'
    path('add/', views.add_expense, name='add'),
    path('category/add/', views.add_category, name='add_category'),
    path('delete/<int:pk>/', views.delete_expense, name='expense_delete'),
    path('visualizations/', views.visualizations, name='visualizations'),
]
