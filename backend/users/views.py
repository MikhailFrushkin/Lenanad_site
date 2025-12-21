from pprint import pprint

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from .forms import ProfileUpdateForm
from .models import Country, City, Store

#
# @login_required
# def profile_edit(request):
#     """Редактирование профиля пользователя"""
#     user = request.user
#
#     if request.method == 'POST':
#         form = ProfileUpdateForm(request.POST, request.FILES, instance=user)
#         if form.is_valid():
#             form.save()
#             messages.success(request, 'Профиль успешно обновлен!')
#             return redirect('users:profile_edit')
#         else:
#             messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
#     else:
#         form = ProfileUpdateForm(instance=user)
#
#     country_id = user.country.id if user.country else None
#     countries = Country.objects.get(id=country_id) if country_id else Country.objects.all()
#
#     city_id = user.city.id if user.city else None
#     cities = City.objects.get(id=city_id) if city_id else City.objects.all()
#
#     store_id = user.store.id if user.store else None
#     stores = Store.objects.get(id=city_id) if store_id else Store.objects.all()
#
#     context = {
#         'form': form,
#         'countries': countries,
#         'cities': cities,
#         'stores': stores,
#         'user': user,
#     }
#     pprint(context)
#
#     return render(request, 'users/profile_edit.html', context)
#
@login_required
def profile_edit(request):
    """Редактирование профиля пользователя"""
    user = request.user

    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профиль успешно обновлен!')
            return redirect('users:profile_edit')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else:
        form = ProfileUpdateForm(instance=user)

    context = {
        'form': form,
        'user': user,
    }

    return render(request, 'users/profile_edit.html', context)