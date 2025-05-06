from django.shortcuts import get_object_or_404
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required
from .forms import *
from django.utils.timezone import localtime
from django.db.models import Q
import uuid
import requests
from django.db.models import Count
from collections import defaultdict
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.core.mail import send_mail
from django.contrib import messages
import django
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "diploma.settings")
django.setup()

from django.conf import settings

def home(request):
    doctors = Doctor.objects.all()
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.user = request.user
            appointment.doctor_id = request.POST.get('doctor')
            appointment.save()
            if hasattr(request.user, 'role'):
                if request.user.role == 'doctor':
                    return redirect('doctor_dashboard')
                else:
                    return redirect('home')
            else:
                return redirect('home')
    else:
        form = AppointmentForm()
    return render(request, 'home.html', {'doctors': doctors, 'form': form})


def register_patient(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            email = form.cleaned_data.get('email')
            if CustomUser.objects.filter(username=username).exists():
                messages.error(request, 'Пользователь с таким именем уже существует.')
            elif CustomUser.objects.filter(email=email).exists():
                messages.error(request, 'Пользователь с такой почтой уже зарегистрирован.')
            else:
                user = form.save()
                login(request, user)
                send_mail(
                    'Регистрация прошла успешно',
                    'Добро пожаловать!',
                    'e02616920@gmail.com',
                    [user.email],
                    fail_silently=False,
                )
                if user.role == 'doctor':
                    return redirect('register_doctor')
                else:
                    return redirect('home')
    else:
        form = RegistrationForm()
    return render(request, 'register_patient.html', {'form': form})


def get_coordinates(address):
    url = 'https://nominatim.openstreetmap.org/search'
    params = {
        'q': address,
        'format': 'json'
    }
    response = requests.get(url, params=params, headers={'User-Agent': 'Mozilla/5.0'})
    if response.status_code == 200 and response.json():
        data = response.json()[0]
        return float(data['lat']), float(data['lon'])
    return None, None


def register_doctor(request):
    services = Service.objects.all()
    if request.method == 'POST':
        form = RegistrationDoctorForm(request.POST, request.FILES)
        if form.is_valid():
            doctor = form.save(commit=False)
            doctor.user = request.user
            address = form.cleaned_data.get('address')
            lat, lon = get_coordinates(address)
            doctor.latitude = lat
            doctor.longitude = lon
            doctor.save()
            form.save_m2m()
            return redirect('doctor_dashboard')
    else:
        form = RegistrationDoctorForm()
    return render(request, 'register_doctor.html', {'services': services, 'form': form})


def update_user(request):
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=request.user)

        if form.is_valid():
            user = form.save(commit=False)
            if CustomUser.objects.exclude(id=user.id).filter(email=user.email).exists():
                form.add_error('email', 'Этот email уже используется.')
            if CustomUser.objects.exclude(id=user.id).filter(username=user.username).exists():
                form.add_error('username', 'Это имя пользователя уже занято.')
            if form.errors:
                return render(request, 'update_user.html', {'form': form})
            user.save()
            send_mail(
                'Изменение данных аккаунта',
                'Ваши данные были успешно обновлены.',
                'e02616920@gmail.com',
                [user.email],
                fail_silently=False,
            )
            return redirect(request.META.get('HTTP_REFERER', 'dashboard'))
    else:
        form = UserUpdateForm(instance=request.user)

    return render(request, 'update_user.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if username == 'admin' and password == 'admin':
                return redirect('admin_panel')

            if hasattr(user, 'doctor'):
                return redirect('doctor_dashboard')
            else:
                return redirect('home')
    return render(request, 'login.html')


def user_info_view(request):
    user = request.user
    if user.role == 'doctor':
        doctor = Doctor.objects.get(user=user)
        return render(request, '', {'doctor': doctor})
    elif user.role == 'patient':
        return render(request, '', {'user': user})


@login_required
def dashboard(request):
    if request.user.role == 'doctor':
        return doctor_dashboard(request)
    elif request.user.role == 'patient':
        return patient_dashboard(request)


def patient_dashboard(request):
    appointments = Appointment.objects.filter(
        user=request.user,
        status__in=['completed', 'scheduled']
    )

    reviewed_appointments = Review.objects.filter(
        user=request.user
    ).values_list('appointment_id', flat=True)

    return render(request, 'dashboard.html', {
        'appointments': appointments,
        'reviewed_appointments': reviewed_appointments,
    })


@login_required
def doctor_dashboard(request):
    if request.user.role != 'doctor':
        return redirect('home')

    try:
        doctor = Doctor.objects.get(user=request.user)
    except Doctor.DoesNotExist:
        return redirect('register_doctor')

    appointments = Appointment.objects.filter(doctor=doctor, status='scheduled')
    return render(request, 'doctor_dashboard.html', {'appointments': appointments})


@login_required
def create_medical_record(request):
    if request.method == 'POST':
        form = MedicalRecordForm(request.POST)
        if form.is_valid():
            record = form.save(commit=False)
            record.user = request.user
            record.save()
            return redirect('dashboard')
    else:
        form = MedicalRecordForm()
    return render(request, 'create_medical_record.html', {'form': form})


@login_required
def cancel_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id, user=request.user)
    appointment.status = 'canceled'
    appointment.save()
    return redirect('home')


