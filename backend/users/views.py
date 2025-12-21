from pprint import pprint

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.views.decorators.cache import cache_page

from .forms import ProfileUpdateForm
from .models import Country, City, Store


@cache_page(60 * 1)
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