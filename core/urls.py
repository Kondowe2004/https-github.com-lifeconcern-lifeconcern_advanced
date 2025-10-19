from django.urls import path
from django.http import HttpResponse
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # -------------------- Dashboard --------------------
    path('', views.dashboard, name='dashboard'),

    # -------------------- Projects --------------------
    path('projects/', views.projects, name='projects'),
    path('projects/add/', views.project_add, name='project_add'),
    path('projects/<int:pk>/', views.project_detail, name='project_detail'),
    path('projects/<int:pk>/edit/', views.project_edit, name='project_edit'),
    path('projects/<int:pk>/delete/', views.project_delete, name='project_delete'),
    path('projects/<int:pk>/kpis/', views.project_kpis, name='project_kpis'),
    path('projects/<int:pk>/bulk-save/', views.bulk_save_entries, name='bulk_save_entries'),

    # Project KPI Bulk Actions
    path('projects/<int:project_id>/bulk-action/', views.project_bulk_action, name='project_bulk_action'),

    # -------------------- Indicators --------------------
    path('projects/<int:project_pk>/indicators/add/', views.indicator_add, name='indicator_add'),
    path('projects/<int:project_pk>/indicators/<int:pk>/edit/', views.indicator_edit, name='indicator_edit'),
    path('projects/<int:project_pk>/indicators/<int:pk>/delete/', views.indicator_delete, name='indicator_delete'),

    # Edit indicator targets
    path('indicators/<int:indicator_id>/targets/edit/', views.edit_indicator_targets, name='edit_indicator_targets'),

    # -------------------- Project Exports --------------------
    path('projects/<int:pk>/export/csv/', views.export_project_kpis, name='export_project_kpis'),
    path('projects/<int:pk>/export/excel/', views.export_project_kpis_excel, name='export_project_kpis_excel'),

    # -------------------- Reports --------------------
    path('reports/', views.reports, name='reports'),
    path('reports/export/', views.reports_export_csv, name='reports_export_csv'),
    path('actual-vs-variance/', views.actual_vs_variance_report, name='actual_vs_variance'),
    path('reports/more/', views.more_reports, name='more_reports'),
    path('reports/more/export/csv/', views.more_reports_export_csv, name='more_reports_export_csv'),
    path('reports/more/export/excel/', views.more_reports_export_excel, name='more_reports_export_excel'),
    path('reports/more/export/pdf/', views.more_reports_pdf, name='more_reports_pdf'),
    path('reports/more/filter/data/', views.pivot_filter_data_json, name='pivot_filter_data_json'),
    path('reports/more/monthly-trend/', views.monthly_trend_report, name='monthly_trend_report'),
    path('reports/monthly-performance/', views.monthly_performance_report, name='monthly_performance_report'),

    # -------------------- Profile --------------------
    path('profile/', views.profile, name='profile'),

    # -------------------- Data Story Dashboard --------------------
    path('data-story/', views.data_story, name='data_story'),
    path('data-story/gender-insights/', views.gender_insights, name='gender_insights'),
    path('data-story/gender-insights/download-excel/', views.download_gender_excel, name='download_gender_excel'),

    # -------------------- Facilities Map & CRUD --------------------
    path('facilities/map/', views.facilities_map, name='facilities_map'),
    path('facilities/<int:pk>/delete/', views.facility_delete, name='facility_delete'),

    # -------------------- Donors --------------------
    path('donors/', views.donors_list, name='donors_list'),
    path('donors/add/', views.donor_add, name='donor_add'),
    path('donors/<int:donor_id>/', views.donor_detail, name='donor_detail'),
    path('donors/<int:donor_id>/edit/', views.donor_edit, name='donor_edit'),
    path('donors/<int:donor_id>/delete/', views.donor_delete, name='donor_delete'),

    # -------------------- Authentication --------------------
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='registration/logged_out.html'), name='logout'),
]

# -------------------- Service Worker (Prevents 404 Error) --------------------
def service_worker(request):
    """
    Handles requests for /service-worker.js to prevent 404 errors in console.
    You can later replace this with a real PWA service worker if needed.
    """
    return HttpResponse(
        "// Placeholder Service Worker — no caching active\n",
        content_type="application/javascript"
    )

urlpatterns += [
    path("service-worker.js", service_worker, name="service-worker"),
]
