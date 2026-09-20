import uuid
from authlib.integrations.django_client import OAuth
from django.conf import settings
from django.contrib.auth import login
from django.contrib import messages
from django.db import IntegrityError, transaction
from django.shortcuts import redirect
from .models import User, Audit

oauth=OAuth()
oauth.register(name='google',client_id=settings.GOOGLE_CLIENT_ID,client_secret=settings.GOOGLE_CLIENT_SECRET,server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',client_kwargs={'scope':'openid email profile','code_challenge_method':'S256','timeout':15})

def google_start(request):
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        messages.info(request,'ورود گوگل هنوز فعال نشده است. از نام کاربری و رمز عبور استفاده کنید.');return redirect('login')
    return oauth.google.authorize_redirect(request,settings.PUBLIC_BASE_URL+'/auth/google/callback/')

def google_callback(request):
    try:
        # Authlib validates state, signature, issuer, audience, expiry and nonce.
        token=oauth.google.authorize_access_token(request)
        info=token.get('userinfo',{})
        if not info.get('sub') or info.get('email_verified') is not True: raise ValueError('Unverified identity')
        email=info['email'].lower()
        user=User.objects.filter(google_sub=info['sub']).first()
        if not user:
            if User.objects.filter(email__iexact=email).exists():
                messages.error(request,'این ایمیل قبلاً حساب دارد. با رمز عبور وارد شوید؛ اتصال حساب موجود باید توسط مدیر بررسی شود.');return redirect('login')
            with transaction.atomic():
                user=User(username='g_'+uuid.uuid4().hex[:24],email=email,google_sub=info['sub'],first_name=info.get('name','')[:150],role='student')
                user.set_unusable_password();user.save()
        if not user.is_active: raise ValueError('Inactive account')
        login(request,user);Audit.objects.create(actor=user,action='ورود گوگل');return redirect('dashboard')
    except Exception:
        # Never render tokens or provider exception details to the user.
        messages.error(request,'ورود گوگل تکمیل نشد. دوباره تلاش کنید یا با رمز عبور وارد شوید.');return redirect('login')
