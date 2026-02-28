from django.urls import path
from . import views


urlpatterns = [
    path('efootball/', views.EfootballListCreateView.as_view(), name='efootball-list-create'),
    path('efootball/bulk/', views.EfootballBulkCreateView.as_view(), name='efootball-bulk-create'),
    path('efootball/<int:pk>/', views.EfootbalDetailView.as_view(), name='efootball-detail'),
    path('efootball/bulk/update/', views.EfootballBulkUpdateView.as_view(), name='efootball-bulk-update'),
    path('efootball/bulk/delete/', views.EfootballBulkDeleteView.as_view(), name='efootball-bulk-delete'),

]