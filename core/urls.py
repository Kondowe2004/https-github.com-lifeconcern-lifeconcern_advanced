from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Projects
    path('projects/', views.projects, name='projects'),
    path('projects/add/', views.project_add, name='project_add'),
    path('projects/<int:pk>/', views.project_detail, name='project_detail'),
    path('projects/<int:pk>/edit/', views.project_edit, name='project_edit'),
    path('projects/<int:pk>/delete/', views.project_delete, name='project_delete'),
    path('projects/<int:pk>/kpis/', views.project_kpis, name='project_kpis'),
    path('projects/<int:pk>/bulk-save/', views.bulk_save_entries, name='bulk_save_entries'),

    # ✅ KPI / Indicator routes (project-aware, consistent param names)
    path('projects/<int:project_pk>/indicators/add/', views.indicator_add, name='indicator_add'),
    path('projects/<int:project_pk>/indicators/<int:pk>/edit/', views.indicator_edit, name='indicator_edit'),
    path('projects/<int:project_pk>/indicators/<int:pk>/delete/', views.indicator_delete, name='indicator_delete'),

    # ✅ Project KPI Export
    path('projects/<int:pk>/export/csv/', views.export_project_kpis, name='export_project_kpis'),

    # Reports
    path('reports/', views.reports, name='reports'),
    path('reports/export/', views.reports_export_csv, name='reports_export_csv'),

    # ✅ (Optional future expansion: different export formats)
    # path('reports/export/excel/', views.reports_export_excel, name='reports_export_excel'),
    # path('reports/export/pdf/', views.reports_export_pdf, name='reports_export_pdf'),

    # Profile
    path('profile/', views.profile, name='profile'),
]
