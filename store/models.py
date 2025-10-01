# store/models.py
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
from django.db.models import Avg, Sum, Count

class Movie(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(
        max_digits=6, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    image = models.ImageField(upload_to='movies/')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
    
    def get_average_rating(self):
        """Calculate and return the average rating for this movie"""
        avg_rating = self.review_set.aggregate(Avg('rating'))['rating__avg']
        return round(avg_rating, 1) if avg_rating else 0
    
    def get_rating_count(self):
        """Return the total number of ratings for this movie"""
        return self.review_set.count()
    
    def get_total_purchases_by_region(self, region=None):
        """Get total purchases for this movie, optionally filtered by region"""
        queryset = self.orderitem_set.all()
        if region:
            queryset = queryset.filter(order__region=region)
        return queryset.aggregate(total=Sum('quantity'))['total'] or 0


class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    movie = models.ForeignKey('Movie', on_delete=models.CASCADE)
    content = models.TextField()
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'movie']

    def __str__(self):
        return f"Review for {self.movie.title} by {self.user.username}"

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    region = models.CharField(max_length=100, default='Georgia')
    city = models.CharField(max_length=100, default='Atlanta')

    def __str__(self):
        return f"Order #{self.id} by {self.user.username}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=6, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} x {self.movie.title}"

    def subtotal(self):
        return self.quantity * self.price