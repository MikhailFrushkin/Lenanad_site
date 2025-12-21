# forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth import get_user_model
from .models import Country, City, Role, Department, Store

CustomUser = get_user_model()


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'first_name', 'last_name')


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['photo', 'phone_number', 'birth_date', 'address', 'telegram']
        widgets = {
            'birth_date': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'form-control',
                    'value': lambda: self.instance.birth_date.strftime('%Y-%m-%d') if self.instance.birth_date else ''
                },
                format='%Y-%m-%d'
            ),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+7 (XXX) XXX-XX-XX'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Введите ваш адрес'}),
            'telegram': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'username'}),
            'photo': forms.FileInput(attrs={'class': 'custom-file-input'}),
        }
        labels = {
            'photo': 'Фото профиля',
            'phone_number': 'Номер телефона',
            'birth_date': 'Дата рождения',
            'address': 'Адрес проживания',
            'telegram': 'Telegram',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Делаем все поля необязательными, если это требуется
        for field in self.fields:
            self.fields[field].required = False

        # Устанавливаем значение для birth_date
        if self.instance.birth_date:
            self.fields['birth_date'].widget.attrs['value'] = self.instance.birth_date.strftime('%Y-%m-%d')