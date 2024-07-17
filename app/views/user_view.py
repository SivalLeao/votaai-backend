from rest_framework import status
from rest_framework.response import Response
from rest_framework import viewsets
from app.serializers.user_serializer import UserSerializer, ChangePasswordSerializer
from app.services.user_service import UserService
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import action
from django.contrib.auth.models import User


#from app.serializers.ChangePasswordSerializer import ChangePasswordSerializer



class UserViewSet(viewsets.ViewSet):
    _service = UserService()

    def get_permissions(self):
        if self.action in ['list', 'create']:
            self.permission_classes = [AllowAny]
        else:
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()

    # GET
    def list(self, request):
        users = self._service.get_all_users()
        if users['success']:
            return Response(users['data'], status=status.HTTP_200_OK)
        return Response({'error': users['error']}, status=status.HTTP_404_NOT_FOUND)

    # GET
    def retrieve(self, request, pk=None):
        if not pk:
            return Response({'error': 'Missing parameter'}, status=status.HTTP_400_BAD_REQUEST)

        if str(pk).isdigit():
            if len(str(pk)) == 11:
                user = self._service.get_user_by_cpf(pk)
            else:
                user = self._service.get_user_by_id(pk)
        else:
            if '@' in str(pk):
                user = self._service.get_user_by_email(pk)
            else:
                user = self._service.get_user_by_username(pk)

        if user['success']:
            return Response(user['data'], status=status.HTTP_200_OK)

        return Response({'error': user['error']}, status=status.HTTP_404_NOT_FOUND)

    # POST
    def create(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = self._service.create_user(serializer.data)
            if user['success']:
                return Response(user['data'], status=status.HTTP_201_CREATED)
            return Response({'error': user['error']}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # PUT
    def update(self, request, pk=None):
        if not pk:
            return Response({'error': 'Missing parameter'}, status=status.HTTP_400_BAD_REQUEST)

        user = self._service.get_user_by_id(pk)
        if user['success']:
            serializer = UserSerializer(data=request.data)
            if serializer.is_valid():
                user = self._service.update_user(user['data'], serializer.data)
                if user['success']:
                    return Response(user['data'], status=status.HTTP_200_OK)
                return Response({'error': user['error']}, status=status.HTTP_400_BAD_REQUEST)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response({'error': user['error']}, status=status.HTTP_404_NOT_FOUND)
    
    # PATCH
    def partial_update(self, request, pk=None):
        if not pk:
            return Response({'error': 'Missing parameter'}, status=status.HTTP_400_BAD_REQUEST)

        user = self._service.get_user_by_id(pk)
        if user['success']:
            serializer = UserSerializer(user['data'], data=request.data, partial=True)
            if serializer.is_valid():
                updated_user = self._service.update_user(user['data'], serializer.validated_data)
                if updated_user['success']:
                    return Response(updated_user['data'], status=status.HTTP_200_OK)
                return Response({'error': updated_user['error']}, status=status.HTTP_400_BAD_REQUEST)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response({'error': user['error']}, status=status.HTTP_404_NOT_FOUND)

    # DELETE
    def destroy(self, request, pk=None):
        return Response({'error': 'Not Implemented'})

    @action(detail=False, methods=['get', 'patch'], url_path='profile', permission_classes=[IsAuthenticated])
    def user_profile(self, request):
        user_id = request.user.id  # Usa o ID do usuário autenticado
        user = self._service.get_user_by_id(user_id)

        if request.method == 'GET':
            if user['success']:
                return Response(user['data'], status=status.HTTP_200_OK)
            return Response({'error': user['error']}, status=status.HTTP_404_NOT_FOUND)

        if request.method == 'PATCH':
            if user['success']:
                user_instance = user['data']  # Certifique-se de que isso seja uma instância do User
                
                if not isinstance(user_instance, User):
                    return Response({'error': 'Usuário não encontrado.'}, status=status.HTTP_404_NOT_FOUND)

                # Atualizar senha se os dados forem fornecidos
                if 'current_password' in request.data and 'new_password' in request.data:
                    current_password = request.data['current_password']
                    new_password = request.data['new_password']

                    if user_instance.check_password(current_password):
                        user_instance.set_password(new_password)
                        user_instance.save()
                        return Response({'message': 'Senha atualizada com sucesso.'}, status=status.HTTP_200_OK)
                    else:
                        return Response({'error': 'Senha atual incorreta.'}, status=status.HTTP_400_BAD_REQUEST)

                # Atualizar email e username
                serializer = UserSerializer(user_instance, data=request.data, partial=True)
                if serializer.is_valid():
                    updated_user = self._service.update_user(user_instance, serializer.validated_data)
                    if updated_user['success']:
                        return Response(updated_user['data'], status=status.HTTP_200_OK)
                    return Response({'error': updated_user['error']}, status=status.HTTP_400_BAD_REQUEST)

            return Response({'error': user['error']}, status=status.HTTP_404_NOT_FOUND)