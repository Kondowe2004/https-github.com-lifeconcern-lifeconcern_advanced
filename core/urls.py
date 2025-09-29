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

    # KPI / Indicator routes
    path('projects/<int:project_pk>/indicators/add/', views.indicator_add, name='indicator_add'),
    path('projects/<int:project_pk>/indicators/<int:pk>/edit/', views.indicator_edit, name='indicator_edit'),
    path('projects/<int:project_pk>/indicators/<int:pk>/delete/', views.indicator_delete, name='indicator_delete'),

    # Edit indicator targets
    path('indicators/<int:indicator_id>/targets/edit/', views.edit_indicator_targets, name='edit_indicator_targets'),

    # Project KPI Export
    path('projects/<int:pk>/export/csv/', views.export_project_kpis, name='export_project_kpis'),
    path('projects/<int:pk>/export/excel/', views.export_project_kpis_excel, name='export_project_kpis_excel'),

    # Reports
    path('reports/', views.reports, name='reports'),
    path('reports/export/', views.reports_export_csv, name='reports_export_csv'),

    # More Reports
    path('reports/more/', views.more_reports, name='more_reports'),
    path('reports/more/export/csv/', views.more_reports_export_csv, name='more_reports_export_csv'),
    path('reports/more/export/excel/', views.more_reports_export_excel, name='more_reports_export_excel'),
    path('reports/more/export/pdf/', views.more_reports_pdf, name='more_reports_pdf'),

    # --- AJAX endpoint for dynamic pivot/filter charts ---
    path('reports/more/filter/data/', views.pivot_filter_data_json, name='pivot_filter_data_json'),

    # Monthly Trend Report (new)
    path('reports/more/monthly-trend/', views.monthly_trend_report, name='monthly_trend_report'),

    # Monthly Performance Report
    path('reports/monthly-performance/', views.monthly_performance_report, name='monthly_performance_report'),

    # Profile
    path('profile/', views.profile, name='profile'),

    # Data Story Dashboard
    path('data-story/', views.data_story, name='data_story'),

    # Facilities Map & CRUD
    path('facilities/map/', views.facilities_map, name='facilities_map'),
    path('facilities/<int:pk>/delete/', views.facility_delete, name='facility_delete'),
    # path('facilities/<int:pk>/update/', views.facility_update, name='facility_update'),  # handled via AJAX
]
