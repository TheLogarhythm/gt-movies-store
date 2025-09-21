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

# New models for Movie Petition functionality - User Story #21
class MoviePetition(models.Model):
    """Model for movie inclusion petitions - User Story #21"""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('pending', 'Pending Review'),
    ]
    
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_petitions')
    movie_title = models.CharField(max_length=200)
    movie_description = models.TextField()
    reason = models.TextField(help_text="Why should this movie be added to the catalog?")
    director = models.CharField(max_length=100, blank=True)
    release_year = models.PositiveIntegerField(blank=True, null=True)
    genre = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Petition for '{self.movie_title}' by {self.creator.username}"
    
    def total_votes(self):
        """Get total number of votes"""
        return self.votes.count()
    
    def yes_votes(self):
        """Get number of 'yes' votes"""
        return self.votes.filter(vote_type='yes').count()
    
    def no_votes(self):
        """Get number of 'no' votes"""
        return self.votes.filter(vote_type='no').count()
    
    def yes_percentage(self):
        """Get percentage of 'yes' votes"""
        total = self.total_votes()
        if total == 0:
            return 0
        return round((self.yes_votes() / total) * 100, 1)
    
    def user_voted(self, user):
        """Check if user has already voted on this petition"""
        if not user.is_authenticated:
            return False
        return self.votes.filter(user=user).exists()
    
    def user_vote_type(self, user):
        """Get user's vote type for this petition"""
        if not user.is_authenticated:
            return None
        vote = self.votes.filter(user=user).first()
        return vote.vote_type if vote else None

class PetitionVote(models.Model):
    """Model for votes on movie petitions - User Story #21"""
    VOTE_CHOICES = [
        ('yes', 'Yes - Add this movie'),
        ('no', 'No - Don\'t add this movie'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    petition = models.ForeignKey(MoviePetition, on_delete=models.CASCADE, related_name='votes')
    vote_type = models.CharField(max_length=3, choices=VOTE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'petition']

    def __str__(self):
        return f"{self.user.username} voted '{self.vote_type}' on '{self.petition.movie_title}'"