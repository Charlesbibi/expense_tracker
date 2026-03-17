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
    path('modal-debug/', views.modal_debug, name='modal_debug'),
    path('minimal-test/', views.minimal_test, name='minimal_test'),
    path('clean/', views.expense_list_clean, name='list_clean'),
    path('nocss/', views.nocss_test, name='nocss_test'),
    path('api/categories/', views.get_categories_api, name='api_categories'),
]
