from rest_framework import serializers
from ecommerce.models import *
from ecommerce.helpers import format_str


class ProductSerializer(serializers.ModelSerializer):
    dolar_price = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['id', 'name', 'price', 'dolar_price', 'stock']

    @staticmethod
    def get_dolar_price(obj):
        precio_dolar = get_total_usd()
        return format(float(obj.price / float(precio_dolar['valor'].replace(',', '.'))), '.2f')


class ProductLiteSerializer(serializers.Serializer):
    id = serializers.CharField()
    quantity = serializers.IntegerField()

    class Meta:
        fields = ['id', 'quantity']


class OrderLiteSerializer(serializers.Serializer):
    product_list = serializers.ListField(child=ProductLiteSerializer())

    class Meta:
        fields = ['product_list']


class OrderSerializer(serializers.ModelSerializer):
    details_order = serializers.SerializerMethodField()
    date = serializers.SerializerMethodField()
    total_dolar = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ['id', 'total', 'total_dolar', 'date', 'details_order']

    @staticmethod
    def get_details_order(obj):
        return OrderDetailSerializer(OrderDetail.objects.filter(order=obj), many=True).data

    @staticmethod
    def get_date(obj):
        return format_str(obj.date_time)

    @staticmethod
    def get_total_dolar(obj):
        return obj.total_usd['total_dolar']


class OrderDetailLiteSeriazer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['name', 'price']


class OrderDetailSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()

    class Meta:
        model = OrderDetail
        fields = ['name', 'price', 'quantity']

    @staticmethod
    def get_name(obj):
        return obj.product.name

    @staticmethod
    def get_price(obj):
        return obj.product.price
