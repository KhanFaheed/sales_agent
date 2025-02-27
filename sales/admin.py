from django.contrib import admin

# Register your models here.
from .models import  Product, Sale, Customer,CustomerSale
admin.site.register(Product)
admin.site.register(Sale)
admin.site.register(Customer)
admin.site.register(CustomerSale)
