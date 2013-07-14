from urlparse import urlparse

from django import forms
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.context_processors import csrf
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from requests_oauthlib import OAuth2, OAuth2Session
from tumblr import TumblrClient
import oauth2 as oauth
import requests
from oauthlib.oauth2 import BackendApplicationClient

from models import TumblrBlog


class TumblrChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return urlparse(obj.tumblr_url).netloc

class TumblrBlogForm(forms.ModelForm):
    class Meta:
        model = TumblrBlog
        fields = ('tumblr_url',)

    tumblr_url = forms.URLField(
        label='Tumblr URL',
        widget=forms.TextInput(attrs={'size':'50'})
    )

class TumblrSubmission(forms.Form):
    album_url = forms.URLField(
        label='Rdio Album URL',
        widget=forms.TextInput(attrs={'size':'50'})
    )

    comment = forms.CharField(
        label='Your comment',
        required=False,
        widget=forms.Textarea
    )

    def __init__(self, user, *args, **kwargs):
        super(TumblrSubmission, self).__init__(*args, **kwargs)

        self.fields['tumblr_url'] = TumblrChoiceField(
            label='Tumblr URL',
            empty_label=None,
            queryset=user.tumblrblog_set.all(),
        )


def get_album_info(rdio_token, rdio_url):
    """
    Query Rdio API to get information about the album.
    """

    payload = {
        'method': 'getObjectFromUrl',
        'url': rdio_url,
        'extras': '-trackKeys,bigIcon',
    }

    oauth2_token = {
        'access_token': rdio_token,
        'token_type': 'bearer'
    }
    oauth2_auth = OAuth2(client_id=settings.RDIO_OAUTH2_CLIENT_ID,
                         token=oauth2_token)

    r = requests.post(settings.RDIO_API_URL, auth=oauth2_auth, data=payload)
    r.raise_for_status()

    return r.json()['result']


def create_post(client, album_info, user_comment=None):
    """
    Creates a post submission on Tumblr.
    """

    artist_url = 'http://www.rdio.com' + album_info['artistUrl']
    artist_name = album_info['artist']
    album_name = album_info['name']
    album_url = album_info['shortUrl']
    album_artwork_url = album_info['bigIcon']

    default_tags = 'rdio,album artwork'

    # Ignore various artists
    if album_info['artistKey'] == 'r62':
        post_caption = '<p><a href="%s">%s</a> by <em>%s</em></p>' % (album_url, album_name, artist_name)
    else:
        post_caption = '<p><a href="%s">%s</a> by <a href="%s">%s</a></p>' % (album_url, album_name, artist_url, artist_name)

    if user_comment is not None:
        post_caption+= '<p>%s</p>' % user_comment

    params = {
        'type': 'photo',
        'source': album_artwork_url,
        'link': album_url,
        'tags': default_tags,
        'caption': post_caption,
    }
    return client.submit_post(params)


@login_required
def submission(request):
    if request.method == 'POST': # If the form has been submitted...
        form = TumblrSubmission(user=request.user, data=request.POST) # A form bound to the POST data
        if form.is_valid(): # All validation rules pass
            tumblr_auth = request.user.social_auth.filter(provider='tumblr').get()
            access_key = tumblr_auth.tokens['oauth_token']
            access_secret = tumblr_auth.tokens['oauth_token_secret']

            consumer = oauth.Consumer(settings.TUMBLR_CONSUMER_KEY,
                settings.TUMBLR_CONSUMER_SECRET)
            token = oauth.Token(access_key, access_secret)

            client = TumblrClient(form.cleaned_data['tumblr_url'], consumer, token)
            album_info = get_album_info(settings.RDIO_API_TOKEN, form.cleaned_data['album_url'])
            create_post(client, album_info, form.cleaned_data['comment'])

            return HttpResponseRedirect(reverse('submittumblr.views.done'))
    else:
        form = TumblrSubmission(user=request.user, initial={
            'album_url': request.GET.get('url', None),
        })

    c = {
        'form': form,
    }
    c.update(csrf(request))

    return render_to_response('tumblr-submission.html', c)


@login_required
def add(request):
    if request.method == 'POST':
        tumblr_blog = TumblrBlog(user=request.user)
        form = TumblrBlogForm(request.POST, instance=tumblr_blog)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('submittumblr.views.done'))
    else:
        form = TumblrBlogForm(initial={
            'tumblr_url': request.GET.get('url', None),
        })

    c = {
        'form': form,
    }
    c.update(csrf(request))

    return render_to_response('tumblr-add.html', c)


def done(request):
    return render_to_response('done.html', {})


def home(request):
    return render_to_response('index.html', {})
