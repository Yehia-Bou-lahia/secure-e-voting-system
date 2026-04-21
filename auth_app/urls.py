from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import UserView, RegisterView, StudentViewSet, CandidateViewSet

router = DefaultRouter()
urlpatterns = [
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('self', UserView.as_view(), name='user_self_details'),
    path('register/', RegisterView.as_view(), name='user_register')]
router.register(r'student', StudentViewSet, basename='student_viewset')
router.register(r'candidate', CandidateViewSet, basename='candidate_viewset')

urlpatterns = urlpatterns + router.urls
