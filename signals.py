from django.db.models.signals import post_save,post_delete
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import Customer,Product
from elasticsearch import Elasticsearch

es=Elasticsearch("http://localhost:9200")
def index_product(product):
    doc={
        "name":product.name,
        "category":product.category.name if product.category else " ",
        "price":product.price,
        "digital":product.digital,
        "manufacturer":product.manufacturer or "",
        "description":product.description or "",
        "image_url":product.imageURL,
    }
    es.index(index="products",id=product.id,document=doc)
def delete_product(product_id):
    es.delete(index="products",id=product_id,ignore=[404])

@receiver(post_save, sender=Product)
def update_index(sender, instance, **kwargs):
    index_product(instance)
    
@receiver(post_delete, sender=Product)
def delete_from_index(sender, instance, **kwargs):
    delete_product(instance.id)

@receiver(post_save, sender=User)
def create_customer(sender, instance, created, **kwargs):
    if created:  
        Customer.objects.create(
            user=instance,
            name=instance.username,  
            email=instance.email
        )