@login_required
def doctor_detail(request, doctor_id):
    doctor = get_object_or_404(Doctor, id=doctor_id)
    return render(request, 'doctor_detail.html', {'doctor': doctor})


@login_required
def doctor_home(request):
    users = CustomUser.objects.filter(user=request.user)
    return render(request, 'doctor_home.html', {'users': users})


@login_required
def video(request, room_name):
    return render(request, 'video.html', {
        'room_name': room_name,
        'user': request.user,
    })


@login_required
def select_patient_view(request):
    if request.method == 'POST':
        form = PatientSelectForm(request.POST)
        if form.is_valid():
            patient = form.cleaned_data['patient']
            room_name = f"meet-{uuid.uuid4().hex[:10]}"
            link = request.build_absolute_uri(f"/video/{room_name}/")
            send_mail(
                subject="Видеовстреча с врачом",
                message=f"Вы приглашены на встречу. Перейдите по ссылке: {link}",
                from_email="e02616920@gmail.com",
                recipient_list=[patient.email],
                fail_silently=False,
            )
            return redirect('video', room_name=room_name)
    else:
        form = PatientSelectForm()
    return render(request, 'select_user.html', {'form': form})


@login_required
def patient_detail(request, user_id, appointment_id):
    user = get_object_or_404(CustomUser, id=user_id)
    doctor = Doctor.objects.get(user=request.user)
    appointment = get_object_or_404(Appointment, id=appointment_id, user=user, doctor=doctor)
    if request.method == 'POST':
        description = request.POST.get('description')
        results = request.POST.get('results')
        prescription = request.POST.get('prescription', '')
        if description and results:
            record = MedicalRecord.objects.create(
                user=user,
                doctor=doctor,
                appointment=appointment,
                description=description,
                results=results,
                prescription=prescription
            )
            appointment.status = 'completed'
            appointment.save()
            patient_email = appointment.user.email
            subject = 'Медицинская запись создана'
            message = f"""
            Медицинский центр "Офтальмолог"

            Медицинская запись для пациента {record.user.username}:

            Врач: {record.doctor.user.username}
            Описание: {record.description}
            Результаты: {record.results}
            Рецепт: {record.prescription if record.prescription else 'Отсутствует'}

            Услуга: {record.appointment.service.name}
            Цена: {record.appointment.service.price}
            Дата и время: {record.appointment.datetime}
            """
            send_mail(
                subject,
                message,
                'e02616920@gmail.com',
                [patient_email],
                fail_silently=False,
            )
            return redirect('print_medical_record', record_id=record.id)
    records = MedicalRecord.objects.filter(user=user, doctor=doctor, appointment=appointment).order_by('-created_at')
    return render(request, 'patient_detail.html', {
        'user': user,
        'records': records,
        'appointment': appointment
    })


@login_required
def cancel_appointment_doctor(request, appointment_id):
    if request.user.role != 'doctor':
        return redirect('home')
    try:
        doctor = Doctor.objects.get(user=request.user)
    except Doctor.DoesNotExist:
        return redirect('register_doctor')
    appointment = get_object_or_404(Appointment, id=appointment_id, doctor=doctor)
    appointment.status = 'cancelled'
    appointment.save()
    return redirect('doctor_dashboard')


def print_medical_record(request, record_id):
    record = get_object_or_404(MedicalRecord, id=record_id)

    return render(request, 'print_medical_record.html', {
        'record': record
    })


def leave_review(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)

    forbidden_words = ['блять', 'сука', 'тварь']

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.appointment = appointment
            review.user = request.user
            review.doctor = appointment.doctor

            content = review.content.lower()
            if any(word in content for word in forbidden_words):
                return render(request, 'leave_review.html', {'form': form, 'appointment': appointment})

            review.save()
            return redirect('dashboard')
    else:
        form = ReviewForm(initial={'doctor': appointment.doctor})

    return render(request, 'leave_review.html', {'form': form, 'appointment': appointment})


