from django.db import models
from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('patient', 'Пациент'),
        ('doctor', 'Доктор'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)


class Service(models.Model):
    name = models.CharField(max_length=150)
    description = models.TextField(null=False, default='Не указано')
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name


class Doctor(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    img = models.ImageField(upload_to='images/', default='images/user.png')
    name = models.CharField(max_length=150, null=False)
    description = models.TextField(null=False, default='Не указано')
    surname = models.CharField(max_length=150, null=False)
    patronymic = models.CharField(max_length=150, null=False)
    experience = models.DecimalField(max_digits=3, decimal_places=0, default=0)
    services = models.ManyToManyField('Service')
    address = models.CharField(max_length=255, default='Не указано')
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} {self.surname}"


class Appointment(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, verbose_name="Пациент")
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, verbose_name="Врач")
    datetime = models.DateTimeField(null=False, verbose_name="Дата и время")
    status = models.CharField(max_length=20, default='scheduled', verbose_name="Статус")
    service = models.ForeignKey(Service, on_delete=models.CASCADE, default=1, verbose_name="Услуга")

    def __str__(self):
        return f"{self.user} - {self.doctor.name} on {self.datetime}"


class Review(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='reviews')
    content = models.TextField()
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, default=1)

    def __str__(self):
        return f"Review by {self.user} for {self.doctor.name}"


class MedicalRecord(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, verbose_name="Пациент")
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, verbose_name="Врач")
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Приём")

    description = models.TextField(verbose_name="Описание приёма", default="Нет описания")
    results = models.TextField(verbose_name="Результаты обследования")
    prescription = models.TextField(verbose_name="Назначения и рекомендации", blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Record for {self.user} by {self.doctor.name}"
