# store/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('movies/', views.movie_list, name='movie_list'),
    path('movies/<int:pk>/', views.movie_detail, name='movie_detail'),
    path('reviews/<int:pk>/edit/', views.review_edit, name='review_edit'),
    path('reviews/<int:pk>/delete/', views.review_delete, name='review_delete'),
    path('cart/', views.cart_view, name='cart'),
    path('add-to-cart/<int:movie_id>/', views.add_to_cart, name='add_to_cart'),
    path('remove-from-cart/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('orders/', views.order_list, name='order_list'),
    
    # Movie Petition URLs - User Story #21
    path('petitions/', views.petition_list, name='petition_list'),
    path('petitions/create/', views.create_petition, name='create_petition'),
    path('petitions/<int:pk>/', views.petition_detail, name='petition_detail'),
    path('petitions/<int:pk>/vote/', views.vote_petition, name='vote_petition'),
    path('my-petitions/', views.my_petitions, name='my_petitions'),
]