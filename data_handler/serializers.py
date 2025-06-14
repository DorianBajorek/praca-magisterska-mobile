from rest_framework import serializers
from .models import Offer, Book
from django.contrib.auth.models import User



class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ['id', 'title', 'author', 'cover_image', 'isbn']

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class OfferSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)  # Nested serializer to include user details
    book = BookSerializer(read_only=True)  # Nested serializer to include book details

    class Meta:
        model = Offer
        fields = ['id', 'user', 'book', 'price', 'created_at', 'modified_at', 'is_for_sale', 'condition', 'front_image', 'back_image']