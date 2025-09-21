# store/admin.py
from django.contrib import admin
from .models import Movie, Review, Order, OrderItem, MoviePetition, PetitionVote

@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ['title', 'price', 'created_at']
    list_filter = ['created_at']
    search_fields = ['title']
    ordering = ['title']

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['user', 'movie', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['user__username', 'movie__title']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'total_amount', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username']

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'movie', 'quantity', 'price']
    list_filter = ['order__created_at']

@admin.register(MoviePetition)
class MoviePetitionAdmin(admin.ModelAdmin):
    list_display = ['movie_title', 'creator', 'status', 'total_votes', 'yes_votes', 'created_at']
    list_filter = ['status', 'created_at', 'genre']
    search_fields = ['movie_title', 'creator__username', 'director']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    def total_votes(self, obj):
        return obj.total_votes()
    total_votes.short_description = 'Total Votes'
    
    def yes_votes(self, obj):
        return f"{obj.yes_votes()} ({obj.yes_percentage()}%)"
    yes_votes.short_description = 'Yes Votes'

@admin.register(PetitionVote)
class PetitionVoteAdmin(admin.ModelAdmin):
    list_display = ['user', 'petition', 'vote_type', 'created_at']
    list_filter = ['vote_type', 'created_at']
    search_fields = ['user__username', 'petition__movie_title']
    readonly_fields = ['created_at']
    ordering = ['-created_at']