from django.urls import path
from . import views

app_name = "particles"

urlpatterns = [
    path('', views.ParticlesTable.as_view(), name='particles_main'),
    path('assembly/<int:pk>/', views.AssemblyDetailView.as_view(), name='assembly_detail'),
    path('export/', views.export_assemblies_to_excel, name='export_assemblies'),

    # Основной эндпоинт с детальной статистикой (рекомендуется)
    path('partially_picked_assemblies/',
         views.ReceivePartiallyPickedAssembliesView.as_view(),
         name='receive-partially-picked'),

    # Получение данных
    path('partially_picked_list/',
         views.PartiallyPickedAssembliesListView.as_view(),
         name='list-partially-picked'),

    # Статистика
    path('today_stats/',
         views.TodayStatsView.as_view(),
         name='today-stats'),
]
