from django.urls import path
from . import views

urlpatterns = [
    # Badilisha hii - tumia BetCRUDView badala ya CreateBetView
    path('bets/', views.BetCRUDView.as_view(), name='bet-crud'),
    
    # Hizi ni sawa
    path('bets/<str:game_id>/', views.BetDetailView.as_view(), name='bet-detail'),
    path('bets/<str:game_id>/approve/', views.BetApproveView.as_view(), name='bet-approve'),
    path('bets/filter/summary/', views.BetFilterView.as_view(), name='bet-filter'),
    path('bets/<str:game_id>/matches/', views.MatchCRUDView.as_view(), name='add-match'),
    path('matches/<int:match_id>/', views.MatchCRUDView.as_view(), name='match-detail'),
    path('balance/', views.AccountBalanceView.as_view(), name='balance-crud'),


    path('fixtures/', views.MatchFixtureListCreateView.as_view(), name='fixture-list-create'),
    path('fixtures/bulk/', views.MatchFixtureBulkCreateView.as_view(), name='fixture-bulk-create'),
    path('fixtures/<int:pk>/', views.MatchFixtureDetailView.as_view(), name='fixture-detail'),
    path('fixtures/bulk/update/', views.MatchFixtureBulkUpdateView.as_view(), name='fixture-bulk-update'),
    path('fixtures/bulk/delete/', views.MatchFixtureBulkDeleteView.as_view(), name='fixture-bulk-delete'),

]