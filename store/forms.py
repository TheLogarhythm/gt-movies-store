# store/forms.py
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Review, MoviePetition

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['content', 'rating']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 4}),
            'rating': forms.Select(choices=[(i, i) for i in range(1, 6)])
        }

class MoviePetitionForm(forms.ModelForm):
    """Form for creating movie petitions - User Story #21"""
    class Meta:
        model = MoviePetition
        fields = ['movie_title', 'movie_description', 'reason', 'director', 'release_year', 'genre']
        widgets = {
            'movie_title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter the movie title'
            }),
            'movie_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe the movie plot, themes, etc.'
            }),
            'reason': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Why should this movie be added to our catalog?'
            }),
            'director': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Director name (optional)'
            }),
            'release_year': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Year (optional)',
                'min': 1900,
                'max': 2030
            }),
            'genre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Genre (optional)'
            }),
        }
        labels = {
            'movie_title': 'Movie Title',
            'movie_description': 'Movie Description',
            'reason': 'Why This Movie?',
            'director': 'Director',
            'release_year': 'Release Year',
            'genre': 'Genre',
        }
        help_texts = {
            'reason': 'Explain why you think this movie would be a great addition to our catalog.',
            'release_year': 'The year the movie was released.',
        }