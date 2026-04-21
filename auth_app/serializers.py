import re

from django.db import transaction
from drf_yasg.utils import swagger_serializer_method

from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from auth_app.models import User, Student, Candidate


class ProfileSerializer(serializers.Serializer):
    name = serializers.CharField(read_only=True, max_length=255)


class UserSerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField()

    @swagger_serializer_method(serializer_or_field=ProfileSerializer)
    def get_profile(self, instance: User):
        try:
            name = None
            if instance.role in ('student', 'candidate'):
                student = Student.objects.get(user=instance)
                name = student.name
            return {
                "name": name,
            }
        except Student.DoesNotExist:
            raise ValidationError('Inactive user')

    class Meta:
        model = User
        fields = ('id', 'email', 'profile',)


class UserRegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    """
    password = serializers.CharField(required=True, write_only=True)
    name = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        if not re.match(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&#_.])[A-Za-z\d@$!%*?&#_.]{8,20}$",
                        attrs.get('password')):
            raise ValidationError(
                (
                    "Password must be at least 8 characters long, has at least 1 digit, 1 lowercase, 1 uppercase and 1 special character (@, $, !, %, *, ?, &, _, .)"))
        return attrs

    class Meta:
        model = User
        fields = ('email', 'password', 'name', 'role')
        read_only_fields = ('id', 'role')

    @transaction.atomic
    def create(self, validated_data):
        """
        Create a new user instance.

        Args:
            validated_data (dict): The validated data for creating the user.

        Returns:
            User: The created user instance.
        """
        name = validated_data.pop('name')

        user = User(
            is_active=True,
            email=validated_data['email'],
            username=validated_data['email'],
        )
        user.set_password(validated_data['password'])
        user.save()

        Student.objects.create(user=user, name=name)

        return user


class RefreshTokenSerializer(serializers.Serializer):
    refresh_token = serializers.CharField(required=True)
    access_token = serializers.CharField(required=True)


class RegisterSerializer(serializers.Serializer):
    user = UserRegisterSerializer(required=True)
    token = RefreshTokenSerializer(read_only=True)


class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = ('id', 'name', 'created_at', 'updated_at')


class CandidateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Candidate
        fields = ('id', 'name', 'created_at', 'updated_at')
