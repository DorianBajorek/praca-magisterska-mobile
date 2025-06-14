from django.urls import path
from .views import *

urlpatterns = [
   path("v1/add_book/", v1_add_book, name = "v1-add-book"),
   path('v1/create_offer/', v1_create_offer, name = "v1-create-offer"),
   path('v1/create_offer_by_title/', v1_create_offer_by_title_author, name = "v1-create-offer_by_title_author"),
   path("v1/get_user_offers/<str:username>/", v1_get_user_offers, name="v1-get-user-offers"),
   path('v1/get_all_offers/', v1_get_all_offers, name = "v1-get-all-offers"),
   path('v1/search_users_with_title/', v1_search_offers_with_title, name = "v1-search-offers-with-title"),
   path('v2/search_users_with_title/', v2_search_offers_with_title, name = "v2-search-offers-with-title"),
   path('v1/delete_offer/<str:offer_id>/', v1_delete_offer, name="v1-delete_offer"),
   path('v1/get_offer/<str:offer_id>/', v1_get_offer, name='v1-get-offer'),
   path('v1/get_last_added_offers/', v1_get_last_added_offers, name = 'get-last-added-offers'),
   path('v2/get_last_added_offers/', v2_get_last_added_offers, name = 'get-last-added-offers'),
   path('v1/analyze_image/', v1_analyze_image, name = 'analyze-image'),

   path('v1/export_user_offers/', v1_export_user_offers, name = 'export-user-offers' ),
   path('v1/change_price/', v1_change_price, name = 'change-price' ),
   path("entries/add_offer/",add_ofer, name = "add-offer"),
   path('entries/get_offer/', get_offer, name = 'get-offer'),
   path('entries/get_latest_offers/', get_latest_offers, name = 'get-latest-books'),
   path('v1/check_isbn/', v1_check_isbn, name = 'check-isbn' ),
]