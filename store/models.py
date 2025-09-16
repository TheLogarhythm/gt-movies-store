# store/models.py
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal

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
    
    def is_hidden_by_user(self, user):
        """Check if this movie is hidden by the given user"""
        if not user.is_authenticated:
            return False
        return HiddenMovie.objects.filter(user=user, movie=self).exists()
    
    @classmethod
    def get_visible_movies(cls, user):
        """Get movies that are not hidden by the user"""
        if not user.is_authenticated:
            return cls.objects.all()
        
        hidden_movie_ids = HiddenMovie.objects.filter(
            user=user
        ).values_list('movie_id', flat=True)
        
        return cls.objects.exclude(id__in=hidden_movie_ids)
    
    @classmethod
    def get_hidden_movies(cls, user):
        """Get movies that are hidden by the user"""
        if not user.is_authenticated:
            return cls.objects.none()
        
        hidden_movie_ids = HiddenMovie.objects.filter(
            user=user
        ).values_list('movie_id', flat=True)
        
        return cls.objects.filter(id__in=hidden_movie_ids)

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

class HiddenMovie(models.Model):
    """Model to track movies hidden by users - User Story #22"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    movie = models.ForeignKey('Movie', on_delete=models.CASCADE)
    hidden_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'movie']
        verbose_name = 'Hidden Movie'
        verbose_name_plural = 'Hidden Movies'
    
    def __str__(self):
        return f"{self.user.username} hid {self.movie.title}"