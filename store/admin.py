from django.contrib import admin
from django.shortcuts import render, redirect
from django.urls import path
from .models import Product, Category, Order, OrderItem
from django import forms
from django.contrib import messages


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'created_at', 'total_price']
    list_filter = ['created_at']
    inlines = [OrderItemInline]

class CategoryActionForm(forms.Form):
    category = forms.ModelChoiceField(queryset=Category.objects.all(), required=True)

def assign_category(modeladmin, request, queryset):
    if 'apply' in request.POST:
        form = CategoryActionForm(request.POST)
        if form.is_valid():
            category = form.cleaned_data['category']
            count = queryset.update(category=category)
            modeladmin.message_user(request, f"{count} product(s) assigned to category '{category}'.")
            return redirect(request.get_full_path())
    else:
        form = CategoryActionForm()

    return render(request, 'admin/assign_category.html', {
        'products': queryset,
        'form': form,
        'action_checkbox_name': 'action_checkbox',  # ✅ updated line
    })

assign_category.short_description = "Assign selected products to a category"

class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'price']
    fields = ['name', 'price', 'image_url']

admin.site.register(Product, ProductAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(Category)


# Register your models here.
