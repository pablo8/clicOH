from django.db import transaction
from rest_framework import viewsets
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from ecommerce.models import Product, Order, OrderDetail
from ecommerce.serializers import ProductSerializer, OrderSerializer, OrderDetailSerializer, OrderLiteSerializer
import datetime


class ProductViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, ]
    model = Product
    serializer_class = ProductSerializer
    queryset = Product.objects.all()

    def update(self, request, *args, **kwargs):
        id = kwargs['pk']
        name = request.data.get('name', None)
        price = request.data.get('price', None)
        stock = request.data.get('stock', None)
        try:
            with transaction.atomic():
                product = self.model.objects.get(id=id)
                if name and name != 'string' and name != product.name:
                    product.name = name
                if price and product.price != price:
                    product.price = price
                if stock and stock != product.stock:
                    product.stock = stock
                product.save()

            return Response({
                'detail': 'ok',
                'message': f'Product actualizado correctamente!'
            }, status=status.HTTP_200_OK)
        except Exception as ex:
            return Response({
                'detail': 'error',
                'message': f'Error al actualizar producto:{ex.__str__()}'
            }, status=status.HTTP_406_NOT_ACCEPTABLE)


class OrderViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, ]
    model = Order
    serializer_class = OrderLiteSerializer
    queryset = Order.objects.all()

    def create(self, request, *args, **kwargs):
        """
        :param request: product_list [
        {'id':product_id,
        'quantity':product_quantity}
        ]
        :return: order successfully created or multiples errors
        """
        product_list = request.data.get('product_list', None)
        try:
            if product_list:
                # Check if exist stock
                instance_products = Product.objects.filter(id__in=[p['id'] for p in product_list])
                if instance_products.exclude(stock__gt=1).exists():
                    return Response({
                        'detail': 'error',
                        'message': 'No existe actualmente stock para el producto que intenta incorporar a la orden'
                    }, status=status.HTTP_406_NOT_ACCEPTABLE)
                # Check if product quantity 0
                zero_quantity = len(
                    list(filter(lambda n: n if n['quantity'] <= 0 else None, product_list)))
                if zero_quantity:
                    return Response({
                        'detail': 'error',
                        'message': 'Existen productos con cantidades iguales o inferiores a 0, '
                                   'por favor verifique los valores y vuelva a intentarlo'
                    }, status=status.HTTP_406_NOT_ACCEPTABLE)
                # Check equal products
                repeats_values = [e for e in product_list if product_list.count(e) > 1]
                if repeats_values:
                    return Response({
                        'detail': 'error',
                        'message': 'Ha cargado el mismo producto mas de una vez, por favor verifique y vuelva a intentarlo'
                    }, status=status.HTTP_406_NOT_ACCEPTABLE)

                # Check product stock
                stock_products = instance_products.values('stock')
                stock_fail = [p for index, p in enumerate(product_list) if
                              p['quantity'] > stock_products[index]['stock']]
                if stock_fail:
                    return Response({
                        'detail': 'error',
                        'message': f'Existen productos que exceden el stock maximo disponible! '
                                   'Por favor reingrese los valores teniendo en cuenta el stock diponible'
                    }, status=status.HTTP_406_NOT_ACCEPTABLE)
                else:
                    quantities = [q['quantity'] for q in product_list]
                    add_order = [e for e in instance_products if
                                 str(e.id) in [p['id'] for p in product_list if not stock_fail.__contains__(p)]]
                    try:
                        with transaction.atomic():
                            # Crate instance order
                            order = Order.objects.create()
                            # Create order detail
                            orders_details = [OrderDetail(
                                order=order,
                                product=p,
                                quantity=quantities[index]
                            ) for index, p in enumerate(add_order)]
                            OrderDetail.objects.bulk_create(orders_details)
                            # Update values order
                            order.date_time = datetime.datetime.now()
                            order.get_total()
                            order.get_total_usd()
                            order.save()
                            # Update stock product
                            for index, ip in enumerate(instance_products):
                                ip.update_stock(type=False, q=product_list[index]['quantity'])
                                ip.save()

                    except Exception as ex:
                        return Response({
                            'detail': 'error',
                            'message': f'Se produjo un error al intentar de crear la orden:{ex.__str__()}'
                        }, status=status.HTTP_406_NOT_ACCEPTABLE)
            else:
                return Response({
                    'detail': 'error',
                    'message': 'No existen productos para agregar en la orden'
                }, status=status.HTTP_406_NOT_ACCEPTABLE)

            return Response({
                'detail': 'ok',
                'message': f'La orden fue creada correctamente!'
            }, status=status.HTTP_200_OK)
        except Exception as ex:
            return Response({
                'detail': 'error',
                'message': f'Se genero un error al momento de crear la orden:{ex.__str__()}'
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

    def list(self, request, *args, **kwargs):
        return Response(OrderSerializer(instance=self.model.objects.all(), many=True).data)

    def destroy(self, request, *args, **kwargs):
        order_id = kwargs['pk']
        order = self.model.objects.get(id=order_id)
        get_products = OrderDetail.objects.filter(order_id=order_id).values('product', 'quantity')
        try:
            with transaction.atomic():
                # Restore stock Product
                update_product = [Product.objects.get(id=p['product']).update_stock(type=True, q=p['quantity'])
                                  for p in get_products]
                Product.objects.bulk_update(update_product, ['stock'])
                # Delete order
                order.delete()
                return Response({
                    'detail': 'ok',
                    'message': f'La orden fue eliminada correctamente!'
                }, status=status.HTTP_200_OK)

        except Exception as ex:
            return Response({
                'detail': 'error',
                'message': f'No se pudo actualizar la orden:{ex.__str__()}'
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

    def update(self, request, *args, **kwargs):
        order_id = kwargs['pk']
        order = Order.objects.get(id=order_id)
        product_list = request.data.get('product_list', None)
        try:
            with transaction.atomic():
                product_ids = [p['id'] for p in product_list]
                if product_list:
                    find_original_products = Product.objects.filter(orderdetail__order__id=order_id)
                    # Section exclude products
                    exclude_products = [e for e in find_original_products if not product_ids.__contains__(e.id)]
                    order_details = OrderDetail.objects.filter(order_id=order_id).filter(
                        product__in=exclude_products)
                    restore_quantities = order_details.values('quantity')
                    update_product = []
                    for index, ep in enumerate(exclude_products):
                        ep.update_stock(type=True, q=restore_quantities[index]['quantity'])
                        update_product.append(ep)
                    # Restore stock product
                    Product.objects.bulk_update(update_product, ['stock'])
                    # Delete Order Detail
                    order_details.delete()
                    # Update total and total usd from Order
                    order.get_total()
                    order.get_total_usd()
                    order.save()

                return Response({
                    'detail': 'ok',
                    'message': f'La orden fue actualizada correctamente!'
                }, status=status.HTTP_200_OK)

        except Exception as ex:
            return Response({
                'detail': 'error',
                'message': f'Se ha producido un error al momento de actualizar:{ex.__str__()}'
            }, status=status.HTTP_406_NOT_ACCEPTABLE)


class OrderDetailViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, ]
    model = OrderDetail
    serializer_class = OrderDetailSerializer
    queryset = OrderDetail.objects.all()
