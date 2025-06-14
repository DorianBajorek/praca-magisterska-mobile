from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Book(models.Model):
    title = models.CharField(max_length=255)  # Tytuł książki
    author = models.CharField(max_length=255)  # Autor książki
    cover_image = models.ImageField(upload_to='covers/', null=True, blank=True)  # Zdjęcie okładki
    isbn = models.CharField(max_length=13, null=True, blank=True, unique=True) # Numer ISBN
    tags = models.JSONField(default=list, blank=True)

    def __str__(self):
        return f"{self.title} by {self.author}"


class Offer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='entries')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='entries')
    price = models.CharField(max_length=50, default="00")
    created_at = models.DateTimeField(default=timezone.now)
    modified_at = models.DateTimeField(default=timezone.now)
    is_for_sale = models.BooleanField(default=False)
    condition = models.CharField(max_length=50)  # Stan książki (np. 'nowa', 'używana', 'zniszczona')
    front_image = models.ImageField(upload_to='user_books/front_images/', null=True, blank=True)
    back_image = models.ImageField(upload_to='user_books/back_images/', null=True, blank=True)
    tags = models.JSONField(default=list, blank=True)  # Lista tagów zwróconych przez GPT

    def __str__(self):
        return f"{self.user.username} owns {self.book.title}"
 