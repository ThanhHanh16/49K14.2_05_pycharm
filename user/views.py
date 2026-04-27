from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from rest_framework.decorators import api_view
from rest_framework.response import Response
import random
from django.core.mail import send_mail
from accounts.models import CustomerProfile
from customers.models import Customer

@api_view(['POST'])
def forgot_password_api(request):
    email = request.data.get('email')
    if not email:
        return Response({'detail': 'Email is required'}, status=400)
    User = get_user_model()
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response({'detail': 'User with this email does not exist'}, status=404)
    otp = str(random.randint(100000, 999999))
    send_mail(
        'Mã khôi phục mật khẩu',
        f'Mã OTP của bạn là: {otp}',
        'from@example.com',
        [email],
        fail_silently=False,
    )
    return Response({'detail': 'OTP đã được gửi'})

@api_view(['POST'])
def reset_password_quick(request):
    username = request.data.get('username')
    email = request.data.get('email')
    phone = request.data.get('phone')
    new_password = request.data.get('new_password')
    confirm_password = request.data.get('confirm_password')

    if not all([username, email, phone, new_password, confirm_password]):
        return Response({'detail': 'Vui lòng nhập đầy đủ thông tin'}, status=400)
    if new_password != confirm_password:
        return Response({'detail': 'Mật khẩu xác nhận không khớp'}, status=400)

    User = get_user_model()
    try:
        user = User.objects.get(username=username, email=email)
        customer_profile = CustomerProfile.objects.filter(user=user, phone=phone).first()
        customer = Customer.objects.filter(email=email, phone_number=phone).first()

        if not customer and not customer_profile:
             return Response({'detail': 'Thông tin xác thực sai (Số điện thoại không khớp).'}, status=400)

        user.password = make_password(new_password)
        user.save()
        return Response({'detail': 'Đổi mật khẩu thành công'})
    except User.DoesNotExist:
        return Response({'detail': 'Thông tin xác thực sai (Không tìm thấy tài khoản).'}, status=400)