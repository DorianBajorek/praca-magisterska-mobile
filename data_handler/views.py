from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from .models import  Book, Offer 
from .serializers import BookSerializer, OfferSerializer
from .service import Scraper
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from rest_framework.permissions import AllowAny
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.db.models import Q
import os
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponse
from PIL import Image
import numpy as np
import cv2
from io import BytesIO
from ultralytics import YOLO

api_key = os.getenv("OPENAI_API_KEY")

@api_view(['POST'])
@authentication_classes([SessionAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def v1_add_book(request):
    serializer = BookSerializer(data=request.data)
    
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@authentication_classes([SessionAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def add_ofer(request):
    user = request.user
    isbn = request.data.get("isbn")

    try:
        book = Book.objects.get(isbn=isbn)
    except Book.DoesNotExist:
        return Response({'error' : 'Book not found'},status=status.HTTP_400_BAD_REQUEST )

    user_offer  = Offer.objects.create(user=user,
                                       book=book,
                                       is_for_sale = False,
                                       condition = 'new')
    serializer = OfferSerializer(user_offer)
    return Response(serializer.data, status=status.HTTP_201_CREATED)

@api_view(['GET'])
@permission_classes([AllowAny])
def v1_get_user_offers(request, username):
    if not username:
        return Response({"error": "Username parameter is required"}, status=status.HTTP_400_BAD_REQUEST)
    user = User.objects.get(username=username)
    offers = Offer.objects.filter(user=user)
    
    if not offers.exists():
        return Response({"error": "No offers found for this user"}, status=status.HTTP_404_NOT_FOUND)

    serializer = OfferSerializer(offers, many=True)

    response_data = [
        {
            "username" : username,
            "offer_id": item["id"],
            "title": item["book"]["title"],
            "author": item["book"]["author"],
            "condition": item["condition"],
            "price": item["price"],
            "cover_book": request.build_absolute_uri(item["book"]["cover_image"]),
            "frontImage": request.build_absolute_uri(item["front_image"]),
            "backImage": request.build_absolute_uri(item["back_image"]),
            "description": "text"
        }
        for item in serializer.data
    ]
    
    return Response(response_data, status=status.HTTP_200_OK)

@api_view(['GET'])
@authentication_classes([SessionAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def v1_get_all_offers(request):
    user = request.user
    offers = Offer.objects.all()
    
    # Serializowanie wielu obiektów wymaga many=True
    serializer = OfferSerializer(offers, many=True)
    response_data = [
        {
            "offer_id": item["id"],
            "title": item["book"]["title"],
            "author": item["book"]["author"],
            "condition": item["condition"],
            "price": "10",  # Dodaj wartość ceny (przykładowo 10)
            "cover_book": item["book"]["cover_image"],
            "frontImage": item["front_image"],
            "backImage": item["back_image"],
            "description": "text"  # Dodaj opis (przykładowo "text")
        }
        for item in serializer.data
    ]
    
    return Response(response_data, status=200)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_offer(request):
    offer_id = request.data.get("offer_id")
    offers = Offer.objects.filter(id = offer_id)
    
    
    # Serializowanie wielu obiektów wymaga many=True
    serializer = OfferSerializer(offers, many=True)
    return Response(serializer.data, status=200)

import openai

@api_view(['POST'])
@authentication_classes([SessionAuthentication, TokenAuthentication])
@permission_classes([AllowAny])
def v1_create_offer(request):
    print("OFFER")
    user = request.user
    isbn = request.data.get("isbn")
    book_price = request.data.get("price")
    front_image = request.FILES.get('frontImage')
    back_image = request.FILES.get('backImage')
    isbn_book = Book.objects.filter(isbn=isbn).first()

    # Jeśli książka już istnieje
    if not isbn_book:
        s = Scraper(isbn)
        title, author = s.get_info()
        print(title, author)
        isbn_book = Book.objects.create(title=title, author=author, isbn=isbn)

    user_offer = Offer.objects.create(
        user=user,
        book=isbn_book,
        is_for_sale=False,
        condition='new',
        price=book_price
    )
    
    # Zapisz obrazy, jeśli są
    if front_image:
        front_image_name = f"front_{isbn}_{user.username}.jpg"
        front_image_path = default_storage.save(f'user_books/front_images/{front_image_name}', ContentFile(front_image.read()))
        user_offer.front_image = front_image_path

    if back_image:
        back_image_name = f"back_{isbn}_{user.username}.jpg"
        back_image_path = default_storage.save(f'user_books/back_images/{back_image_name}', ContentFile(back_image.read()))
        user_offer.back_image = back_image_path

    user_offer.save()

    openai.api_key = api_key

    with open('media/tags/tags1.txt', 'r') as file:
        tags_list = file.read().splitlines()

    try:
        print("ROBIE AI")
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": f"Please provide a list of the most relevant tags for the book titled '{isbn_book.title}', based on the following predefined tags list: {', '.join(tags_list)}. Return only the tags as a comma-separated list without any additional text."}
            ]
        )
        print("ROBIE AI")
        tags_response = response['choices'][0]['message']['content'].strip()
        tags_list_from_gpt = [tag.strip() for tag in tags_response.split(",")]

        print(f"Generated tags for {isbn_book.title}: {tags_list_from_gpt}")

        isbn_book.tags = tags_list_from_gpt
        isbn_book.save()

        user_offer.tags = tags_list_from_gpt
        user_offer.save()

    except Exception as e:
        print(f"Error contacting GPT: {e}")

    return Response(status=status.HTTP_200_OK)

@api_view(['POST'])
@authentication_classes([SessionAuthentication, TokenAuthentication])
@permission_classes([AllowAny])
def v1_create_offer_by_title_author(request):
    print("OFFER BY TITLE AND AUTHOR")
    user = request.user
    title = request.data.get("title")
    author = request.data.get("author")
    book_price = request.data.get("price")
    front_image = request.FILES.get('frontImage')
    back_image = request.FILES.get('backImage')

    book = Book.objects.filter(title__iexact=title, author__iexact=author).first()

    if not book:
        book = Book.objects.create(title=title, author=author)

    print(f"BOOK: {book.title} by {book.author}")

    user_offer = Offer.objects.create(
        user=user,
        book=book,
        is_for_sale=False,
        condition='new',
        price=book_price
    )

    if front_image:
        front_image_name = f"front_{title}_{user.username}.jpg"
        front_image_path = default_storage.save(f'user_books/front_images/{front_image_name}', ContentFile(front_image.read()))
        user_offer.front_image = front_image_path

    if back_image:
        back_image_name = f"back_{title}_{user.username}.jpg"
        back_image_path = default_storage.save(f'user_books/back_images/{back_image_name}', ContentFile(back_image.read()))
        user_offer.back_image = back_image_path

    user_offer.save()

    openai.api_key = api_key

    try:
        with open('media/tags/tags1.txt', 'r') as file:
            tags_list = file.read().splitlines()

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": f"Please provide a list of the most relevant tags for the book titled '{book.title}', based on the following predefined tags list: {', '.join(tags_list)}. Return only the tags as a comma-separated list without any additional text."}
            ]
        )

        tags_response = response['choices'][0]['message']['content'].strip()
        tags_list_from_gpt = [tag.strip() for tag in tags_response.split(",")]

        print(f"Generated tags for {book.title}: {tags_list_from_gpt}")

        book.tags = tags_list_from_gpt
        book.save()

        user_offer.tags = tags_list_from_gpt
        user_offer.save()

    except Exception as e:
        print(f"Error contacting GPT: {e}")

    return Response(status=status.HTTP_200_OK)



@api_view(['DELETE'])
@authentication_classes([SessionAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def v1_delete_offer(request, offer_id):
    user = request.user
    print(offer_id)
    try:
        offer = Offer.objects.get(id=offer_id, user=user)
        print("TITLE: ", offer.book.title)
        offer.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    except ObjectDoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    
@api_view(['GET'])
@authentication_classes([SessionAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_latest_offers(request):
    recent_books = Offer.objects.order_by('-created_at')[:5]
    serializer = OfferSerializer(recent_books, many=True)
    return Response({'latest_books' : serializer.data}, status=status.HTTP_200_OK)





@api_view(['GET'])
@permission_classes([AllowAny])
def v1_search_offers_with_title(request):
    search_query = request.query_params.get('searchQuery')
    
    if not search_query:
        return Response({'error': 'Search query is required'}, status=status.HTTP_400_BAD_REQUEST)

    books = Book.objects.filter(title__iregex=fr'\b{search_query}.*')

    if not books.exists():
        return Response({'message': 'No books found matching the search query'}, status=status.HTTP_200_OK)

    user_books = Offer.objects.filter(book__in=books).select_related('user', 'book')

    if not user_books.exists():
        return Response({'message': 'No users found with the specified books'}, status=status.HTTP_200_OK)

    result = []
    for user_book in user_books:
        result.append({
            'username': user_book.user.username,
            'title': user_book.book.title,
            'isbn': user_book.book.isbn,
            'author' : user_book.book.author,
            'price': user_book.price,
            'offer_id': user_book.id,
            'condition': user_book.condition,
            'cover_book': request.build_absolute_uri(user_book.book.cover_image.url) if user_book.book.cover_image else None,
            'frontImage': request.build_absolute_uri(user_book.front_image.url) if user_book.front_image else None,
            'backImage': request.build_absolute_uri(user_book.back_image.url) if user_book.back_image else None,
        })

    return Response(result, status=status.HTTP_200_OK)


from django.db.models import Count, Q
from collections import Counter
import traceback

@api_view(['GET'])
@permission_classes([AllowAny])
def v2_search_offers_with_title(request):
    search_query = request.query_params.get('searchQuery')
    print("SIEMA" + search_query)

    if not search_query:
        return Response({'error': 'Search query is required'}, status=status.HTTP_400_BAD_REQUEST)
    print("SIEMA2")
    tags_file_path = os.path.join(settings.BASE_DIR, 'media/tags/tags1.txt')
    try:
        with open(tags_file_path, 'r', encoding='utf-8') as file:
            tags_from_file = file.read().strip().split(',')
            tags_from_file = [tag.strip() for tag in tags_from_file]
    except FileNotFoundError:
        return Response({'error': 'Tags file not found'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    print("XD ", tags_from_file)
    try:
        print("SIEMA3")
        openai.api_key = api_key
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": "You are a helpful assistant."},
                      {"role": "user", "content": f"Provide the most relevant tags for the book about '{search_query}' from the list of available tags: {', '.join(tags_from_file)}"}]
        )
        print("SIEMA4")
        gpt_tags = response.choices[0].message['content'].strip().split(',')
        print(gpt_tags)
        gpt_tags = [tag.strip() for tag in gpt_tags]

    except Exception as e:
        return Response({'error': f'Error contacting GPT: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    query = Q()

    for tag in gpt_tags:
        query |= Q(tags__icontains=tag)

    books = Book.objects.filter(query)

    if not books.exists():
        return Response({'message': 'No books found matching the search query'}, status=status.HTTP_200_OK)

    user_books = Offer.objects.filter(book__in=books).select_related('user', 'book')

    if not user_books.exists():
        return Response({'message': 'No users found with the specified books'}, status=status.HTTP_200_OK)

    book_with_matching_tags = []

    for user_book in user_books:
        matching_tags_count = sum(1 for tag in gpt_tags if tag in user_book.book.tags)
        book_with_matching_tags.append({
            'username': user_book.user.username,
            'title': user_book.book.title,
            'isbn': user_book.book.isbn,
            'author': user_book.book.author,
            'price': user_book.price,
            'offer_id': user_book.id,
            'condition': user_book.condition,
            'cover_book': request.build_absolute_uri(user_book.book.cover_image.url) if user_book.book.cover_image else None,
            'frontImage': request.build_absolute_uri(user_book.front_image.url) if user_book.front_image else None,
            'backImage': request.build_absolute_uri(user_book.back_image.url) if user_book.back_image else None,
            'matching_tags_count': matching_tags_count
        })

    book_with_matching_tags.sort(key=lambda x: x['matching_tags_count'], reverse=True)

    result = book_with_matching_tags[:10]

    return Response(result, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([AllowAny])
def v1_get_offer(request, offer_id):
    try:
        offer = Offer.objects.get(id=offer_id)
        response_data = {
            "offer_id": offer.id,
            "username": offer.user.username,
            "title": offer.book.title,
            "author": offer.book.author,
            "condition": offer.condition,
            "price": offer.price,
            "cover_book": request.build_absolute_uri(offer.book.cover_image.url) if offer.book.cover_image else None,
            "frontImage": request.build_absolute_uri(offer.front_image.url) if offer.front_image else None,
            "backImage": request.build_absolute_uri(offer.back_image.url) if offer.back_image else None,
            "description": "text",
        }

        return Response(response_data, status=status.HTTP_200_OK)

    except Offer.DoesNotExist:
        return Response({'error': 'Offer not found'}, status=status.HTTP_404_NOT_FOUND)
    
@api_view(['GET'])
@permission_classes([AllowAny])
def v1_get_last_added_offers(request):
    latest_offers = Offer.objects.order_by('-created_at')[:10]
    #serializer = OfferSerializer(latest_offers, many=True)
    response_data = []

    for offer in latest_offers:
        # Zbuduj dane dla każdej oferty
        response_data.append({
            "offer_id": offer.id,
            "username": offer.user.username,
            "title": offer.book.title,
            "author": offer.book.author,
            "condition": offer.condition,
            "price": offer.price,
            "cover_book": request.build_absolute_uri(offer.book.cover_image.url) if offer.book.cover_image else None,
            "frontImage": request.build_absolute_uri(offer.front_image.url) if offer.front_image else None,
            "backImage": request.build_absolute_uri(offer.back_image.url) if offer.back_image else None,
            "description": "text",  # Możesz zmienić tekst na dynamiczny, jeśli to konieczne
        })
    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def v2_get_last_added_offers(request):
    pageNumber = int(request.GET.get('pageNumber', 1))  # domyślnie 1, jeśli nie podano
    page_size = int(request.GET.get('pageSize', 10))  # domyślnie 10, jeśli nie podano
    latest_offers = Offer.objects.order_by('-created_at')[pageNumber*page_size: (pageNumber+1)*(page_size)]
    response_data = []

    for offer in latest_offers:
        # Zbuduj dane dla każdej oferty
        response_data.append({
            "offer_id": offer.id,
            "username": offer.user.username,
            "title": offer.book.title,
            "author": offer.book.author,
            "condition": offer.condition,
            "price": offer.price,
            "cover_book": request.build_absolute_uri(offer.book.cover_image.url) if offer.book.cover_image else None,
            "frontImage": request.build_absolute_uri(offer.front_image.url) if offer.front_image else None,
            "backImage": request.build_absolute_uri(offer.back_image.url) if offer.back_image else None,
            "description": "text",  # Możesz zmienić tekst na dynamiczny, jeśli to konieczne
        })
    return Response(response_data, status=status.HTTP_200_OK)

@api_view(['GET'])
@authentication_classes([SessionAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def v1_export_user_offers(request):
    user = request.user
    offers = Offer.objects.filter(user=user)
    file_content = ""
    for offer in offers:
        file_content += f"{offer.book.title}, {offer.price} zł\n"

    # Tworzenie odpowiedzi jako plik tekstowy
    response = HttpResponse(file_content, content_type='text/plain')
    response['Content-Disposition'] = 'attachment; filename="user_books.txt"'
    return response


@api_view(['POST'])
@authentication_classes([SessionAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def v1_change_price(request):
    user = request.user
    offer_id = request.data.get("offer_id")
    new_price = request.data.get("new_price")
    offer = Offer.objects.filter(id=offer_id).first()
    if not offer:
        return Response({"error": "Oferta nie istnieje."}, status=404)

    # Sprawdzenie, czy użytkownik jest właścicielem oferty
    if offer.user != user:
        return Response({"error": "Nie masz uprawnień do zmodyfikowania tej oferty."}, status=403)
    
    offer.price = new_price 
    offer.save()
    return Response({"message": "Cena została zaktualizowana", "new_price": new_price}, status=200)

from .serializers import BookSerializer  # musisz mieć serializer

@api_view(['GET'])
@authentication_classes([SessionAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def v1_check_isbn(request):
    print("DUPA")
    isbn = request.query_params.get('isbn')
    isbn_book = Book.objects.filter(isbn=isbn).first()

    if isbn_book:
        serializer = BookSerializer(isbn_book)
        return Response(serializer.data, status=status.HTTP_200_OK)
    else:
        try:
            s = Scraper(isbn)
            title, author = s.get_info()
            if title is None:
                return Response(status=status.HTTP_404_NOT_FOUND)
            return Response({"title": title, "author": author}, status=status.HTTP_200_OK)
        except Exception:
            return Response(status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@authentication_classes([SessionAuthentication, TokenAuthentication])
@permission_classes([AllowAny])
def v1_analyze_image(request):
    uploaded_file = request.FILES.get('image')
    print("ANALYZE IMAGE")
    if not uploaded_file:
        return Response({"error": "No image file provided."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        img_bytes = uploaded_file.read()
        np_img = np.frombuffer(img_bytes, np.uint8)
        cv_img = cv2.imdecode(np_img, cv2.IMREAD_COLOR)
        print("ROBIE WYCINKE")
        model = YOLO("yolov8x.pt")
        results = model(cv_img)
        print("RESULTS: ", results)
        for result in results:
            for box in result.boxes:
                if int(box.cls.item()) in [73, 63, 67, 62]:  # class IDs likely for books
                    x1, y1, x2, y2 = map(int, box.xyxy[0].cpu().numpy())
                    cropped = cv_img[y1:y2, x1:x2]

                    # Convert to RGB for PIL
                    cropped_rgb = cv2.cvtColor(cropped, cv2.COLOR_BGR2RGB)
                    pil_img = Image.fromarray(cropped_rgb)

                    # Save image to buffer
                    buffer = BytesIO()
                    pil_img.save(buffer, format='JPEG')
                    buffer.seek(0)

                    return HttpResponse(buffer, content_type='image/jpeg')

        return Response({"error": "No book cover detected."}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

    except Exception as e:
        print(f"Image processing error: {e}")
        return Response({"error": "Image processing failed."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
