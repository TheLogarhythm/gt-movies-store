# store/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Movie, Review, Order, OrderItem, HiddenMovie
from .forms import UserRegistrationForm, ReviewForm

def home(request):
    return render(request, 'store/home.html')

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful!')
            return redirect('home')
    else:
        form = UserRegistrationForm()
    return render(request, 'store/register.html', {'form': form})

def movie_list(request):
    """Movie list view with search functionality and hidden movies filter - User Stories #4, #5, #22"""
    # Get visible movies (not hidden by current user)
    if request.user.is_authenticated:
        movies = Movie.get_visible_movies(request.user)
    else:
        movies = Movie.objects.all()

    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        movies = movies.filter(title__icontains=search_query)

    return render(request, 'store/movie_list.html', {
        'movies': movies,
        'search_query': search_query
    })

def movie_detail(request, pk):
    """Movie detail view with reviews - User Stories #8, #12, #13"""
    movie = get_object_or_404(Movie, pk=pk)
    reviews = Review.objects.filter(movie=movie).order_by('-created_at')

    # Check if user has already reviewed this movie
    user_review = None
    if request.user.is_authenticated:
        user_review = Review.objects.filter(movie=movie, user=request.user).first()

    if request.method == 'POST' and request.user.is_authenticated and not user_review:
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.movie = movie
            review.save()
            messages.success(request, 'Review added successfully!')
            return redirect('movie_detail', pk=pk)
    else:
        form = ReviewForm()

    return render(request, 'store/movie_detail.html', {
        'movie': movie,
        'reviews': reviews,
        'form': form,
        'user_review': user_review
    })

@login_required
def review_edit(request, pk):
    """Edit review - User Story #10"""
    review = get_object_or_404(Review, pk=pk)

    # Check if user owns this review
    if review.user != request.user:
        messages.error(request, 'You cannot edit this review.')
        return redirect('movie_detail', pk=review.movie.pk)

    if request.method == 'POST':
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
            messages.success(request, 'Review updated successfully!')
            return redirect('movie_detail', pk=review.movie.pk)
    else:
        form = ReviewForm(instance=review)

    return render(request, 'store/review_edit.html', {
        'form': form,
        'review': review
    })

@login_required
def review_delete(request, pk):
    """Delete review - User Story #11"""
    review = get_object_or_404(Review, pk=pk)

    # Check if user owns this review
    if review.user != request.user:
        messages.error(request, 'You cannot delete this review.')
        return redirect('movie_detail', pk=review.movie.pk)

    if request.method == 'POST':
        movie_pk = review.movie.pk
        review.delete()
        messages.success(request, 'Review deleted successfully!')
        return redirect('movie_detail', pk=movie_pk)

    return render(request, 'store/review_confirm_delete.html', {'review': review})

def get_cart(request):
    """Utility function to get or create cart in session"""
    cart = request.session.get('cart', {})
    return cart

def update_cart(request, cart):
    """Utility function to update cart in session"""
    request.session['cart'] = cart
    request.session.modified = True

@login_required
def add_to_cart(request, movie_id):
    """Add movie to cart - User Story #7"""
    movie = get_object_or_404(Movie, id=movie_id)
    cart = get_cart(request)

    try:
        quantity = int(request.POST.get('quantity', 1))
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
    except (ValueError, TypeError):
        messages.error(request, 'Invalid quantity specified.')
        return redirect('movie_detail', pk=movie_id)

    if str(movie_id) in cart:
        cart[str(movie_id)] += quantity
    else:
        cart[str(movie_id)] = quantity

    update_cart(request, cart)
    messages.success(request, f'Added {quantity} {movie.title} to cart.')
    return redirect('movie_detail', pk=movie_id)

def cart_view(request):
    """View cart contents - User Story #6"""
    cart = get_cart(request)
    cart_items = []
    total = 0

    for movie_id, quantity in cart.items():
        try:
            movie = Movie.objects.get(id=int(movie_id))
            item_total = movie.price * quantity
            cart_items.append({
                'movie': movie,
                'quantity': quantity,
                'total': item_total
            })
            total += item_total
        except Movie.DoesNotExist:
            continue

    return render(request, 'store/cart.html', {
        'cart_items': cart_items,
        'total': total
    })

