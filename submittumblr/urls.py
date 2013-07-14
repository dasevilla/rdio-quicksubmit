from django.conf.urls import patterns, url

urlpatterns = patterns('',
    url(r'^$', 'submittumblr.views.home', name='home'),
    url(r'^add/$', 'submittumblr.views.add', name='add'),
    url(r'^submission/$', 'submittumblr.views.submission', name='submission'),
    url(r'^done/$', 'submittumblr.views.done', name='done'),
)
