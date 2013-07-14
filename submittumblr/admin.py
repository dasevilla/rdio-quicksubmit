from django.contrib import admin
from submittumblr.models import TumblrBlog


class TumblrBlogAdmin(admin.ModelAdmin):
    fields = ['user', 'tumblr_url']
    list_display = ('user', 'tumblr_url')
    list_filter = ['user']


admin.site.register(TumblrBlog, TumblrBlogAdmin)
