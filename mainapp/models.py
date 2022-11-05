import sys
from PIL import Image
from io import BytesIO
from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.urls import reverse
from django.utils import timezone

User = get_user_model()


def get_models_for_count(*model_names):
    return [models.Count(model_name) for model_name in model_names]


def get_product_url(obj, viewname):
    """Данная функция строит url под один шаблон."""
    ct_model = obj.__class__._meta.model_name
    return reverse(viewname, kwargs={'ct_model': ct_model, 'slug': obj.slug})


class MinResolutionErrorExceptions(Exception):
    pass


class MaxResolutionErrorExceptions(Exception):
    pass


class LatestProductsManager:
    @staticmethod
    def get_products_for_main_page(*args, **kwargs):
        """Вывод на главную страницу 5 первых добавленных товаров"""
        with_respect_to = kwargs.get('with_respect_to')
        products = []
        ct_models = ContentType.objects.filter(model__in=args)
        for ct_model in ct_models:
            model_products = ct_model.model_class()._base_manager.all().order_by('-id')[:5]
            products.extend(model_products)
        if with_respect_to:
            ct_model = ContentType.objects.filter(model=with_respect_to)
            if ct_models.exists():
                if with_respect_to in args:
                    return sorted(products, key=lambda x: x.__class__._meta.model_name.startswith(with_respect_to), reverse=True)
        return products


class LatestProducts:
    objects = LatestProductsManager()


class CategoryManager(models.Manager):
    """ Подсчет продуктов в категории """

    CATEGORY_NAME_COUNT_NAME = {
        'Ноутбуки': 'notebook__count',
        'Смартфоны': 'smartphone__count'
    }

    def get_queryset(self):
        return super().get_queryset()

    def get_categories_for_left_sidebar(self):
        models = get_models_for_count('notebook', 'smartphone')
        qs = list(self.get_queryset().annotate(*models))
        data = [
            dict(name=c.name, url=c.get_absolut_url(), count=getattr(c, self.CATEGORY_NAME_COUNT_NAME[c.name]))
            for c in qs
        ]
        return data


class Category(models.Model):
    name = models.CharField(max_length=255, verbose_name='Имя категории')
    slug = models.SlugField(unique=True)
    objects = CategoryManager()

    def __str__(self):
        return self.name

    def get_absolut_url(self):
        return reverse('category_detail', kwargs={'slug': self.slug})


class Product(models.Model):

    MIN_RESOLUTION = (400, 400)
    MAX_RESOLUTION = (800, 800)
    MAX_IMAGE_SIZE = 3145728

    class Meta:
        abstract = True

    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    title = models.CharField(max_length=255, verbose_name='Наименование')
    slug = models.SlugField(unique=True)
    image = models.ImageField(verbose_name='Изображение')
    descriptions = models.TextField(verbose_name='Описание', null=True)
    price = models.DecimalField(max_digits=9, decimal_places=2, verbose_name='Цена')

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        """ Сжимание загружаемого изображения до размера 200х200"""
        image = self.image
        img = Image.open(image)
        new_img = img.convert('RGB')
        resized_new_image = new_img.resize((200, 200), Image.ANTIALIAS)
        filestream = BytesIO()
        resized_new_image.save(filestream, 'JPEG', quality=90)
        filestream.seek(0)
        name = '{}.{}'.format(*self.image.name.split('.'))
        self.image = InMemoryUploadedFile(
            filestream, 'ImageField', name, 'jpeg/image', sys.getsizeof(filestream), None
        )
        super().save(*args, **kwargs)

    def get_model_name(self):
        """Метод для удаления из корзины."""
        return self.__class__.__name__.lower()


class Notebook(Product):
    diagonal = models.CharField(max_length=255, verbose_name='Диагональ')
    display_type = models.CharField(max_length=255, verbose_name='Тип дисплея')
    processor_freq = models.CharField(max_length=255, verbose_name='Частота процессора')
    ram = models.CharField(max_length=255, verbose_name='Оперативная память')
    video = models.CharField(max_length=255, verbose_name='Видеокарта')
    time_without_charge = models.CharField(max_length=255, verbose_name='Время работы от аккумулятора')

    def __str__(self):
        return "{} : {}".format(self.category.name, self.title)

    def get_absolut_url(self):
        return get_product_url(self, 'product_detail')


