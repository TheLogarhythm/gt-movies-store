from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('movies/', views.movie_list, name='movie_list'),
    path('movie/<int:pk>/', views.movie_detail, name='movie_detail'),
    path('cart/', views.cart_view, name='cart'),
    path('add-to-cart/<int:movie_id>/', views.add_to_cart, name='add_to_cart'),
    path('remove-from-cart/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('orders/', views.order_list, name='order_list'),
    path('review/<int:pk>/edit/', views.review_edit, name='review_edit'),
    path('review/<int:pk>/delete/', views.review_delete, name='review_delete'),

    # 新增的URL路由
    path('top-comments/', views.top_comments, name='top_comments'),
    path('funny-users/', views.funny_users, name='funny_users'),
    path('like-review/<int:review_id>/', views.like_review, name='like_review'),
]