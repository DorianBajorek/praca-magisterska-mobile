from loguru import logger
from django.conf import settings
import json

class RequestResponseLoggerMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # Ścieżka do pliku z logami z settings.py (domyślnie 'request_response.log')
        log_file_path = getattr(settings, 'LOG_FILE_PATH', 'request_response.log')
        # Konfiguracja loguru
        logger.add(log_file_path, rotation="10 MB", level="DEBUG")

    def __call__(self, request):
        # Pomijanie logowania zdjęć
        if 'image' in request.content_type:
            return self.get_response(request)

        # Logowanie żądania
        request_body = self._get_request_body(request)
        log_data = {
            'method': request.method,
            'path': request.path,
            'query_params': dict(request.GET),
            'body': self._sanitize_data(request_body),
        }
        logger.debug(f"Request: {json.dumps(log_data, indent=2)}")

        response = self.get_response(request)

        # Pomijanie logowania zdjęć w odpowiedzi
        if 'image' in response.get('Content-Type', ''):
            return response

        # Logowanie odpowiedzi
        response_body = self._get_response_body(response)
        log_data = {
            'status_code': response.status_code,
            'body': self._sanitize_data(response_body),
        }
        logger.debug(f"Response: {json.dumps(log_data, indent=2)}")

        return response

    def _get_request_body(self, request):
        """Pobiera ciało żądania i dekoduje je, jeśli to możliwe."""
        if request.body:
            try:
                # Próba dekodowania jako JSON (dla danych tekstowych)
                return json.loads(request.body.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError):
                # Jeśli nie można zdekodować jako JSON, zwróć informację o danych binarnych
                return "***BINARY DATA***"
        return {}

    def _get_response_body(self, response):
        """Pobiera ciało odpowiedzi."""
        if hasattr(response, 'data'):
            return response.data
        return {}

    def _sanitize_data(self, data):
        """Filtruje wrażliwe dane (hasła, tokeny)."""
        if isinstance(data, dict):
            sanitized_data = {}
            for key, value in data.items():
                if 'password' in key or 'token' in key:
                    sanitized_data[key] = '***FILTERED***'
                else:
                    sanitized_data[key] = value
            return sanitized_data
        return data