def appointments_history(request, user_id):
    medical_records = MedicalRecord.objects.filter(user_id=user_id)
    return render(request, 'appointments_history.html', {'medical_records': medical_records})


def address(request):
    doctors = Doctor.objects.all()
    return render(request, 'add.html', {'doctors': doctors, "YANDEX_MAPS_API_KEY": os.getenv("YANDEX_MAPS_API_KEY")})


def calendar(request, user_id):
    user = get_object_or_404(CustomUser, pk=user_id)
    records = MedicalRecord.objects.filter(doctor__user=user).order_by('created_at')
    work_days = defaultdict(list)
    for record in records:
        date = record.created_at.date()
        time = record.created_at.time()
        work_days[date].append(time)

    work_days = dict(work_days)
    return render(request, 'calendar.html', {
        'user': user,
        'work_days': work_days
    })


def doctor_review(request, user_id):
    doctor = get_object_or_404(Doctor, user__id=user_id)

    reviews = Review.objects.filter(doctor=doctor)

    return render(request, 'doctor_review.html', {
        'doctor': doctor,
        'reviews': reviews
    })


def doctor_detail(request, doctor_id):
    doctor = get_object_or_404(Doctor, id=doctor_id)
    services = doctor.services.all()
    reviews = doctor.reviews.all()

    return render(request, 'doctor_detail.html', {
        'doctor': doctor,
        'services': services,
        'reviews': reviews,
    })


@login_required
def service_detail(request, doctor_id, service_id):
    doctor = get_object_or_404(Doctor, id=doctor_id)
    service = get_object_or_404(Service, id=service_id)
    form = AppointmentForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        appointment = form.save(commit=False)
        appointment.user = request.user
        appointment.doctor = doctor
        appointment.service = service
        appointment.status = 'scheduled'
        if Appointment.objects.filter(doctor=doctor, datetime=appointment.datetime).exists():
            form.add_error('datetime', 'Это время уже занято другим пациентом.')
            return render(request, 'service_detail.html', {
                'doctor': doctor,
                'service': service,
                'form': form,
            })
        appointment.save()
        return redirect('dashboard')
    return render(request, 'service_detail.html', {
        'doctor': doctor,
        'service': service,
        'form': form,
    })


def search_and_filter(request):
    query = request.GET.get('s', '').strip()
    experience_min_filter = request.GET.get('experience_min', '')
    experience_max_filter = request.GET.get('experience_max', '')
    services_min_filter = request.GET.get('services_count_min', '')
    services_max_filter = request.GET.get('services_count_max', '')
    reviews_min_filter = request.GET.get('reviews_count_min', '')
    reviews_max_filter = request.GET.get('reviews_count_max', '')
    doctors = Doctor.objects.all()
    if query:
        doctors = doctors.filter(
            models.Q(surname__icontains=query) |
            models.Q(name__icontains=query) |
            models.Q(patronymic__icontains=query) |
            models.Q(services__name__icontains=query)
        ).distinct()
    if experience_min_filter:
        doctors = doctors.filter(experience__gte=experience_min_filter)
    if experience_max_filter:
        doctors = doctors.filter(experience__lte=experience_max_filter)
    if services_min_filter or services_max_filter:
        doctors = doctors.annotate(services_count=Count('services'))
        if services_min_filter:
            doctors = doctors.filter(services_count__gte=services_min_filter)
        if services_max_filter:
            doctors = doctors.filter(services_count__lte=services_max_filter)
    if reviews_min_filter or reviews_max_filter:
        doctors = doctors.annotate(reviews_count=Count('reviews'))
        if reviews_min_filter:
            doctors = doctors.filter(reviews_count__gte=reviews_min_filter)
        if reviews_max_filter:
            doctors = doctors.filter(reviews_count__lte=reviews_max_filter)
    return render(request, 'search_and_filter.html', {'doctors': doctors})


def search_doctor(request):
    query = request.GET.get('s', '')
    results = []
    if request.user.role == 'doctor':
        doctor = get_object_or_404(Doctor, user=request.user)
    else:
        doctor = None

    if query and doctor:

        results = Appointment.objects.filter(
            (Q(user__username__icontains=query) | Q(service__name__icontains=query)) &
            Q(status='scheduled') &
            Q(doctor=doctor)
        ).select_related('doctor', 'user', 'service')

    return render(request, 'search_results.html', {'results': results, 'query': query, 'doctor': doctor})


def admin_panel(request):
    return render(request, 'admin_panel.html')


def admin_appointments(request):
    appointments = Appointment.objects.all()
    return render(request, 'admin_appointments.html', {'appointments': appointments})


