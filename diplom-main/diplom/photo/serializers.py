from rest_framework import serializers
from .models import Post, Comment, ImageModel
from geopy.geocoders import Nominatim


class ImageSerializers(serializers.ModelSerializer):
    class Meta:
        model = ImageModel
        fields = ['image']


class LocationSerializer(serializers.Serializer):
    def to_representation(self, instance):
        geolocator = Nominatim(user_agent="social_network")
        location = geolocator.reverse((instance.latitude, instance.longitude))
        return location.address



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
    images = serializers.ListField(child=serializers.ImageField(), write_only=True, required=False)
    like_count = serializers.IntegerField(read_only=True)
    location_name = serializers.CharField(read_only=True)

    class Meta:
        model = Post
        fields = [
            'id', 'user', 'text', 'created_at', 'image',
            'comment', 'like_count', 'location_query',
            'latitude', 'longitude', 'location_name', 'location',
        ]
        extra_kwargs = {
            'location_query': {'write_only': True},
            'latitude': {'read_only': True},
            'longitude': {'read_only': True},
        }

    def get_location(self, obj):
        return LocationSerializer(obj).data
    
    def validate_image(self, image):
        if not image.name.lower().endswith(('.png', '.jpg', '.jpeg')):
            raise serializers.ValidationError("Поддерживаются только PNG, JPG и JPEG.")
        return image
