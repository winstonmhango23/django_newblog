from django import template
from ..models import Post

register = template.Library()


@register.inclusion_tag('blog/post/recent_posts.html')
def show_recent_posts(count=2):
    recent_posts = Post.published.order_by('-publish')[:count]
    return {'recent_posts': recent_posts}

