from django.contrib.auth.models import UserManager
from django.db import models
import uuid
from ecommerce.helpers import get_total_usd
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager


class User(AbstractBaseUser):
    first_name = models.CharField(max_length=255, blank=True, null=True)
    last_name = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(max_length=255, unique=True)
    username = models.CharField(max_length=255, blank=True, null=True)
    is_staff = models.BooleanField(default=False, blank=True, null=True)
    is_superuser = models.BooleanField(default=False, blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'username']

    objects = UserManager()

    def __str__(self):
        return f'{self.first_name} ({self.email})'


class Product(models.Model):
    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)
    name = models.CharField(max_length=255, blank=True, null=True)
    price = models.FloatField(default=0, blank=True, null=True)
    stock = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return self.name

    def update_stock(self, type, q):
        """
        :param type:true if add or count product | false is discount product q:quantity
        :return: update_stock
        """
        try:
            self.stock = self.stock - q if not type else self.stock + q
            return self
        except:
            return None


class Order(models.Model):
    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)
    date_time = models.DateTimeField(blank=True, null=True)
    number = models.IntegerField(blank=True, null=True)
    total = models.FloatField(default=0, blank=True, null=True)
    total_usd = models.JSONField(blank=True, null=True)

    def __str__(self):
        return f'Number order: {self.number}'

    def get_total(self):
        total = sum([od.orderdetail_set.filter(order=self).first().quantity * od.price for od in
                     Product.objects.filter(orderdetail__order=self)])
        return total

    def get_total_usd(self):
        total = self.get_total()
        precio_dolar = get_total_usd()
        precio_dolar['total_dolar'] = format(float(total / float(precio_dolar['valor'].replace(',', '.'))), '.2f')
        return precio_dolar

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        total_orders = Order.objects.all()
        if total_orders.count() == 0:
            self.number = 0
        else:
            if self.number == 0:
                self.number = total_orders.order_by('-number').first().number + 1

        self.total = self.get_total()
        self.total_usd = self.get_total_usd()
        super(Order, self).save(force_insert, force_update, using)


class OrderDetail(models.Model):
    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, blank=True, null=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, blank=True, null=True)
    quantity = models.IntegerField(default=0, blank=True, null=True)

    def __str__(self):
        return f'Order:{self.order} |Product:{self.product}|Quantity:{self.quantity}'
