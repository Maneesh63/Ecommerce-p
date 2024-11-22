from common.models import *
from products.models import *
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404
from products.serializers import *
 

class ProductHandler:
    
    @staticmethod
    def create_product(validated_data):
        user=validated_data.pop('user')
        category = validated_data.pop('category')
        product = Product.objects.create(**validated_data, category=category,user=user)
        return product

    @staticmethod
    def get_filtered_products(request):
        search_query = request.query_params.get('search', None)
        ordering = request.query_params.get('ordering', None)

        products = Product.objects.filter(status=True)
        
        if search_query:
            products = products.filter(name__icontains=search_query) | products.filter(description__icontains=search_query)

        if ordering:
            ordering_fields = ordering.split(',')
            valid_fields = ['price', '-price', 'rating', '-rating']
            ordering_fields = [field for field in ordering_fields if field in valid_fields]
            products = products.order_by(*ordering_fields)

        return products

    @staticmethod
    def delete_product(product_id):
        try:
            product = Product.objects.get(product_id=product_id)
            product.delete()
            return {"status": "SUCCESS", "message": "Product deleted successfully."}
        except ObjectDoesNotExist:
            raise ValueError("Product with the provided ID does not exist.")

    @staticmethod
    def update_product(product_id, update_data):
     try:
        # Retrieve the product by product_id
        product = Product.objects.get(product_id=product_id)

        # Handle category update if present
        if 'category' in update_data:
            category_id = update_data.pop('category')
            try:
                category_instance = Category.objects.get(id=category_id)
                update_data['category'] = category_instance
            except Category.DoesNotExist:
                raise ValueError("Category with the provided ID does not exist.")

        # Handle user update if user_id is provided
        if 'user_id' in update_data:
            user_id = update_data.pop('user_id')
            try:
                user_instance = CustomUser.objects.get(user_id=user_id)
                update_data['user'] = user_instance
            except CustomUser.DoesNotExist:
                raise ValueError("User with the provided ID does not exist.")

        # Update the remaining fields dynamically
        for attr, value in update_data.items():
            setattr(product, attr, value)
        
        product.save()  # Save the updated product
        return product

     except Product.DoesNotExist:
        raise ValueError("Product with the provided ID does not exist.")


class CartHandler:
    
    @staticmethod
    def add_cart(request):

        user_id=request.data.get('user_id')
        
        user=get_object_or_404(CustomUser,user_id=user_id)
        product_id=request.data.get('product_id')
        product=get_object_or_404(Product,product_id=product_id)
        
        quantity=request.data.get("quantity")
        cart_item, created = Cart.objects.get_or_create(user=user,product=product)
        
        
        if not created:
          cart_item.quantity += int(quantity)
        else:
            cart_item.quantity = quantity
        cart_item.save()
        
        response = {
                "status": "SUCCESS",
               
                "data": {
                    "cart_id": cart_item.id,
                    "product_id": cart_item.product.product_id,
                    "product_name": cart_item.product.name,
                    "quantity": cart_item.quantity,
                    "user_id": cart_item.user.user_id
                }
            }
        return response




class AddressHandler:

    @staticmethod
    def create_address(validated_data, user):
        """
        Handles the creation of an Address object.
        """
        street_address = validated_data.pop('street_address')
        city = validated_data.pop('city')
        state = validated_data.pop('state')
        postal_code = validated_data.pop('postal_code')
        country = validated_data.pop('country')

       
        address = Address.objects.create(
            street_address=street_address,
            city=city,
            state=state,
            postal_code=postal_code,
            country=country,
            user=user   
        )
        
        return address


    @staticmethod
    def update_address(address_id, validated_data, user):
       
      try:
          address = Address.objects.get(id=address_id, user=user)
      except Address.DoesNotExist:
          raise ValueError("Address not found or doesn't belong to the user.")

         
      address.street_address = validated_data.get('street_address', address.street_address)
      address.city = validated_data.get('city', address.city)
      address.state = validated_data.get('state', address.state)
      address.postal_code = validated_data.get('postal_code', address.postal_code)
      address.country = validated_data.get('country', address.country)
  
      address.save()
      return address

    @staticmethod
    def delete_address(address_id, user):
        """
        Delete an address for the user.
        """
        try:
            address = Address.objects.get(id=address_id, user=user)
        except Address.DoesNotExist:
            raise ValueError("Address not found or doesn't belong to the user.")
        
        address.delete()
        return True

    @staticmethod
    def get_address(address_id, user):
        """
        Retrieve a specific address by its ID for the user.
        """
        try:
            address = Address.objects.get(id=address_id, user=user)
            return address
        except Address.DoesNotExist:
            raise ValueError("Address not found or doesn't belong to the user.")
  
 

# Order handler
class OrderHandler:
    
    @staticmethod
    def create_order(request):
        # Validate cart items
        cart_items = Cart.objects.filter(user=request.user)
        if not cart_items.exists():
            raise ValueError("No items in the cart to create an order.")

     
        address_id = request.data.get("address_id")
        if not address_id:
            raise ValueError("Address ID is required to place an order.")
        
        try:
            address = Address.objects.get(id=address_id, user=request.user)
        except Address.DoesNotExist:
            raise ValueError("The provided address does not exist.")
        order = Order.objects.create(user=request.user, address=address)
        for cart_item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                quantity=cart_item.quantity,
                total_price=cart_item.total_price,
            )

        # Clear the cart after creating the order
        cart_items.delete()

        return order
