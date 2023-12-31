from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone as tz
from django_filters.rest_framework import DjangoFilterBackend
from djoser.serializers import SetPasswordSerializer
from djoser.views import UserViewSet
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, SAFE_METHODS, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from recipes.models import (Cart, FavoriteRecipe, Ingredient, Recipe,
                            RecipeIngredientAmount, Tag)
from users.models import Subscription, User

from api.filters import IngredientFilter, RecipeFilter
from api.pagination import CartPagination, CustomPagination
from api.permissions import IsAdminOrReadOnly, IsAuthorOrReadOnly
from api.serializers import (DjoserUserSerializer,
                             DjoserUserCreateSerializer,
                             IngredientSerializer,
                             RecipeReadSerializer,
                             RecipeShortSerializer,
                             SubscriptionSerializer,
                             TagSerializer,
                             WriteRecipeSerializer
                             )


class DjoserUserViewSet(UserViewSet):

    queryset = User.objects.all()
    pagination_class = CustomPagination
    permission_classes = (AllowAny,)

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return DjoserUserSerializer
        elif self.action == 'set_password':
            return SetPasswordSerializer
        return DjoserUserCreateSerializer

    @action(
        methods=('get',),
        detail=False,
        permission_classes=[IsAuthenticated],
    )
    def me(self, request):
        """Профиль"""

        serializer = DjoserUserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        methods=['post', 'delete'],
        detail=True,
        permission_classes=[IsAuthenticated],)
    def subscribe(self, request, id):
        if request.method == 'POST':
            author = get_object_or_404(User, id=id)
            serializer = SubscriptionSerializer(
                author,
                data=request.data,
                context={"request": request},
            )
            serializer.is_valid(raise_exception=True)
            Subscription.objects.create(user=request.user, author=author)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        subscription = get_object_or_404(
            Subscription,
            user=request.user,
            author=get_object_or_404(User, id=id),
        )
        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False,
            methods=['get'],
            permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        user = request.user
        subscriptions = User.objects.filter(author_in_subscription__user=user)
        serializer_context = {"request": request}
        paginated_subscriptions = self.paginate_queryset(subscriptions)

        serializer = SubscriptionSerializer(
            paginated_subscriptions,
            many=True,
            context=serializer_context)
        return self.get_paginated_response(serializer.data)


class IngredientViewSet(mixins.ListModelMixin,
                        mixins.RetrieveModelMixin,
                        viewsets.GenericViewSet):

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class TagViewSet(mixins.ListModelMixin,
                 mixins.RetrieveModelMixin,
                 viewsets.GenericViewSet):

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)


class RecipeViewSet(ModelViewSet):

    queryset = Recipe.objects.all()
    permission_classes = (IsAuthorOrReadOnly | IsAdminOrReadOnly,)
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeReadSerializer
        return WriteRecipeSerializer

    @action(
        methods=['post', 'delete'],
        detail=True,
        permission_classes=[IsAuthenticated],)
    def favorite(self, request, pk):
        if request.method == 'POST':
            recipe = get_object_or_404(Recipe, id=pk)
            if FavoriteRecipe.objects.filter(
                user=self.request.user,
                recipe=recipe
            ).exists():
                return Response(
                    {"errors": "Вы уже добавили этот рецепт!"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            FavoriteRecipe.objects.create(
                user=self.request.user,
                recipe=recipe
            )
            serializer = RecipeShortSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        del_favorite = FavoriteRecipe.objects.filter(
            user=self.request.user,
            recipe__id=pk
        )
        if del_favorite.exists():
            del_favorite.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(
            {"errors": "Вы уже удалили этот рецепт!"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @action(
        methods=['post', 'delete'],
        detail=True,
        permission_classes=[IsAuthenticated],)
    def shopping_cart(self, request, pk):
        self.queryset = Cart.objects.all().order_by('-id',)
        self.pagination_class = CartPagination

        if request.method == 'POST':
            recipe = get_object_or_404(Recipe, id=pk)
            if Cart.objects.filter(
                user=self.request.user,
                recipe=recipe
            ).exists():
                return Response(
                    {"errors": "Вы уже добавили этот рецепт!"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            Cart.objects.create(
                user=self.request.user,
                recipe=recipe
            )
            serializer = RecipeShortSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        del_cart = Cart.objects.filter(
            user=self.request.user,
            recipe__id=pk
        )
        if del_cart.exists():
            del_cart.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(
            {"errors": "Вы уже удалили этот рецепт!"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    def cart_text(self, user, ingredients, date):
        text = (
            f'Привет, {user.first_name}!\n\n'
            'Вот твой список покупок на сегодня.\n\n'
            'Нужно купить:\n\n'
        )
        text += '\n'.join([
            f' - {ingredient["ingredient__name"]} '
            f'({ingredient["ingredient__measurement_unit"]})'
            f' - {ingredient["in_shopping_cart_ingredient_amount"]}'
            for ingredient in ingredients
        ])
        text += '\n\nFoodgram.'
        return text

    @action(detail=False,
            methods=['get'],
            permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        self.pagination_class = CartPagination
        ingredients = RecipeIngredientAmount.objects.filter(
            recipe__shopping_cart__user=self.request.user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(
            in_shopping_cart_ingredient_amount=Sum('amount')
        ).order_by('ingredient__name')
        shopping_list_date = tz.now()
        cart_text = self.cart_text(
            self.request.user, ingredients, shopping_list_date
        )

        response = HttpResponse(cart_text, content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; filename="Foodgram_shopping_cart.txt"'
        )
        return response
