from django.urls import path
from . import views
from django.views.decorators.cache import cache_page

app_name = "particles"

urlpatterns = [
    # path('', views.ParticlesTable.as_view(), name='particles_main'),
    path('', cache_page(60 * 1)(views.ParticlesTable.as_view()), name='particles_main'),

    path('assembly/<int:pk>/', views.AssemblyDetailView.as_view(), name='assembly_detail'),
    path('export/', views.export_assemblies_to_excel, name='export_assemblies'),

    # Основной эндпоинт с детальной статистикой (рекомендуется)
    path('partially_picked_assemblies/',
         views.ReceivePartiallyPickedAssembliesView.as_view(),
         name='receive-partially-picked'),
    path('statistics/', views.StatisticsDashboard.as_view(), name='statistics_dashboard'),
    path('statistics/api/', views.StatisticsAPIView.as_view(), name='statistics_api'),
    path('statistics/export/', views.StatisticsExportView.as_view(), name='statistics_export'),
]
