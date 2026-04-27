from django.db import transaction

from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets

from rest_framework.permissions import IsAuthenticated, AllowAny

from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework_simplejwt.tokens import RefreshToken

from .models import User, Student, Candidate
from .serializers import UserSerializer, UserRegisterSerializer, RegisterSerializer, StudentSerializer

from rest_framework.decorators import api_view, permission_classes


# Create your views here.
class UserView(APIView):
    """
    API View to get user information
    """

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        responses={
            200: UserSerializer()
        })
    def get(self, request):
        if not request.user or request.user.is_anonymous:
            return Response('User not found', status=status.HTTP_404_NOT_FOUND)

        user = UserSerializer(instance=request.user)

        return Response(data=user.data, status=status.HTTP_200_OK)


class RegisterView(APIView):
    permission_classes = [AllowAny, ]

    @swagger_auto_schema(
        request_body=RegisterSerializer,
        responses={
            201: RegisterSerializer(),
        }
    )
    def post(self, request):
        user = request.data.get('user')

        try:
            user = User.objects.get(email=user.get('email'))
            return Response(data='Email already exists', status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            with transaction.atomic():
                user_serializer = UserRegisterSerializer(data=user)
                if user_serializer.is_valid(raise_exception=True):
                    user_serializer.save()

                refresh: RefreshToken = RefreshToken.for_user(user_serializer.instance)

                return Response(data={
                    'user': user_serializer.data,
                    'token': {
                        'access_token': str(refresh.access_token),
                        'refresh_token': str(refresh),
                    }
                }, status=status.HTTP_201_CREATED)

class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    permission_classes = [IsAuthenticated]


class CandidateViewSet(viewsets.ModelViewSet):
    queryset = Candidate.objects.all()
    serializer_class = StudentSerializer
    permission_classes = [IsAuthenticated]

@api_view(['GET'])
@permission_classes([AllowAny])
def results(request):
    """
    عرض النتائج الحالية للانتخابات: أسماء المرشحين وأصواتهم.
    متاح للجميع.
    """
    candidates = Candidate.objects.select_related('student').all()
    data = {candidate.student.name: candidate.vote_count for candidate in candidates}
    return Response(data)