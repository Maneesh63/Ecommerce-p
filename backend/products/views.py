from django.shortcuts import render,get_object_or_404
from rest_framework.views import APIView
from rest_framework import generics
from products.serializers import *
from rest_framework.response import Response
from rest_framework import status
from products.models import Product
from products.handlers import ProductHandler,CartHandler,AddressHandler,OrderHandler
from rest_framework.permissions import IsAuthenticated, AllowAny
from common.backends import CookieJWTAuthentication
from rest_framework.decorators import authentication_classes, permission_classes
import logging
logger = logging.getLogger('custom_logger')
"""code follows structured pattern kindly retrack to understand"""
from functools import wraps


class ProductAPIView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        """
        Override get_permissions to apply dynamic permission classes
        based on the HTTP method.
        """
        if self.request.method == "GET":
            return [AllowAny()]
        return super().get_permissions()  

    def get_authenticators(self):
        if self.request.method == "GET":
            return []
        return super().get_authenticators()
    
    def get(self, request, product_id=None):
        if product_id:
            product = get_object_or_404(Product, product_id=product_id)
            if not product:
             return Response(
                {"message": "No products are available"},
                status=status.HTTP_200_OK
             )
            serializer = ProductSerializer(product)
            return Response(
                {"data":serializer.data},status=status.HTTP_200_OK)

        products = ProductHandler.get_filtered_products(request)
        if not products.exists():
            return Response(
                {"message": "No products are available"},
                status=status.HTTP_200_OK
            )
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
   

    def post(self, request):
        logger.info(f"Authenticated user from view productss: {request.user.email} (ID: {request.user.user_id})")
        serializer = ProductSerializer(data=request.data)
        if serializer.is_valid():
            try:
                product_data = ProductHandler.create_product(serializer.validated_data)
                return Response(
                    {
                        "data": product_data, 
                        "message": "Product created successfully!"
                    },
                    status=status.HTTP_201_CREATED
                )
            except Exception as e:
                return Response(
                    {"error": str(e), "message": "Product creation failed."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(
            {"errors": serializer.errors, "message": "Product creation failed."},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    def delete(self, request, product_id):
        try:
            result = ProductHandler.delete_product(product_id)
            return Response(result, status=status.HTTP_204_NO_CONTENT)
        except ValueError as e:
            return Response(
                {"status": "FAILURE", "error": str(e)}, status=status.HTTP_404_NOT_FOUND
            )

     
    def patch(self, request, product_id):
        """
        Handle partial updates to an existing product.
        """
        try:
            serializer = ProductSerializer(data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            update_data = serializer.validated_data
            updated_product = ProductHandler.update_product(product_id, update_data)

            return Response(
                {
                    "data": updated_product,
                    "message": "Product updated successfully!"
                },
                status=status.HTTP_200_OK
            )

        except ValueError as e:
            return Response(
                {
                    "error": str(e),
                    "message": "Product update failed."
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {
                    "error": str(e),
                    "message": "An unexpected error occurred while updating the product."
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

class CategoryView(generics.ListCreateAPIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    

class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

class CartView(APIView):
   permission_classes = [IsAuthenticated]
   authentication_classes = [CookieJWTAuthentication]
    
   def post(self,request,*args,**kwargs):
       logger.info(f"Authenticated user from views: {request.user.email} (ID: {request.user.user_id})")
       result=CartHandler.add_cart(request)
       if result["status"] == "SUCCESS":
            return Response(
                {"data":result,"message":"Item added successfully"}, status=status.HTTP_200_OK)
        
       return Response(result, status=status.HTTP_400_BAD_REQUEST)
       
   def get(self, request): 
     user=request.user
      
     if user:
        
        cart_items = Cart.objects.filter(user=user)
        if not cart_items:
            return Response({
                "data":"No items in the cart"
            })
        serializer = CartSerializer(cart_items, many=True)

        total_price = sum(item.total_price for item in cart_items)
        
        return Response({'data': serializer.data,
                         'Total_price':total_price}, status=status.HTTP_200_OK)
     else:
        
        return Response(

            {'error': 'User ID is required to retrieve cart items.'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
 
   def delete(self, request, *args, **kwargs):
        cart_id = request.data.get("cart_id")
        
        if not cart_id:
            return Response(
                {'error': 'Item ID is required to remove an item from the cart.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
           
            cart_item = Cart.objects.get(id=cart_id, user=request.user)
            cart_item.delete()
            return Response(
                {'message': 'Item removed from cart successfully'},
                status=status.HTTP_200_OK
            )
        except Cart.DoesNotExist:
            return Response(
                {'error': 'Item not found in your cart.'},
                status=status.HTTP_404_NOT_FOUND
            )

class AddressCreateView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]
    '''Used Serializer Method and handler for DB logic'''
    def post(self, request):
        serializer = AddressSerializer(data=request.data)
        if serializer.is_valid():
            try:
                address = AddressHandler.create_address(serializer.validated_data, request.user)
                address_serializer = AddressSerializer(address)
                return Response({"status": "success", "data": address_serializer.data}, status=status.HTTP_201_CREATED)
            
            except ValueError as e:
                return Response({"status": "FAILURE", "error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"status": "FAILURE", "error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        
    def patch(self, request, address_id):
        """
        Partially update an address.
        """
        serializer = AddressSerializer(data=request.data, partial=True)  # Enable partial updates
        if serializer.is_valid():
            try:
                address = AddressHandler.update_address(
                    address_id=address_id,
                    validated_data=serializer.validated_data,
                    user=request.user,
                )
                address_serializer = AddressSerializer(address)
                return Response({"status": "SUCCESS", "data": address_serializer.data}, status=status.HTTP_200_OK)
            
            except ValueError as e:
                return Response({"status": "FAILURE", "error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"status": "FAILURE", "error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        
    
    def delete(self, request, address_id):
        """
        Delete an address.
        """
        try:
            AddressHandler.delete_address(address_id=address_id, user=request.user)
            return Response({"status": "SUCCESS", "message": "Address deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except ValueError as e:
            return Response({"status": "FAILURE", "error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, address_id):
        """
        Retrieve a specific address.
        """
        try:
            address = AddressHandler.get_address(address_id=address_id, user=request.user)
            address_serializer = AddressSerializer(address)
            return Response({"status": "SUCCESS", "data": address_serializer.data}, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"status": "FAILURE", "error": str(e)}, status=status.HTTP_404_NOT_FOUND)




class OrderCreateView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]
    def post(self, request):
        try:
            order_handler = OrderHandler.create_order(request)
            order_serializer = OrderSerializer(order_handler)
            return Response(
                { "status": "SUCCESS",
                  "message": "Order placed successfully!",
                  "Reference Id":order_handler.order_id
                  },
                status=status.HTTP_201_CREATED
            )
        except ValueError as e:
            return Response(
                {"status": "FAILURE", "error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
  
    def get(self, request):

        try:
            user = request.user
            orders = Order.objects.filter(user=user).order_by('-ordered_at')  # Fetch orders for the user
            serializer = OrderSerializer(orders, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"status": "FAILURE", "error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
  