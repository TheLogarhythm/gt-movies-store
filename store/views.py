# store/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Movie, Review, Order, OrderItem
from .forms import UserRegistrationForm, ReviewForm

from django.db.models import Sum
import json

def trending_map_view(request):
    """Display interactive Leaflet map with trending movies"""
    # Define major Southeast US cities with coordinates
    regions = {
        'Atlanta, GA': {'lat': 33.7490, 'lng': -84.3880},
        'Miami, FL': {'lat': 25.7617, 'lng': -80.1918},
        'Orlando, FL': {'lat': 28.5383, 'lng': -81.3792},
        'Charlotte, NC': {'lat': 35.2271, 'lng': -80.8431},
        'Nashville, TN': {'lat': 36.1627, 'lng': -86.7816},
        'Birmingham, AL': {'lat': 33.5186, 'lng': -86.8104},
        'Columbia, SC': {'lat': 34.0007, 'lng': -81.0348},
    }
    
    regional_data = {}
    
    for region_name, coords in regions.items():
        city_name = region_name.split(',')[0]
        trending_movies = Movie.objects.filter(
            orderitem__region__icontains=city_name
        ).annotate(
            total_purchases=Sum('orderitem__quantity')
        ).filter(total_purchases__gt=0).distinct().order_by('-total_purchases')[:3]
        
        if not trending_movies.exists():
            trending_movies = Movie.objects.all()[:3]
            for movie in trending_movies:
                movie.total_purchases = 5  # Sample data
        
        regional_data[region_name] = {
            'coordinates': coords,
            'movies': [
                {
                    'title': movie.title,
                    'purchases': getattr(movie, 'total_purchases', 5),
                    'id': movie.id,
                    'price': str(movie.price)
                } for movie in trending_movies
            ],
            'total_orders': OrderItem.objects.filter(region__icontains=city_name).count() or 3
        }
    
    context = {
        'regional_data': regional_data,
        'regions_json': json.dumps(regional_data)
    }
    return render(request, 'store/trending_map.html', context)

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
    """Movie list view with search functionality - User Stories #4, #5"""
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
    """Retrieve the cart from the session"""
    cart = request.session.get('cart', {})
    cart_items = []
    total = 0

    for movie_id, quantity in cart.items():
        try:
            movie = Movie.objects.get(id=int(movie_id))
            cart_items.append({
                'movie': movie,
                'quantity': quantity,
                'total_price': movie.price * quantity
            })
            total += movie.price * quantity
        except Movie.DoesNotExist:
            continue

    return {
        'items': cart_items,
        'total': total
    }

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
    cart = get_cart(request)  # Function to retrieve the cart
    if not cart:
        messages.error(request, 'Your cart is empty.')
        return redirect('cart')

    if request.method == 'POST':
        # Process the form data
        region = request.POST.get('region', 'Unknown Region')
        city = request.POST.get('city', 'Unknown City')

        # Create the order
        total = 0
        order = Order.objects.create(
            user=request.user,
            total_amount=0,
            city=city,
            region=region
        )

        for movie_id, quantity in cart.items():
            try:
                movie = Movie.objects.get(id=int(movie_id))
                item_total = movie.price * quantity
                OrderItem.objects.create(
                    order=order,
                    movie=movie,
                    quantity=quantity,
                    price=movie.price,
                    region=region
                )
                total += item_total
            except Movie.DoesNotExist:
                messages.error(request, f'Movie with ID {movie_id} not found.')
                continue

        order.total_amount = total
        order.save()

        # Clear the cart
        request.session['cart'] = {}
        request.session.modified = True

        messages.success(request, f'Order #{order.id} created successfully!')
        return redirect('order_list')

    # Render the checkout form
    return render(request, 'store/checkout.html', {'cart': cart})

@login_required
def order_list(request):
    """View order history - User Story #14"""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'store/order_list.html', {'orders': orders})