from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import *
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import UserChangeForm


class RegistrationForm(UserCreationForm):
    role = forms.ChoiceField(choices=CustomUser.ROLE_CHOICES, label="Кем вы хотите быть")

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password1', 'password2', 'role']


class PatientSelectForm(forms.Form):
    patient = forms.ModelChoiceField(queryset=CustomUser.objects.filter(role='patient'), label="Пациент:")


class RegistrationDoctorForm(forms.ModelForm):
    class Meta:
        model = Doctor
        fields = ['img', 'name', 'surname', 'patronymic', 'description', 'experience', 'services', 'address']


class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['datetime']
        widgets = {
            'datetime': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['content']


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'email']

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if CustomUser.objects.exclude(pk=self.instance.pk).filter(username=username).exists():
            raise ValidationError('Это имя пользователя уже занято.')
        return username


class MedicalRecordForm(forms.ModelForm):
    class Meta:
        model = MedicalRecord
        fields = ['doctor', 'prescription', 'results']


class CustomUserChangeForm(UserChangeForm):
    role = forms.ChoiceField(choices=CustomUser.ROLE_CHOICES, label="Роль")

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'role']


class CustomUserCreationForm(UserCreationForm):
    role = forms.ChoiceField(choices=CustomUser.ROLE_CHOICES, label="Роль")

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password1', 'password2', 'role']


class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ['name', 'description', 'price']
        labels = {
            'name': 'Название',
            'description': 'Описание',
            'price': 'Цена',
        }


class DoctorForm(forms.ModelForm):
    class Meta:
        model = Doctor
        fields = ['name', 'surname', 'patronymic', 'description', 'experience', 'address', 'latitude', 'longitude',
                  'img', 'services']
        labels = {
            'name': 'Имя',
            'surname': 'Фамилия',
            'patronymic': 'Отчество',
            'description': 'Описание',
            'experience': 'Стаж (лет)',
            'address': 'Адрес',
            'latitude': 'Широта',
            'longitude': 'Долгота',
            'img': 'Изображение',
            'services': 'Услуги',
        }


class CustomReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['doctor', 'content', 'appointment']
        labels = {
            'doctor': 'Врач',
            'content': 'Текст отзыва',
            'appointment': 'Прием',
        }
        widgets = {
            'content': forms.Textarea(attrs={'rows': 4, 'cols': 50}),
        }


class CustomMedicalRecordForm(forms.ModelForm):
    class Meta:
        model = MedicalRecord
        fields = ['user', 'doctor', 'appointment', 'description', 'results', 'prescription']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'results': forms.Textarea(attrs={'rows': 4}),
            'prescription': forms.Textarea(attrs={'rows': 4}),
        }

    labels = {
        'user': "Пациент",
        'doctor': 'Врач',
        'appointment': 'Приём',
        'description': 'Описание приёма',
        'results': 'Результаты обследования',
        'prescription': 'Назначения и рекомендации',
    }


class CustomAppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['user', 'doctor', 'datetime', 'status', 'service']
        widgets = {
            'datetime': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    labels = {
        'user': 'Пациент',
        'doctor': 'Врач',
        'datetime': 'Дата и время',
        'status': 'Статус',
        'service': 'Услуга',
    }