class Smartphone(Product):
    diagonal = models.CharField(max_length=255, verbose_name='Диагональ')
    display_type = models.CharField(max_length=255, verbose_name='Тип дисплея')
    resolution = models.CharField(max_length=255, verbose_name='Разрещение экрана')
    acum_volume = models.CharField(max_length=255, verbose_name='Объем батарее')
    ram = models.CharField(max_length=255, verbose_name='Оперативная память')
    sd = models.BooleanField(default=True, verbose_name='НаличиеSD карты')
    sd_volume_max = models.CharField(
        max_length=255, blank=True, null=True, verbose_name='Максимальный объем встраиваемой памяти'
        )
    main_cam_np = models.CharField(max_length=255, verbose_name='Главная камера')
    frontal_cam_np = models.CharField(max_length=255, verbose_name='Фронтальная камера')

    def __str__(self):
        return "{} : {}".format(self.category.name, self.title)

    def get_absolut_url(self):
        return get_product_url(self, 'product_detail')

    # @property
    # def sd(self):
    #     if self.sd:
    #         return 'Да'
    #     return 'Нет'


class CartProduct(models.Model):
    user = models.ForeignKey('Customer', on_delete=models.CASCADE, verbose_name='Пользователь')
    cart = models.ForeignKey('Cart', on_delete=models.CASCADE, related_name='related_products', verbose_name='Корзина')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    qty = models.PositiveIntegerField(default=1)
    final_price = models.DecimalField(max_digits=9, decimal_places=2, verbose_name='Общая цена')

    def __str__(self):
        return "Продукт:{} (для корзины)".format(self.content_object.title)

    def save (self, *args, **kwargs):
        self.final_price = self.qty * self.content_object.price
        super().save(*args, **kwargs)


class Cart(models.Model):

    owner = models.ForeignKey('Customer', null=True, on_delete=models.CASCADE, verbose_name='Владелец')
    products = models.ManyToManyField(CartProduct, blank=True, related_name='related_cart')
    total_products = models.PositiveIntegerField(default=0)
    final_price = models.DecimalField(max_digits=9,default=0, decimal_places=2, verbose_name='Общая цена')
    in_order = models.BooleanField(default=False)
    for_anonymous_user = models.BooleanField(default=False)

    def __str__(self):
        return str(self.id)


class Customer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    phone = models.CharField(max_length=20, null=True, blank=True, verbose_name="Номер телефона")
    address = models.CharField(max_length=255, null=True, blank=True, verbose_name='Адрес')
    orders = models.ManyToManyField('Order', related_name='related_customer', verbose_name='Заказы покупателя.')

    def __str__(self):
        return "Покупатель: {} {}".format(self.user.first_name, self.user.last_name)


class Order(models.Model):
    """ Создание модели самого заказа. """
    STATUS_NEW = 'new'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_READY = 'is_ready'
    STATUS_COMPLETED = 'completed'

    BUYING_TYPE_SELF = 'self'
    BUYING_TYPE_DELIVERY = 'delivery'

    STATUS_CHOICES = (
        (STATUS_NEW,'Новый заказ'),
        (STATUS_IN_PROGRESS, 'Заказ в обработке'),
        (STATUS_READY, 'Заказ готов'),
        (STATUS_COMPLETED, 'Заказ выполнен'),
    )

    BUYING_TYPE_CHOICES = (
        (BUYING_TYPE_SELF, 'Самовывоз'),
        (BUYING_TYPE_DELIVERY, 'Доставка'),

    )

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='related_orders', verbose_name="Покупатель")
    first_name = models.CharField(max_length=255, verbose_name="Имя")
    last_name = models.CharField(max_length=255, verbose_name="Фамилия")
    phone = models.CharField(max_length=255, verbose_name="Телефон")
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE,  null=True, blank=True, verbose_name="Корзина")
    address = models.CharField(max_length=1024, null=True, blank=True, verbose_name="Имя")
    status = models.CharField(
        max_length=100,
        choices=STATUS_CHOICES,
        default=STATUS_NEW,
        verbose_name="Статус заказа",
        )
    buying_type = models.CharField(
        max_length=100,
        choices=BUYING_TYPE_CHOICES,
        default=BUYING_TYPE_SELF,
        verbose_name="Тип заказа",
        )
    comment = models.TextField(max_length=1024, null=True, blank=True, verbose_name="Комментарий к заказу")
    createt_at = models.DateTimeField(auto_now=True, verbose_name="Дата создания заказу")
    order_date = models.DateField(verbose_name="Дата получения заказа", default=timezone.now)

    def __str__(self):
        return str(self.id)
