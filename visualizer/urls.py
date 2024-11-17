from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from . import views

urlpatterns = [
    path('signup/', views.signup, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('upload/', views.upload_file, name='upload_file'),
    path('display_page/', views.display_page, name='display_page'),  # Corrected the path name for display page
    path('dashboard/', views.dashboard, name='dashboard'),  # Dashboard path
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
