from itsdangerous import URLSafeTimedSerializer
from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.urls import reverse
import requests
from django.core.exceptions import ValidationError
from typing import Dict, Any
from urllib.parse import urlencode
from django.shortcuts import redirect

GOOGLE_ACCESS_TOKEN_OBTAIN_URL = 'https://oauth2.googleapis.com/token'
GOOGLE_USER_INFO_URL = 'https://www.googleapis.com/oauth2/v3/userinfo'

def generate_email_token(email):
    serializer = URLSafeTimedSerializer(settings.SECRET_KEY)
    return serializer.dumps(email, salt="email-verification-salt")

def confirm_email_token(token):
    serializer = URLSafeTimedSerializer(settings.SECRET_KEY)
    try:
        email = serializer.loads(token, salt="email-verification-salt", max_age=3600)  # Token ważny przez godzinę
    except Exception:
        return None
    return email

def send_verification_email(user):
    token = generate_email_token(user.email)
    verification_link = f"https://www.drugaksiazka.pl/verification/?token={token}"
    subject = "Potwierdź swój adres email"
    message = f"Cześć {user.username},\n\nKliknij poniższy link, aby zweryfikować swój adres email:\n{verification_link}\n\nDziękujemy!"
    send_mail(subject, message, settings.EMAIL_HOST_USER, [user.email])

def send_reset_password_email(user, reset_link):
    subject="Resetowanie hasła drugaksiazka.pl"
    message=f"Kliknij w poniższy link, aby zresetować swoje hasło: {reset_link}"
    send_mail(subject, message, settings.EMAIL_HOST_USER, [user.email])

def send_log_email(type, data):
    if type == "registation":
        subject = "Nowy użytkownik zarejestrowany"
        message = data
        send_mail(subject, message, settings.EMAIL_HOST_USER, ["pawblo28@gmail.com", "dorianb324@gmail.com"])
    if type == "google-info":
        subject = "Rejestracja google"
        message = data
        send_mail(subject, message, settings.EMAIL_HOST_USER, ["pawblo28@gmail.com", "dorianb324@gmail.com"])



# Exchange authorization token with access token
def google_get_access_token(code: str, redirect_uri: str) -> str:
    print(1)
    data = {
        'code': code,
        'client_id': os.getenv("CLIENT_ID"),
        'client_secret': os.getenv("CLIENT_SECRET"),
        'redirect_uri':  "https://drugaksiazka.pl/",
        'grant_type': 'authorization_code'
    }
    response = requests.post(GOOGLE_ACCESS_TOKEN_OBTAIN_URL, data=data)
    if not response.ok:
        raise ValidationError('Could not get access token from Google.')
    access_token = response.json()['access_token']
    return access_token

# Get user info from google
def google_get_user_info(access_token: str) -> Dict[str, Any]:
    response = requests.get(
        GOOGLE_USER_INFO_URL,
        params={'access_token': access_token}
    )

    if not response.ok:
        raise ValidationError('Could not get user info from Google.')
    
    return response.json()


def get_user_data(validated_data):
    domain = "https://drugaksiazka.pl/"
    redirect_uri = "https://drugaksiazka.pl/"

    code = validated_data.get('code')
    error = validated_data.get('error')

    
    access_token = google_get_access_token(code=code, redirect_uri=redirect_uri)
    user_data = google_get_user_info(access_token=access_token)

    # Creates user in DB if first time login
    # User.objects.get_or_create(
    #     username = user_data['email'],
    #     email = user_data['email'],
    #     first_name = user_data.get('given_name'), 
    #     last_name = user_data.get('family_name')
    # )
    
    profile_data = {
        'email': user_data['email'],
        'first_name': user_data.get('given_name'),
        'last_name': user_data.get('family_name'),
    }
    return profile_data

def get_user_info_from_mobile(id_token):
    url = "https://oauth2.googleapis.com/tokeninfo"
    params = {"id_token": id_token}
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Rzuca wyjątek w przypadku błędu HTTP
        print(response.json())
        return response.json()  # Parsuje odpowiedź JSON i zwraca dane
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}