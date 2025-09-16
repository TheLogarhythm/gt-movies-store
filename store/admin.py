# store/admin.py
from django.contrib import admin
from .models import Movie, Review, Order, OrderItem, ReviewLike

@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ['title', 'price', 'created_at']
    list_filter = ['created_at']
    search_fields = ['title']
    ordering = ['title']

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['user', 'movie', 'rating', 'likes', 'created_at', 'is_top_comment_display']
    list_filter = ['rating', 'created_at', 'likes']
    search_fields = ['user__username', 'movie__title', 'content']
    readonly_fields = ['likes', 'created_at', 'updated_at']
    ordering = ['-likes', '-created_at']
    
    def is_top_comment_display(self, obj):
        """显示是否为热门评论"""
        return obj.is_top_comment
    is_top_comment_display.boolean = True
    is_top_comment_display.short_description = 'Top Comment'

    def get_queryset(self, request):
        """优化查询性能"""
        return super().get_queryset(request).select_related('user', 'movie')

@admin.register(ReviewLike)
class ReviewLikeAdmin(admin.ModelAdmin):
    list_display = ['user', 'review_movie', 'review_user', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'review__movie__title', 'review__user__username']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
    
    def review_movie(self, obj):
        """显示被点赞评论的电影"""
        return obj.review.movie.title
    review_movie.short_description = 'Movie'
    
    def review_user(self, obj):
        """显示被点赞评论的作者"""
        return obj.review.user.username
    review_user.short_description = 'Review Author'

    def get_queryset(self, request):
        """优化查询性能"""
        return super().get_queryset(request).select_related('user', 'review__user', 'review__movie')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'total_amount', 'items_count', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
    
    def items_count(self, obj):
        """显示订单项目数量"""
        return obj.items.count()
    items_count.short_description = 'Items Count'

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'movie', 'quantity', 'price', 'subtotal_display', 'order_date']
    list_filter = ['order__created_at', 'movie__title']
    search_fields = ['order__user__username', 'movie__title']
    ordering = ['-order__created_at']
    
    def subtotal_display(self, obj):
        """显示小计"""
        return f"${obj.subtotal():.2f}"
    subtotal_display.short_description = 'Subtotal'
    
    def order_date(self, obj):
        """显示订单日期"""
        return obj.order.created_at.strftime('%Y-%m-%d')
    order_date.short_description = 'Order Date'

# 自定义管理界面标题
admin.site.site_header = "GT Movies Store Administration"
admin.site.site_title = "GT Movies Store Admin"
admin.site.index_title = "Welcome to GT Movies Store Administration"