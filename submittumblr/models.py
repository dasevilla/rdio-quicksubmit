from django.db import models
from django.contrib.auth.models import User


class TumblrBlog(models.Model):
    user = models.ForeignKey(User)
    tumblr_url = models.URLField()

    unique_together = (('user', 'tumblr_url'),)
