from django.urls import path
from .views import upload_file,get_input
urlpatterns = [
    path('json_data/',upload_file,name = 'json_data'),
    path('',get_input,name = 'get_input'),
]
