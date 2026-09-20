"""Payment adapter. Amounts in DB are toman; gateway requests are IRR (x10).
External integration requires a live merchant and acceptance testing before launch.
"""
import requests
from django.conf import settings
from django.db import transaction
from django.db.models import F
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404, redirect
from .models import Order, Course, Enrollment, Audit

@transaction.atomic
def settle(order_id,reference,actor=None):
    order=Order.objects.select_for_update().get(pk=order_id)
    if order.status in ['paid','review']: return order
    # A write acquires SQLite's writer lock before the capacity check.
    Course.objects.filter(pk=order.course_id).update(capacity=F('capacity'))
    course=Course.objects.get(pk=order.course_id)
    if Enrollment.objects.filter(student=order.student,course=course).exists(): order.status='paid'
    elif course.seats:
        Enrollment.objects.create(student=order.student,course=course);order.status='paid'
    else: order.status='review'
    order.reference=str(reference)[:128];order.save(update_fields=['reference','status'])
    Audit.objects.create(actor=actor,action='تأیید پرداخت',detail=str(order.pk))
    return order

@login_required
@require_POST
def pay(request,pk):
    order=get_object_or_404(Order,pk=pk,student=request.user)
    if order.status!='pending': return redirect('order',pk=pk)
    if not settings.ZARINPAL_MERCHANT_ID:
        messages.error(request,'پرداخت آنلاین هنوز توسط آموزشگاه فعال نشده است.');return redirect('order',pk=pk)
    if not order.course.seats:
        messages.error(request,'ظرفیت دوره تکمیل شده است.');return redirect('order',pk=pk)
    if order.authority:
        return redirect('https://www.zarinpal.com/pg/StartPay/'+order.authority)
    try:
        response=requests.post('https://api.zarinpal.com/pg/v4/payment/request.json',json={'merchant_id':settings.ZARINPAL_MERCHANT_ID,'amount':order.amount*10,'currency':'IRR','callback_url':settings.PUBLIC_BASE_URL+'/payment/callback/','description':'ثبت‌نام دوره '+order.course.title,'metadata':{'email':request.user.email}},timeout=20)
        response.raise_for_status();data=response.json().get('data',{})
        authority=data.get('authority','')
        if data.get('code')!=100 or not isinstance(authority,str) or not authority.isalnum() or len(authority)>128: raise ValueError('Gateway rejected request')
        updated=Order.objects.filter(pk=pk,authority__isnull=True,status='pending').update(authority=authority)
        if not updated: order.refresh_from_db();authority=order.authority
        return redirect('https://www.zarinpal.com/pg/StartPay/'+authority)
    except (requests.RequestException,ValueError,TypeError):
        messages.error(request,'ارتباط با درگاه برقرار نشد. مبلغی در سامانه تأیید نشده است.');return redirect('order',pk=pk)

@login_required
def callback(request):
    authority=request.GET.get('Authority','')
    order=get_object_or_404(Order,authority=authority,student=request.user)
    if order.status!='pending': return redirect('order',pk=order.pk)
    if request.GET.get('Status')!='OK':
        Order.objects.filter(pk=order.pk,status='pending').update(authority=None)
        messages.error(request,'پرداخت لغو شد یا به پایان نرسید.');return redirect('order',pk=order.pk)
    if not settings.ZARINPAL_MERCHANT_ID: return redirect('order',pk=order.pk)
    try:
        r=requests.post('https://api.zarinpal.com/pg/v4/payment/verify.json',json={'merchant_id':settings.ZARINPAL_MERCHANT_ID,'amount':order.amount*10,'authority':order.authority},timeout=20)
        r.raise_for_status();data=r.json().get('data',{})
        if data.get('code') not in [100,101] or not data.get('ref_id'): raise ValueError('Not verified')
        order=settle(order.pk,data['ref_id'],request.user)
        messages.success(request,'پرداخت تأیید شد.' if order.status=='paid' else 'پرداخت دریافت شد؛ ظرفیت دوره نیازمند بررسی آموزشگاه است. برای تعیین کلاس یا بازپرداخت، تیکت ثبت کنید.')
    except (requests.RequestException,ValueError,TypeError):
        messages.error(request,'تأیید پرداخت دریافت نشد؛ اگر مبلغ کسر شده، با پشتیبانی پیگیری کنید. دوباره پرداخت نکنید.')
    return redirect('order',pk=order.pk)
