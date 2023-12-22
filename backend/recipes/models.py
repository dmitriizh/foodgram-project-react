from colorfield.fields import ColorField
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import UniqueConstraint

User = get_user_model()


class Tag(models.Model):


    name = models.CharField(
        verbose_name='Название',
        max_length=25,
        unique=True,
        help_text='Придумайте название для тега',
    )
    color = ColorField(
        verbose_name='Цвет',
        max_length=10,
        unique=True
    )
    slug = models.SlugField(
        verbose_name='Ссылка',
        max_length=10,
        unique=True,
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return f'{self.name} (цвет: {self.color})'


class Ingredient(models.Model):

    name = models.CharField(
        db_index=True,
        verbose_name='Название ингредиента',
        help_text='Напишите название ингредиента',
        max_length=70,
    )
    measurement_unit = models.CharField(
        verbose_name='Единицы измерения',
        max_length=20,
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = (
            models.UniqueConstraint(
                fields=[
                    'name',
                    'measurement_unit',
                ],
                name='unique_name_measurement_unit',
            ),
        )

    def __str__(self):
        return (
            f'{self.name}, {self.measurement_unit}.'
        )


class Recipe(models.Model):

    author = models.ForeignKey(
        User,
        verbose_name='Автор рецепта',
        related_name='recipe_author',
        on_delete=models.CASCADE,
    )
    name = models.CharField(
        verbose_name='Название',
        max_length=70,
        help_text='Придумайте название для рецепта',
    )
    image = models.ImageField(
        verbose_name='Картинка',
        upload_to='recipes/images/',
    )
    text = models.TextField(
        verbose_name='Описание',
        help_text='Опишите рецепт',
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredientAmount',
        related_name='ingredients_in_recipe',
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Тег',
        help_text='Выбирете теги для рецепта',
        related_name='recipe_tags',
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления (в минутах)',
        help_text='Введите время приготовления рецепта',
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True,
    )

    class Meta:
        ordering = ('-pub_date', 'name',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return f'{self.name}, автор {self.author.username}.'


class RecipeIngredientAmount(models.Model):

    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Рецепт',
        on_delete=models.CASCADE,
    )
    ingredient = models.ForeignKey(
        Ingredient,
        verbose_name='Ингредиент',
        on_delete=models.CASCADE,
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество',
    )

    class Meta:
        constraints = (
            models.UniqueConstraint(
                fields=[
                    'recipe',
                    'ingredient',
                ],
                name='unique_recipe_ingredient',
            ),
        )
        ordering = ('recipe', 'ingredient',)
        verbose_name = 'Количество ингредиента в рецепте'

    def __str__(self):
        return (
            f'В {self.recipe.name} содержится '
            f'{self.amount}{self.ingredient.measurement_unit}. '
            f'{self.ingredient.name}.'
        )


class AbstractUsersRecipe(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )

    class Meta:
        abstract = True
        constraints = [
            UniqueConstraint(
                fields=('user', 'recipe'),
                name='%(app_label)s_%(class)s_unique'
            )
        ]

    def str(self):
        return f'{self.user} :: {self.recipe}'


class FavoriteRecipe(AbstractUsersRecipe):

    add_to_favorite_date = models.DateTimeField(
        verbose_name='Дата добавления в избранное',
        auto_now=True,
    )

    class Meta(AbstractUsersRecipe.Meta):
        default_related_name = 'favorites'
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'
        ordering = ('add_to_favorite_date',)


class Cart(AbstractUsersRecipe):

    add_to_shopping_cart_date = models.DateTimeField(
        verbose_name='Дата добавления в корзину',
        auto_now=True,
    )

    class Meta(AbstractUsersRecipe.Meta):
        default_related_name = 'shopping_cart'
        verbose_name = 'Рецепт в корзине'
        verbose_name_plural = 'Рецепты в корзине'
        ordering = ('-id',)