@login_required
def remove_from_cart(request):
    """Remove all items from cart - User Story #9"""
    request.session['cart'] = {}
    request.session.modified = True
    messages.info(request, 'Cart cleared successfully.')
    return redirect('cart')

@login_required
def checkout(request):
    """Checkout and create order"""
    cart = get_cart(request)
    if not cart:
        messages.error(request, 'Your cart is empty.')
        return redirect('cart')

    # Create order
    total = 0
    order = Order.objects.create(user=request.user, total_amount=0)

    for movie_id, quantity in cart.items():
        try:
            movie = Movie.objects.get(id=int(movie_id))
            item_total = movie.price * quantity
            OrderItem.objects.create(
                order=order,
                movie=movie,
                quantity=quantity,
                price=movie.price
            )
            total += item_total
        except Movie.DoesNotExist:
            messages.error(request, f'Movie with ID {movie_id} not found.')
            continue

    # Update order total
    order.total_amount = total
    order.save()

    # Clear cart
    request.session['cart'] = {}
    request.session.modified = True

    messages.success(request, f'Order #{order.id} created successfully!')
    return redirect('order_list')

@login_required
def order_list(request):
    """View order history - User Story #14"""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'store/order_list.html', {'orders': orders})

# New views for hidden movies functionality - User Story #22
@login_required
def hide_movie(request, movie_id):
    """Hide a movie for the current user - User Story #22"""
    movie = get_object_or_404(Movie, id=movie_id)
    
    # Create hidden record if it doesn't exist
    hidden_movie, created = HiddenMovie.objects.get_or_create(
        user=request.user,
        movie=movie
    )
    
    if created:
        messages.success(request, f'"{movie.title}" has been hidden from your movie list.')
    else:
        messages.info(request, f'"{movie.title}" is already hidden.')
    
    # Redirect to previous page or movie list
    return redirect(request.META.get('HTTP_REFERER', 'movie_list'))

@login_required
def unhide_movie(request, movie_id):
    """Unhide a movie for the current user - User Story #22"""
    movie = get_object_or_404(Movie, id=movie_id)
    
    try:
        hidden_movie = HiddenMovie.objects.get(user=request.user, movie=movie)
        hidden_movie.delete()
        messages.success(request, f'"{movie.title}" has been restored to your movie list.')
    except HiddenMovie.DoesNotExist:
        messages.error(request, f'"{movie.title}" was not hidden.')
    
    # Redirect to hidden movies page
    return redirect('hidden_movies')

@login_required
def hidden_movies(request):
    """View hidden movies that can be unhidden - User Story #22"""
    # Get current user's hidden movies
    hidden_movies = Movie.get_hidden_movies(request.user)
    
    # Search functionality also applies to hidden movies
    search_query = request.GET.get('search', '')
    if search_query:
        hidden_movies = hidden_movies.filter(title__icontains=search_query)
    
    # Get hidden time information
    hidden_records = HiddenMovie.objects.filter(
        user=request.user,
        movie__in=hidden_movies
    ).select_related('movie')
    
    return render(request, 'store/hidden_movies.html', {
        'hidden_movies': hidden_movies,
        'hidden_records': hidden_records,
        'search_query': search_query
    })

@login_required
def toggle_movie_visibility(request, movie_id):
    """Toggle movie visibility (hide/unhide) - User Story #22"""
    movie = get_object_or_404(Movie, id=movie_id)
    
    try:
        # If already hidden, unhide it
        hidden_movie = HiddenMovie.objects.get(user=request.user, movie=movie)
        hidden_movie.delete()
        messages.success(request, f'"{movie.title}" is now visible in your movie list.')
        action = 'unhidden'
    except HiddenMovie.DoesNotExist:
        # If not hidden, hide it
        HiddenMovie.objects.create(user=request.user, movie=movie)
        messages.success(request, f'"{movie.title}" has been hidden from your movie list.')
        action = 'hidden'
    
    # If AJAX request, return JSON response
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'action': action,
            'message': f'Movie {action} successfully'
        })
    
    return redirect(request.META.get('HTTP_REFERER', 'movie_list'))