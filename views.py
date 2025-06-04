from django.shortcuts import render,get_object_or_404
from django.http import JsonResponse,HttpResponse
from django.contrib.auth import authenticate,login
from django.core.exceptions import ValidationError
from .models import *
from django.contrib.auth.forms import AuthenticationForm
import json
from .utils import cookiecart
from elasticsearch import Elasticsearch
def search_results(query):
    es = Elasticsearch("http://localhost:9200")
    products=[]
    body={
            "query":{
                "multi_match":{
                    "query":query,
                    "fields":["name","manufacturer","description"],
                    "fuzziness":"AUTO"
                }
            }
        }
    response = es.search(index="products", body=body)
    hits = response["hits"]["hits"]
    product_ids = [hit["_id"] for hit in hits]
    return Product.objects.filter(id__in=product_ids)

def store(request,category_id):
    if request.user.is_authenticated:
        customer=request.user.customer
        order,created=Order.objects.get_or_create(customer=customer,complete=False)
        items=order.orderitem_set.all()
        carttotal=order.get_cart_items
    else:
        cookiedata=cookiecart(request)
        carttotal=cookiedata['carttotal']
        order=cookiedata['order']
        items=cookiedata['items']
    search_query=request.GET.get('q')
    if search_query:
        products=search_results(search_query)
        category=None
    else:
        if category_id:
          category = get_object_or_404(Category,pk=category_id)
          products = Product.objects.filter(category=category)
        else:
            products = Product.objects.all()
            category = None
    context = {'products': products,'category':category,'carttotal':carttotal,'items':items,'order':order}
    return render(request, 'store/store.html', context)
def homepage(request):
     if request.user.is_authenticated:
         customer=request.user.customer
         order,created=Order.objects.get_or_create(customer=customer,complete=False)
         carttotal=order.get_cart_items
     else:
         cart = json.loads(request.COOKIES.get('cart', '{}'))
         carttotal = sum([item['quantity'] for item in cart.values()])
         
     categories=Category.objects.all()
     context={'categories':categories,'carttotal':carttotal}
     return render(request,'store/home.html',context)
def product_detail(request,pk):
    try:
       product = Product.objects.get(id=pk)
       context={'product':product}
       return render(request,'store/product.html',context)
    except Product.DoesNotExist:
       return HttpResponse("Product not found", status=404)

def cart(request):
    if request.user.is_authenticated:
        customer = request.user.customer
        order, created = Order.objects.get_or_create(customer=customer, complete=False)
        items = order.orderitem_set.all()
        carttotal = order.get_cart_items
    else:
        cookiedata = cookiecart(request) 
        carttotal = cookiedata['carttotal']
        order = cookiedata['order']
        items = cookiedata['items']

    context = {'items': items, 'order': order, 'carttotal': carttotal}
    return render(request, 'store/cart.html', context)


def checkout(request):
    if request.user.is_authenticated:
        customer = request.user.customer
        order, created = Order.objects.get_or_create(customer=customer, complete=False)
        items = order.orderitem_set.all()
        carttotal = order.get_cart_items
    else:
        cookiedata = cookiecart(request)
        carttotal = cookiedata['carttotal']
        order = cookiedata['order']
        items = cookiedata['items']

    context = {'items': items, 'order': order, 'carttotal': carttotal}
    return render(request, 'store/checkout.html', context)

from django.http import JsonResponse
import json
from .models import *

def updateItem(request):
    data = json.loads(request.body)
    productid = data['productid']
    action = data['action']
    size = data.get('size', 'M')
    customer = request.user.customer
    product = Product.objects.get(id=productid)
    order, created = Order.objects.get_or_create(customer=customer, complete=False)
    orderitem, created = Orderitem.objects.get_or_create(order=order, product=product,size=size)

    if action == 'add':
        orderitem.quantity += 1
    elif action == 'remove':
        orderitem.quantity -= 1
    
    if orderitem.quantity<=0:
         orderitem.delete()
         itemprice='$ 0'
         itemquantity=0
    else:
         orderitem.save()
         itemprice='$'+str(orderitem.quantity*orderitem.product.price)
         itemquantity = orderitem.quantity

    cartItems = order.get_cart_items
    cartTotal = '$'+ str(order.get_cart_total)
    return JsonResponse({
        'cartItems': cartItems,
        'cartTotal': cartTotal,
        'itemprice':itemprice,
        'itemquantity':itemquantity,
    })

def loginview(request):
    if request.method == 'GET':
        form = AuthenticationForm()
        return render(request, 'store/login.html', {'form': form})

    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return JsonResponse({'message': 'Login successful'}, status=200)
            else:
                return JsonResponse({'error': 'Invalid username or password'}, status=401)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

    return JsonResponse({'error': 'Only GET and POST methods allowed'}, status=405)

from django.shortcuts import render, redirect
from .forms import CustomUserCreationForm

def signupview(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')  
    else:
        form = CustomUserCreationForm()
    return render(request, 'store/signup.html', {'form': form})
def profileview(request):
    user=request.user
    customer=request.user.customer
    alladdress=Shippingaddress.objects.filter(customer=customer)
    context={'user':user,'addresses':alladdress}
    return render(request,'store/profile.html',context)
def myorders(request):
    customer = request.user.customer  
    totalorders = Order.objects.filter(customer=customer, complete=True) 
    orders = [] 

    for order in totalorders:
        items = Orderitem.objects.filter(order=order)  
        item = {
            'Transaction_id': order.transaction_id,
            'date_ordered': order.date_ordered,
            'total_items': order.get_cart_items,
            'total_amount': order.get_cart_total,
            'items': [] 
        }
        for i in items:
            item['items'].append({
                'name': i.product.name,
                'price': i.product.price,
                'size': i.size,
                'quantity': i.quantity,
                'total_price': i.get_total
            })
        orders.append(item)  
    context = {'orders': orders}
    return render(request, 'store/myorders.html', context)
es=Elasticsearch("http://localhost:9200")
def search_suggestions(request):
    query=request.GET.get("q","")
    if not query:
        return JsonResponse({'suggestions':[]})
    body={
        "suggest":{
            "product_suggest":{
                "prefix":query,
                "completion":{
                    "field":"name_suggest",
                    "size":5
                }
            }
        }
    }
    response=es.search(index="products",body=body)
    suggestions=[]
    if "suggest" in response:
        for options in response['suggest']['product_suggest'][0]['options']:
            suggestions.append(options["_source"]["name"])
    return JsonResponse ({'suggestions':suggestions})





