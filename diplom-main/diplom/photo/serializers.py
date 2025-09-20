from rest_framework import serializers
from .models import Post, Comment, ImageModel
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderUnavailable, GeocoderTimedOut
import logging
from geopy.geocoders import Nominatim

logger = logging.getLogger(__name__)

class ImageSerializers(serializers.ModelSerializer):
    class Meta:
        model = ImageModel
        fields = ['image']


class LocationSerializer(serializers.Serializer):
    def to_representation(self, instance):
        lat = getattr(instance, 'latitude', None)
        lon = getattr(instance, 'longitude', None)
        if lat is None or lon is None:
            return None

        geolocator = Nominatim(user_agent="social_network", timeout=10)
        try:
            location = geolocator.reverse((lat, lon))
            return location.address if location else None
        except (GeocoderTimedOut, GeocoderUnavailable) as e:
            logger.warning("Geocoding failed for (%s,%s): %s", lat, lon, e)
        return None



class CommentSerializers(serializers.ModelSerializer):
    
    class Meta:
        model = Comment
        fields = '__all__'

    def validate_text(self, value):
        if not value.strip():
            raise serializers.ValidationError("Комментарий не может быть пустым.")
        return value


class PostSerializers(serializers.ModelSerializer):
    location = serializers.SerializerMethodField()
    comment = CommentSerializers(many=True, read_only=True)
    images = ImageSerializers(many=True, read_only=True)
    uploaded_images = serializers.ListField(child=serializers.ImageField(), write_only=True, required=False)
    like_count = serializers.IntegerField(read_only=True)
    location_name = serializers.CharField(read_only=True)

    class Meta:
        model = Post
        fields = [
            'id', 'user', 'text', 'created_at', 'images', 'uploaded_images',
            'comment', 'like_count', 'location_query',
            'latitude', 'longitude', 'location_name', 'location',
        ]
        extra_kwargs = {
            'location_query': {'write_only': True},
            'latitude': {'read_only': True},
            'longitude': {'read_only': True},
        }

    def get_location(self, obj):
        """
        Вызываем to_representation напрямую, чтобы не оборачивать
        результат в ReturnDict (который ожидает маппинг).
        Возвращаем строку адреса или None.
        """
        try:
            # используем экземпляр сериализатора без .data
            loc = LocationSerializer().to_representation(obj)
            # loc может быть строкой либо None — оба корректны
            return loc
        except (GeocoderTimedOut, GeocoderUnavailable) as e:
            logger.warning("Geocoding failed for post id=%s: %s", getattr(obj, "id", None), e)
            return None
        except Exception:
            logger.exception("Unexpected error during location serialization for post id=%s", getattr(obj, "id", None))
            return None
    
    def create(self, validated_data):
        images_data = validated_data.pop('uploaded_images', [])
        post = Post.objects.create(**validated_data)
        for image in images_data:
            ImageModel.objects.create(post=post, image=image)
        return post
