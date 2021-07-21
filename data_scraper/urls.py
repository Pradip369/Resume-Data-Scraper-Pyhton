from django.urls import path
from django.urls.conf import include
from django.views.generic.base import RedirectView
from django.conf.urls.static import static
from django.conf import settings
from django.contrib import admin

urlpatterns = [
    path('admin/', admin.site.urls),
    path('data_scrape/', include('data_parser.urls')),
    path('', RedirectView.as_view(url = 'data_scrape/')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,document_root = settings.MEDIA_ROOT)