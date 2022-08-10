# Create your views here.

from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator, EmptyPage,PageNotAnInteger
#JsonResponse to return json objects used in infinite scroll
# from django.http import JsonResponse
from django.views.generic import ListView
from .models import Post, Comment
#postgress search classes
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank, TrigramSimilarity
from .forms import CommentForm, SearchForm
from taggit.models import Tag
from django.db.models import Count
from django.db.models import Q



def post_detail(request, year, month, day, post):
    post = get_object_or_404(Post, slug=post,
                                   status='published',
                                   publish__year=year,
                                   publish__month=month,
                                   publish__day=day)
    
    # List of active comments for this post
    comments = post.comments.filter(active=True)

    new_comment = None

    if request.method == 'POST':
        # A comment was posted
        comment_form = CommentForm(data=request.POST)
        if comment_form.is_valid():
            # Create Comment object but don't save to database yet
            new_comment = comment_form.save(commit=False)
            # Assign the current post to the comment
            new_comment.post = post
            # Save the comment to the database
            new_comment.save()
    else:
        comment_form = CommentForm()

    # List of similar posts
    post_tags_ids = post.tags.values_list('id', flat=True)
    similar_posts = Post.published.filter(tags__in=post_tags_ids).exclude(id=post.id)
    similar_posts = similar_posts.annotate(same_tags=Count('tags')).order_by('-same_tags','-publish')[:3]

    return render(request,
                  'blog/post/detail.html',
                  {'post': post,
                   'comments': comments,
                   'new_comment': new_comment,
                   'comment_form': comment_form,
                   'similar_posts': similar_posts})


#function based view with pagination
def post_list(request, tag_slug=None):
    object_list = Post.published.all()
    tag = None
    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        object_list = object_list.filter(tags__in=[tag])

    paginator = Paginator(object_list, 2) # 2 posts in each page
    page = request.GET.get('page')
    try:
        posts = paginator.page(page)
    except PageNotAnInteger:     
        # If page is not an integer deliver the first page
        posts = paginator.page(1)
    except EmptyPage:
        posts = paginator.page(paginator.num_pages)

    return render(request,'blog/post/list.html',{'page': page,'posts': posts, 'tag': tag})

#search view 
def post_search(request):
    form = SearchForm()
    query = None
    results = []
    if 'query' in request.GET:
        form = SearchForm(request.GET)
        if form.is_valid():
            query = form.cleaned_data['query']
            # results = Post.objects.annotate(search=SearchVector('title', 'body'),).filter(search=query)
            
            # search_vector = SearchVector('title', 'body')
            # search_query = SearchQuery(query)
            # results = Post.objects.annotate(search=search_vector,rank=SearchRank(search_vector, search_query) ).filter(search=search_query).order_by('-rank')


            search_vector = SearchVector('title', weight='A') + SearchVector('body',weight='B')
            search_query = SearchQuery(query) 
            results = Post.objects.annotate(rank=SearchRank(search_vector, search_query)).filter(rank__gte=0.3).order_by('-rank')
            
    return render(request,'blog/post/search.html',{'form': form,'query': query,'results': results})

# def post_search(self): # new
#         query = self.request.GET.get('search')
#         results = Post.objects.filter(
#             Q(name__icontains=query) | Q(state__icontains=query)
#         )
#         return results



# Define function to search book

# def post_search(request):
#     results = []
#     if request.method == "GET":
#         query = request.GET.get('search')
#         if query == '':
#             query = ''
#         results = Post.objects.filter(Q(title__icontains=query) | Q(body__icontains=query) )
#     return render(request, 'blog/post/search.html', {'query': query, 'results': results})



# def post_search(request):
#     form = SearchForm()
#     query = None
#     results = []
#     if 'query' in request.GET:
#         form = SearchForm(request.GET)
#         if form.is_valid():
#             query = form.cleaned_data['query']
#             results = Post.objects.annotate(
#                 similarity=TrigramSimilarity('title', query),
#             ).filter(similarity__gt=0.3).order_by('-similarity')
#     return render(request,
#                   'blog/post/search.html',
#                   {'form': form,
#                    'query': query,
#                    'results': results})