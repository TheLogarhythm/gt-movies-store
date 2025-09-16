# store/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Sum
from django.core.paginator import Paginator
from django.contrib.auth.models import User
from .models import Movie, Review, Order, OrderItem, ReviewLike
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
    reviews = Review.objects.filter(movie=movie).order_by('-likes', '-created_at')

    # Check if user has already reviewed this movie
    user_review = None
    user_likes = []
    if request.user.is_authenticated:
        user_review = Review.objects.filter(movie=movie, user=request.user).first()
        user_likes = list(ReviewLike.objects.filter(
            user=request.user, 
            review__movie=movie
        ).values_list('review_id', flat=True))

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
        'user_review': user_review,
        'user_likes': user_likes
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

# === 新增的热门评论功能 ===

def top_comments(request):
    """显示所有热门评论 - 新用户故事"""
    # 获取热门评论 (按点赞数和评论长度排序)
    reviews = Review.objects.annotate(
        content_length=Count('content')
    ).filter(
        Q(likes__gte=3) |  # 点赞数>=3
        Q(content__regex=r'.{100,}')  # 或评论长度>=100字符
    ).select_related('user', 'movie').order_by('-likes', '-created_at')

    # 分页处理
    paginator = Paginator(reviews, 10)  # 每页显示10条评论
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'store/top_comments.html', {
        'reviews': page_obj,
        'total_comments': reviews.count()
    })

def funny_users(request):
    """显示幽默用户排行榜"""
    # 按用户的总点赞数排序
    users = User.objects.annotate(
        total_likes=Sum('review__likes'),
        review_count=Count('review')
    ).filter(
        total_likes__gt=0
    ).order_by('-total_likes')[:20]  # 前20名

    return render(request, 'store/funny_users.html', {
        'users': users
    })

@login_required
def like_review(request, review_id):
    """点赞/取消点赞评论功能"""
    review = get_object_or_404(Review, id=review_id)
    
    # 检查用户是否已经点赞
    try:
        like = ReviewLike.objects.get(user=request.user, review=review)
        # 如果已经点赞，则取消点赞
        like.delete()
        review.likes = max(0, review.likes - 1)
        review.save()
        messages.info(request, 'You unliked this review.')
    except ReviewLike.DoesNotExist:
        # 如果没有点赞，则添加点赞
        ReviewLike.objects.create(user=request.user, review=review)
        review.likes += 1
        review.save()
        messages.success(request, 'You liked this review!')
    
    # 返回到原页面
    return redirect(request.META.get('HTTP_REFERER', 'movie_detail'), pk=review.movie.pk)