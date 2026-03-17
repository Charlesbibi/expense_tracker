from django.urls import path
from . import views

app_name = 'expenses'

urlpatterns = [
    path('', views.home, name='home'),
    path('expenses/', views.expense_list, name='list'),
    path('add/', views.add_expense, name='add'),
    path('edit/<int:pk>/', views.edit_expense, name='edit'),
    path('category/add/', views.add_category, name='add_category'),
    path('delete/<int:pk>/', views.delete_expense, name='expense_delete'),
    path('visualizations/', views.visualizations, name='visualizations'),
    path('reports/', views.reports, name='reports'),
    path('api/categories/', views.get_categories_api, name='api_categories'),
]
