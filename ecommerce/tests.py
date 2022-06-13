from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
from ecommerce.models import Product, Order, OrderDetail, User
import datetime


# Product test
class ProductTest(APITestCase):

    def setUp(self):
        self.name = 'product_2'
        self.stock = 12
        self.price = 5
        self.params = {
            'name': self.name,
            'price': self.stock,
            'stock': self.price
        }
        self.update_params = {
            'name': 'product_x',
            'price': 99,
            'stock': 100
        }
        self.product = Product.objects.create(name=self.name, stock=self.stock, price=self.price)
        self.url = '/ecommerce/products/'

    @property
    def bearer_token(self):
        user = User.objects.create(email='a@a.com', password='123', first_name='admin', last_name='admin',
                                   username='admin')

        refresh = RefreshToken.for_user(user)
        return {"HTTP_AUTHORIZATION": f'Bearer {refresh.access_token}'}

    def test_create_product(self):
        response = self.client.post(path=self.url, data=self.params, **self.bearer_token)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        product_id = response.data['id']
        self.assertEqual(response.data['id'], str(Product.objects.get(id=product_id).id))

    def test_list_products(self):
        """
        Listar productos
        """

        response = self.client.get(self.url, **self.bearer_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_get_product(self):
        """
        Listar un producto
        """
        response = self.client.get(f'/ecommerce/products/{self.product.id}/', **self.bearer_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], self.name)
        self.assertEqual(response.data['stock'], self.stock)
        self.assertEqual(response.data['price'], self.price)

    def test_update_product(self):
        """
        Actualizar un producto
        """
        response = self.client.put(
            f'/ecommerce/products/{self.product.id}/',
            data=self.update_params,
            **self.bearer_token
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Product actualizado correctamente!')

    def test_destroy_product(self):
        """
        Eliminar un producto
        """
        response = self.client.delete(
            f'/ecommerce/products/{str(self.product.id)}/', **self.bearer_token
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


# Order test
class OrderTest(APITestCase):

    def setUp(self):
        self.name = 'product_1'
        self.stock = 12
        self.price = 5
        self.product = Product.objects.create(name=self.name, stock=self.stock, price=self.price)
        self.order = Order.objects.create(number=1, date_time=datetime.datetime.now())
        self.params = {
            "product_list": [
                {
                    "id": f"{self.product.id}",
                    "quantity": 1
                }
            ]
        }
        self.update_params = {
            "product_list": []
        }
        self.url = '/ecommerce/orders/'

    @property
    def bearer_token(self):
        user = User.objects.create(email='a@a.com', password='123', first_name='admin', last_name='admin',
                                   username='admin')

        refresh = RefreshToken.for_user(user)
        return {"HTTP_AUTHORIZATION": f'Bearer {refresh.access_token}'}

    def test_create_order(self):
        """
        Crear Orden
        """
        response = self.client.post(path=self.url, data=self.params, **self.bearer_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'La orden fue creada correctamente!')
        total_order = Order.objects.all().count()
        total_order_detail = OrderDetail.objects.all().count()
        self.assertEqual(total_order, 2)
        self.assertEqual(total_order_detail, 1)

    def test_list_order(self):
        """
        Listar ordenes
        """

        response = self.client.get(self.url, **self.bearer_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_get_order(self):
        """
        Listar una orden
        """
        response = self.client.get(f'/ecommerce/orders/{self.order.id}/', **self.bearer_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_order(self):
        """
        Actualizar una orden
        """
        response = self.client.patch(
            f'/ecommerce/orders/{self.order.id}/',
            data=self.update_params,
            **self.bearer_token
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'La orden fue actualizada correctamente!')

    def test_destroy_order(self):
        """
        Eliminar una orden
        """
        response = self.client.delete(
            f'/ecommerce/orders/{str(self.order.id)}/', **self.bearer_token
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'La orden fue eliminada correctamente!')
