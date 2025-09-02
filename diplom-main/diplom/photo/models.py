import logging
from django.db import models
from django.contrib.auth.models import User
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderUnavailable, GeocoderTimedOut

# Create your models here.

logger = logging.getLogger(__name__)


class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='post')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    location_query = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Поисковый запрос локации"
    )
    latitude = models.FloatField(
        blank=True,
        null=True,
        verbose_name="Широта"
    )
    longitude = models.FloatField(
        blank=True,
        null=True,
        verbose_name="Долгота"
    )
    location_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Название локации"
    )

    def _geocode(self, geocoder_func, *args, **kwargs):

        try:
            return geocoder_func(*args, **kwargs)
        except (GeocoderUnavailable, GeocoderTimedOut) as e:
            logger.error(f"Geocoding failed after  attempts: {e}")
        return None

    def geocode_location(self):
        if not self.location_query:
            return
        geolocator = Nominatim(user_agent="social_network")
        location = self._geocode(geolocator.geocode, self.location_query)
        if location:
            self.latitude = location.latitude
            self.longitude = location.longitude

    def reverse_geocode(self):
        if self.latitude is None or self.longitude is None:
            return
        geolocator = Nominatim(user_agent="social_network")
        location = self._geocode(
            geolocator.reverse,
            (self.latitude, self.longitude)
        )
        if location:
            self.location_name = location.address

    def save(self, *args, **kwargs):
        if self.location_query:
            self.geocode_location()
        if self.latitude and self.longitude:
            self.reverse_geocode()
        super().save(*args, **kwargs)


class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comment')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comment')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    pass


class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='like')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='like')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'post'],
                name='unique_like'
            )
        ]


class ImageModel(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='image')
    image = models.ImageField(upload_to='posts/images/', verbose_name='Изображение')
    pass
