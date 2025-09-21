# store/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Movie, Review, Order, OrderItem, MoviePetition, PetitionVote
from .forms import UserRegistrationForm, ReviewForm, MoviePetitionForm

def home(request):
    """Home page view - User Story #1"""
    return render(request, 'store/home.html')

def register(request):
    """User registration view - User Story #2"""
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

# New views for Movie Petition functionality - User Story #21
def petition_list(request):
    """View all active movie petitions - User Story #21"""
    petitions = MoviePetition.objects.filter(status='active').order_by('-created_at')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        petitions = petitions.filter(
            Q(movie_title__icontains=search_query) |
            Q(movie_description__icontains=search_query) |
            Q(genre__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(petitions, 10)  # Show 10 petitions per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'store/petition_list.html', {
        'page_obj': page_obj,
        'search_query': search_query
    })

@login_required
def create_petition(request):
    """Create a new movie petition - User Story #21"""
    if request.method == 'POST':
        form = MoviePetitionForm(request.POST)
        if form.is_valid():
            petition = form.save(commit=False)
            petition.creator = request.user
            petition.save()
            messages.success(request, f'Petition for "{petition.movie_title}" created successfully!')
            return redirect('petition_detail', pk=petition.pk)
    else:
        form = MoviePetitionForm()
    
    return render(request, 'store/create_petition.html', {'form': form})

def petition_detail(request, pk):
    """View petition details - User Story #21"""
    petition = get_object_or_404(MoviePetition, pk=pk)
    
    # Get user's vote if authenticated
    user_vote = None
    if request.user.is_authenticated:
        user_vote = PetitionVote.objects.filter(user=request.user, petition=petition).first()
    
    context = {
        'petition': petition,
        'user_vote': user_vote,
    }
    
    return render(request, 'store/petition_detail.html', context)

@login_required
def vote_petition(request, pk):
    """Vote on a movie petition - User Story #21"""
    petition = get_object_or_404(MoviePetition, pk=pk)
    
    if request.method == 'POST':
        vote_type = request.POST.get('vote_type')
        
        if vote_type not in ['yes', 'no']:
            messages.error(request, 'Invalid vote type.')
            return redirect('petition_detail', pk=pk)
        
        # Check if user has already voted
        existing_vote = PetitionVote.objects.filter(user=request.user, petition=petition).first()
        
        if existing_vote:
            # Update existing vote
            if existing_vote.vote_type != vote_type:
                existing_vote.vote_type = vote_type
                existing_vote.save()
                messages.success(request, f'Your vote has been updated to "{vote_type.upper()}"!')
            else:
                messages.info(request, f'You have already voted "{vote_type.upper()}" on this petition.')
        else:
            # Create new vote
            PetitionVote.objects.create(
                user=request.user,
                petition=petition,
                vote_type=vote_type
            )
            messages.success(request, f'Your "{vote_type.upper()}" vote has been recorded!')
    
    return redirect('petition_detail', pk=pk)

@login_required
def my_petitions(request):
    """View petitions created by current user - User Story #21"""
    petitions = MoviePetition.objects.filter(creator=request.user).order_by('-created_at')
    
    return render(request, 'store/my_petitions.html', {
        'petitions': petitions
    })