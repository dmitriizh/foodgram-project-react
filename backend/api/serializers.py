from django.db.models import F
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import (IntegerField, ModelSerializer,
                                        PrimaryKeyRelatedField,
                                        SerializerMethodField)
from rest_framework.status import HTTP_400_BAD_REQUEST

from api.constants import (LENGTH_MIN_MEANING,
                           LENGTH_MAX_MEANING,
                           LENGTH_MAX_VALUE,
                           )
from recipes.models import Ingredient, Recipe, RecipeIngredientAmount, Tag
from users.models import User


class DjoserUserCreateSerializer(UserCreateSerializer):

    class Meta:
        model = User
        fields = (
            'email',
            'username',
            'id',
            'first_name',
            'last_name',
            'password',
        )


class DjoserUserSerializer(UserSerializer):

    is_subscribed = SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id',
                  'username', 'first_name',
                  'last_name', 'is_subscribed')

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        return bool(request and request.user.is_authenticated
                    and obj.subscriber_user.filter(user=request.user).exists())


class SubscriptionSerializer(DjoserUserSerializer):

    recipes = SerializerMethodField()
    recipes_count = SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
        )
        read_only_fields = (
            'email',
            'username',
            'first_name',
            'last_name',
            'recipes',
        )

    def get_recipes_count(self, obj):
        return obj.recipe_author.count()

    def get_recipes(self, obj):
        recipes_limit = self.context['request'].GET.get('recipes_limit')

        try:
            recipes_limit_int = int(recipes_limit) if recipes_limit else None
        except (ValueError, TypeError):
            recipes_limit_int = None

        recipes = obj.recipe_author.all()[:recipes_limit_int]if recipes_limit_int else obj.recipe_author.all()
        return RecipeShortSerializer(recipes, many=True, read_only=True).data

    def validate(self, data):
        author = self.instance
        user = self.context['request'].user
        if user.subscriber_user.filter(author=author).exists():
            raise ValidationError(
                detail='Нельзя подписаться дважды!',
                code=HTTP_400_BAD_REQUEST
            )
        if user == author:
            raise ValidationError(
                detail='Нельзя подписаться на себя!',
                code=HTTP_400_BAD_REQUEST
            )
        return data


class RecipeShortSerializer(ModelSerializer):

    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time',
        )
        read_only_fields = (
            'id',
            'name',
            'image',
            'cooking_time',
        )


class TagSerializer(ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug',)
        read_only_fields = '__all__'


class IngredientSerializer(ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit',)
        read_only_fields = '__all__'


class RecipeIngredientAmountSerializer(ModelSerializer):

    id = IntegerField(write_only=True)
    amount = IntegerField(min_value=LENGTH_MIN_MEANING,
                          max_value=LENGTH_MAX_MEANING
                          )

    class Meta:
        model = RecipeIngredientAmount
        fields = (
            'id',
            'amount',
        )


class RecipeReadSerializer(ModelSerializer):

    author = DjoserUserSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    is_favorited = SerializerMethodField()
    is_in_shopping_cart = SerializerMethodField()
    ingredients = SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def get_is_favorited(self, obj):
        user = self.context['request'].user
        if user and not user.is_anonymous:
            related_manager = getattr(user, 'favorites')
            return related_manager.filter(recipe=obj).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        if not user.is_anonymous:
            related_manager = getattr(user, 'shopping_cart')
            return related_manager.filter(recipe=obj).exists()
        return False

    def get_ingredients(self, obj):
        return (
            obj.ingredients.values(
                'id',
                'name',
                'measurement_unit',
                amount=F('recipeingredientamount__amount')
            )
        )


class WriteRecipeSerializer(ModelSerializer):

    ingredients = RecipeIngredientAmountSerializer(many=True)
    tags = PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
    )
    image = Base64ImageField()
    author = DjoserUserSerializer(read_only=True)
    cooking_time = IntegerField(
        min_value=LENGTH_MIN_MEANING,
        max_value=LENGTH_MAX_VALUE,
    )

    class Meta:
        model = Recipe
        fields = (
            'id',
            'ingredients',
            'tags',
            'author',
            'image',
            'name',
            'text',
            'cooking_time',
        )

    def validate(self, obj):
        if not obj.get('tags'):
            raise ValidationError(
                'Добавьте хотя бы один тег!'
            )
        tags_list = []
        for tag in obj.get('tags'):
            if tag in tags_list:
                raise ValidationError(
                    {'tags': 'Теги должны быть уникальными!'}
                )
            tags_list.append(tag)
        if not obj.get('image'):
            raise ValidationError(
                'Нужно добавить изображение'
            )
        if not obj.get('ingredients'):
            raise ValidationError(
                'Добавьте хотя бы один ингредиент!'
            )
        inrgedient_id_list = [item['id'] for item in obj.get('ingredients')]
        unique_ingredient_id_list = set(inrgedient_id_list)
        if len(inrgedient_id_list) != len(unique_ingredient_id_list):
            raise ValidationError(
                'Ингредиенты должны быть уникальны.'
            )
        return obj

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')

        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)

        for ingredient in ingredients:
            ingredient_id = ingredient['id']
            amount = ingredient['amount']

            try:
                ingredient_obj = Ingredient.objects.get(id=ingredient_id)
            except Ingredient.DoesNotExist:
                raise ValidationError(
                    {'ingredients': f'Ингредиент с id {ingredient_id}'
                     'не существует.'}
                )

            RecipeIngredientAmount.objects.create(
                recipe=recipe,
                ingredient=ingredient_obj,
                amount=amount
            )

        return recipe

    def update(self, instance, validated_data):
        if 'tags' in validated_data:
            instance.tags.clear()
            instance.tags.set(validated_data.pop('tags'))
        if 'ingredients' in validated_data:
            RecipeIngredientAmount.objects.filter(recipe=instance).delete()
            ingredients = validated_data.pop('ingredients')
            for ingredient in ingredients:
                ingredient_id = ingredient['id']
                amount = ingredient['amount']

            try:
                ingredient_obj = Ingredient.objects.get(id=ingredient_id)
            except Ingredient.DoesNotExist:
                raise ValidationError(
                    {'ingredients': f'Ингредиент с id {ingredient_id}'
                     'не существует.'}
                )
            RecipeIngredientAmount.objects.create(
                recipe=instance,
                ingredient=ingredient_obj,
                amount=amount
            )
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        request = self.context['request']
        context = {'request': request}
        return RecipeReadSerializer(
            instance=instance,
            context=context,
        ).data
