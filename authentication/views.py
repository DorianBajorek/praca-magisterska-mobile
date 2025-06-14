from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.hashers import check_password
from django.contrib.auth.password_validation import validate_password
from django.core.validators import EmailValidator
from django.contrib.auth.validators import ASCIIUsernameValidator
from .models import UserProfile
from .utils import  *
from smtplib import SMTPException
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode
import random
import ast 

@api_view(['POST'])
@permission_classes([AllowAny])  # Użytkownicy niezalogowani mogą się rejestrować
def v1_register(request):
    username = request.data.get('username')
    password = request.data.get('password')
    email = request.data.get('email')
    phone_number = request.data.get('phoneNumber', "").replace(' ', '')
    ev = EmailValidator()
#    uv = ASCIIUsernameValidator()
    try:
        validate_password(password)
        ev(email)
#        uv(username)
        if len(username) <5 or len(username) > 30:
            raise Exception("Nazwa użytkownika musi mieć długość pomiędzy 5 i 30 znaków")
        
        if not username.isalnum():
            raise Exception("Nazwa użytkownika zawiera niepoprawne znaki")
        
        if User.objects.filter(username=username).exists():
            raise Exception('Nazwa użytkownika jest już zajęta.')
        
        if User.objects.filter(email=email).exists():
            raise Exception('Podany adres e-mail jest już używany.')
        
        if (phone_number !="") ^ (phone_number.isdigit() and len(phone_number) ==9):
            raise Exception("Podano zły numer telefonu" ) 
        
    except Exception as e:
         if "[" in str(e):
             e = ast.literal_eval(str(e))
             e=e[0]
         
         s = str(e)
         if "najmniej 1 znak." in s:
            s=s.replace("znak", "znak specjalny")
         print(s)
         return Response({'error': [s]}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = User.objects.create_user(username=username, password=password, email = email)
        user.save()
        user_profile = UserProfile.objects.create(user = user, phone_number = phone_number)
        user_profile.save()
        try:
            send_verification_email(user)
            send_log_email('registation', user.username)
        except SMTPException as e:
            s=str(s)
            return Response({'error': [s]}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    except Exception as e:
        s=str(e)
        return Response({'error': [s]}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        s=str(e)
        return Response({'error' : [s]},status=status.HTTP_400_BAD_REQUEST)
    
    token, created = Token.objects.get_or_create(user=user)

    return Response({'token': token.key,'username': username, 'email' : email, "phoneNumber" : phone_number}, status=status.HTTP_201_CREATED)

@api_view(['POST'])
@permission_classes([AllowAny])
def verify_email(request):
    token = request.data.get('token')
    if not token:
        return Response({'error': 'Token is required.'}, status=status.HTTP_400_BAD_REQUEST)

    email = confirm_email_token(token)
    if not email:
        return Response({'error': 'Invalid or expired token.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(email=email)
        user.userprofile.is_email_verified = True
        user.userprofile.save()
        return Response({'message': 'Email verified successfully!'}, status=status.HTTP_200_OK)
    except User.DoesNotExist:
        return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([AllowAny])
def v1_login(request):
    username = request.data.get('username')
    password = request.data.get('password')
    user = User.objects.filter(username=username).first()
    if user and user.check_password(password):
        user_profile = UserProfile.objects.filter(user=user).first()
        if user_profile.is_social_register == True:
            return Response({'error': 'Invalid Credentials'}, status=status.HTTP_400_BAD_REQUEST)
        
        token, created = Token.objects.get_or_create(user=user)
        return Response({'token': token.key, 'username' : username, 'email' : user.email}, status=status.HTTP_200_OK)

    return Response({'error': 'Invalid Credentials'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@authentication_classes([SessionAuthentication, TokenAuthentication])  # Użycie tokenu lub sesji do uwierzytelnienia
@permission_classes([IsAuthenticated])  # Dostęp tylko dla zalogowanych użytkowników
def v1_secured_view(request):
    return Response({'message': 'You are authenticated!'}, status=status.HTTP_200_OK)


@api_view(['POST'])
@authentication_classes([SessionAuthentication, TokenAuthentication])  # Użycie tokenu lub sesji do uwierzytelnienia
@permission_classes([IsAuthenticated])  # Dostęp tylko dla zalogowanych użytkowników
def v1_logout(request):
    user = request.user
    try:
        token = Token.objects.get(user=user)
        token.delete()
        return Response({'message': 'Logged out successfully.'}, status=status.HTTP_200_OK)
    except Token.DoesNotExist:
        return Response({'error': 'Token does not exist.'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@authentication_classes([SessionAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def change_password(request):
    user = request.user
    new_password = request.data.get('new_password')
    old_password = request.data.get('old_password')
    if len(new_password) <5:
        return Response({'error': 'Invalid new password'}, status=status.HTTP_400_BAD_REQUEST)
    if not check_password(old_password, user.password):
           return Response({'error': 'Invalid old password'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        user.set_password(new_password)
        user.save()
        Token.objects.filter(user=user).delete()
        new_token, created = Token.objects.get_or_create(user=user)

        return Response({'message': 'Changed password successfully.', 'token' : new_token.key}, status=status.HTTP_200_OK) 
    except:
        return Response({'error': 'Invalid new password'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([AllowAny]) 
def get_user_data(request, username):
    user = User.objects.filter(username=username).first()
    user_profile = UserProfile.objects.filter(user=user).first()
    return Response({'username': user.username, 'email' : user.email, "phoneNumber" : user_profile.phone_number}, status=status.HTTP_201_CREATED)

@api_view(['GET'])
@authentication_classes([SessionAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def v1_is_user_verify(request):
    # ToDo
    user = request.user
    user_profile = UserProfile.objects.filter(user=user).first()
    if user_profile.is_email_verified == True:
        return Response({'IsAuthenticated' : True}, status=status.HTTP_200_OK)
    else:
        return Response({'IsAuthenticated' : False}, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([AllowAny]) 
def v1_request_reset_password(request):
    email = request.data.get('email')

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response({'error': 'Użytkownik z tym adresem e-mail nie istnieje'}, status=404)

    # Generowanie tokena i UID
    token = PasswordResetTokenGenerator().make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    reset_link = f"{request.scheme}://{request.get_host()}/reset-password?uid={uid}&token={token}/"

    send_reset_password_email(user, reset_link)

    return Response({'message': 'Link do resetowania hasła został wysłany.'}, status=200)

@api_view(['POST'])
@permission_classes([AllowAny]) 
def v1_change_password(request):
    uid = request.data.get('uid')
    token = request.data.get('token')
    new_password = request.data.get('new_password')

    try:
        user_id = urlsafe_base64_decode(uid).decode()
        user = User.objects.get(pk=user_id)
    except (User.DoesNotExist, ValueError, TypeError):
        return Response({'error': 'Błąd'}, status=400)

    if not PasswordResetTokenGenerator().check_token(user, token):
        return Response({'error': 'Token jest nieprawidłowy lub wygasł'}, status=400)

    # Zmiana hasła
    user.set_password(new_password)
    user.save()

    return Response({'message': 'Hasło zostało pomyślnie zmienione'}, status=200)



@api_view(['POST'])
@permission_classes([AllowAny]) 
def v1_google_register(request):
    print(request.data)
    print("xdddddddddddddddddddd")
    code = request.data.get('code')
    type = request.data.get('type')
    id_token = request.data.get('id_token')
    print(code, type, id_token)
    print("xdddddddddddddddddddd")
    if type == 'mobile':
        print("xdddddddddddddddddddd1")
        user_data = get_user_info_from_mobile(id_token)
        print(user_data)
        email = user_data.get('email')
        name = user_data.get('name')
        print("xdddddddddddddddddddd2")
    else:
        access_token = google_get_access_token(code,  "https://drugaksiazka.pl/")
        user_info = google_get_user_info(access_token)
        email = user_info['email']
        first_name = user_info.get('given_name')
        last_name = user_info.get('family_name')
    print("xdddddddddddddddddddd3")

    try:
        print("xdddddddddddddddddddd4")
        user = User.objects.filter(email=email).first()
        if user:
            user_profile = UserProfile.objects.filter(user = user).first()
            if user_profile.is_social_register == False:
                return Response({"message" : "Błąd logowania. Zaloguj się za pomocą loginu i hasła"}, status=status.HTTP_404_NOT_FOUND)
            print("xdddddddddddddddddddd5")
            token, _ = Token.objects.get_or_create(user=user)
            return  Response({'token': token.key,'username': user.username, 'email' : user.email, "phoneNumber" : ""}, status=status.HTTP_201_CREATED)
        if type == 'mobile':
            username_base = name
            print("xdddddddddddddddddddd6")
        else:
            username_base = f"{first_name}_{last_name}".lower()
        username = username_base
        print("xdddddddddddddddddddd7")
        while User.objects.filter(username=username).exists():
            username = f"{username_base}_{random.randint(1000, 9999)}"
        print("debug: ",username)
        print("7.1")
        user = User.objects.create_user(
            username=username,
            email=email,
            password = ""
        ) 
        print("7.2")
        print("xdddddddddddddddddddd8")
        try:
            user_profile = UserProfile.objects.create(user = user, phone_number = "")
            user_profile.is_email_verified = True
            user_profile.is_social_register = True
            user_profile.save()
            token, _ = Token.objects.get_or_create(user=user)
            print(token.key, user.username, user.email)
        except Exception as e:
            print(e)
            print("xdddddddddddddddddddd8.5")
            return Response({'message': 'Próba nie powiodła się'}, status=status.HTTP_404_NOT_FOUND)
        return  Response({'token': token.key,'username': user.username, 'email' : user.email, "phoneNumber" : ""}, status=status.HTTP_201_CREATED)
    except:
        print("xdddddddddddddddddddd9")
        return Response({'message': 'Próba nie powiodła się'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['PATCH'])
@authentication_classes([SessionAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def v1_update_user_phone_number(request):
    username = request.user
    new_phone_number = request.data.get("phoneNumber")
    if (new_phone_number !="") ^ (new_phone_number.isdigit() and len(new_phone_number) ==9):
        return Response({'error' : "Zły numer telefonu"}, status=status.HTTP_400_BAD_REQUEST) 
    user = User.objects.filter(username = username).first()
    if  user:
        try:
            user_profile = UserProfile.objects.filter(user=user).first()
            user_profile.phone_number = new_phone_number
            user_profile.save()
        except Exception as e:
            return Response({'message' : 'Zły numer telefonu'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response({'message': 'Zmiana powiodła się'}, status=200)
    return Response({'message': 'Próba nie powiodła się'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['DELETE'])
@authentication_classes([SessionAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def v1_delete_user(request):
    user = request.user
    try:
        user = User.objects.filter(username = user).first()
        user.delete()
        return Response({'message': 'Konto usunięte!'}, status=status.HTTP_200_OK)
    except:
        return Response({'message': 'Próba nie powiodła się'}, status=status.HTTP_404_NOT_FOUND)