def admin_users(request):
    users = CustomUser.objects.all()
    return render(request, 'admin_users.html', {'users': users})


def admin_reviews(request):
    reviews = Review.objects.all()
    return render(request, 'admin_reviews.html', {'reviews': reviews})


def admin_doctors(request):
    doctors = Doctor.objects.all()
    return render(request, 'admin_doctors.html', {'doctors': doctors})


def admin_services(request):
    services = Service.objects.all()
    return render(request, 'admin_services.html', {'services': services})


def admin_cards(request):
    records = MedicalRecord.objects.all()
    return render(request, 'admin_cards.html', {'records': records})


def create_user(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('admin_users')
    else:
        form = CustomUserCreationForm()
    return render(request, 'create_user.html', {'form': form})


def edit_user(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)

    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('admin_users')
    else:
        form = CustomUserChangeForm(instance=user)

    return render(request, 'edit_user.html', {'form': form})


def delete_user(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    user.delete()
    return redirect('admin_users')


def delete_service(request, service_id):
    service = get_object_or_404(Service, id=service_id)
    service.delete()
    return redirect('admin_services')


def create_service(request):
    if request.method == 'POST':
        form = ServiceForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('admin_services')
    else:
        form = ServiceForm()

    return render(request, 'create_service.html', {'form': form})


def edit_service(request, service_id):
    service = get_object_or_404(Service, id=service_id)
    if request.method == 'POST':
        form = ServiceForm(request.POST, instance=service)
        if form.is_valid():
            form.save()
            return redirect('admin_services')
    else:
        form = ServiceForm(instance=service)
    return render(request, 'edit_service.html', {'form': form, 'service': service})


def create_doctor(request):
    if request.method == 'POST':
        form = DoctorForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('admin_doctors')
    else:
        form = DoctorForm()
    return render(request, 'create_doctor.html', {'form': form})


def edit_doctor(request, doctor_id):
    doctor = get_object_or_404(Doctor, id=doctor_id)
    if request.method == 'POST':
        form = DoctorForm(request.POST, request.FILES, instance=doctor)
        if form.is_valid():
            form.save()
            return redirect('admin_doctors')
    else:
        form = DoctorForm(instance=doctor)
    return render(request, 'edit_doctor.html', {'form': form, 'doctor': doctor})


def delete_doctor(request, doctor_id):
    doctor = get_object_or_404(Doctor, id=doctor_id)
    doctor.delete()
    return redirect('admin_doctors')


def create_review(request):
    if request.method == 'POST':
        form = CustomReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.save()
            return redirect('admin_reviews')
    else:
        form = CustomReviewForm()

    return render(request, 'create_review.html', {'form': form})


def edit_review(request, review_id):
    review = get_object_or_404(Review, id=review_id)
    if request.method == 'POST':
        form = CustomReviewForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
            return redirect('admin_reviews')
    else:
        form = CustomReviewForm(instance=review)

    return render(request, 'edit_review.html', {'form': form, 'review': review})


def delete_review(request, review_id):
    review = get_object_or_404(Review, id=review_id)
    review.delete()
    return redirect('admin_reviews')


def create_medicalrecord(request):
    if request.method == 'POST':
        form = CustomMedicalRecordForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('admin_cards')
    else:
        form = CustomMedicalRecordForm()

    return render(request, 'create_record.html', {'form': form})


def edit_medicalrecord(request, record_id):
    record = get_object_or_404(MedicalRecord, id=record_id)
    if request.method == 'POST':
        form = CustomMedicalRecordForm(request.POST, instance=record)
        if form.is_valid():
            form.save()
            return redirect('admin_cards')
    else:
        form = CustomMedicalRecordForm(instance=record)
    return render(request, 'edit_record.html', {'form': form, 'record': record})


def delete_medicalrecord(request, record_id):
    record = get_object_or_404(MedicalRecord, id=record_id)
    record.delete()
    return redirect('admin_cards')


def delete_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    appointment.delete()
    return redirect('admin_appointments')


def edit_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)

    if request.method == 'POST':
        form = CustomAppointmentForm(request.POST, instance=appointment)
        if form.is_valid():
            form.save()
            return redirect('admin_appointments')
    else:
        appointment.datetime = localtime(appointment.datetime).strftime('%Y-%m-%dT%H:%M')
        form = CustomAppointmentForm(instance=appointment)

    return render(request, 'edit_appointment.html', {'form': form, 'appointment': appointment})


def create_appointment(request):
    if request.method == 'POST':
        form = CustomAppointmentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('admin_appointments')
    else:
        form = CustomAppointmentForm()
    return render(request, 'create_appointment.html', {'form': form})
