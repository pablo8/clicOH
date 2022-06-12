from rest_framework import routers
from ecommerce.viewsets import ProductViewSet, OrderViewSet, OrderDetailViewSet

api_router = routers.SimpleRouter()

# Ecommerce

api_router.register(r'products', ProductViewSet, basename='products')
api_router.register(r'orders', OrderViewSet, basename='orders')
api_router.register(r'order_details', OrderDetailViewSet, basename='order_details')
