"""
URL configuration for ecommerce project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.views import LoginView, LogoutView
from store import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('store.urls')),
    
    # Authentication URLs
    path('login/', LoginView.as_view(template_name='registration/login.html'), name='login'),
    
    # Logout - now pointing to the correct location
    path('logout/', LogoutView.as_view(template_name='store/logout.html'), name='logout'),
    
    path('signup/', views.signup, name='signup'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)