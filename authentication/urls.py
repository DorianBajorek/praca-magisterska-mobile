from django.urls import path
from .views import *

urlpatterns = [
    path('v1/register/', v1_register, name='v1-register'),
    path('v1/login/', v1_login, name='v1-login'),
    path('v1/secured/', v1_secured_view, name='v1-secured'),
    path('v1/logout/', v1_logout, name="v1-logout"),
    path('v1/get_user_data/<str:username>/', get_user_data, name = 'v1-get-user-data'),
    path('v1/verify_email/', verify_email, name = "verify-email"),
    path('v1/is_user_verify/', v1_is_user_verify, name = "v1-is-user-verify"),
    path('v1/request_reset_password/', v1_request_reset_password, name = "v1-request-reset-password"),
    path('v1/change_password/', v1_change_password, name = "v1-change-password"),
    path('v1/google_register/', v1_google_register, name = "v1-google-register"),
    path('v1/update_user_phone_number/', v1_update_user_phone_number, name = "v1-update_user_phone_number"),
    path('v1/delete_user/', v1_delete_user , name = "v1-delete-user" )

]