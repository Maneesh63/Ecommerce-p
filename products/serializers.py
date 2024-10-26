from rest_framework import serializers
from products.models import *
from products.handlers import *




class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['name']
 
class ProductSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())
    
    
    class Meta:
        model = Product
        fields = ['uuid', 'name', 'description', 'price', 'discount_price', 'category', 'rating', 'stock', 'image', 'is_active', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        
        
        handlers=ProductHandler()

        return handlers.create_product(validated_data)

 