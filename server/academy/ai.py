"""Optional plan generation; never determines enrollment or changes academic records."""
import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404,redirect
from django.views.decorators.http import require_POST
from django.utils import timezone
from datetime import timedelta
from .models import PlacementResult,StudyPlan,User
from django.db import transaction

@login_required
@require_POST
def study_plan(request,pk):
    result=get_object_or_404(PlacementResult,pk=pk,student=request.user)
    if not settings.OPENAI_API_KEY or not settings.OPENAI_MODEL:
        messages.info(request,'سرویس برنامه تمرین هوش مصنوعی هنوز فعال نشده است.');return redirect('placement_result',pk=pk)
    if request.POST.get('consent')!='yes':
        messages.error(request,'برای ارسال سطح و درصد آزمون، گزینه رضایت را انتخاب کنید.');return redirect('placement_result',pk=pk)
    with transaction.atomic():
        # One request per result and at most three attempts/day/account, including failures.
        User.objects.filter(pk=request.user.pk).update(last_login=request.user.last_login)
        if StudyPlan.objects.filter(result=result).exists(): return redirect('placement_result',pk=pk)
        if StudyPlan.objects.filter(result__student=request.user,requested__gte=timezone.now()-timedelta(days=1)).count()>=3:
            messages.error(request,'سهمیه روزانه برنامه تمرین به پایان رسیده است.');return redirect('placement_result',pk=pk)
        plan=StudyPlan.objects.create(result=result)
    try:
        r=requests.post('https://api.openai.com/v1/responses',headers={'Authorization':'Bearer '+settings.OPENAI_API_KEY},json={'model':settings.OPENAI_MODEL,'store':False,'max_output_tokens':1100,'instructions':'You are an English tutor. In Persian, provide a concise seven-day practice plan with simple English examples. The supplied level is a provisional grammar/reading screening, not a validated CEFR assessment. Do not change it or infer speaking/listening ability. No links, no paid recommendations, no personal questions.','input':f'Provisional level: {result.level}; screening accuracy: {result.score} percent.'},timeout=35)
        r.raise_for_status();data=r.json()
        text='\n'.join(part.get('text','') for item in data.get('output',[]) if item.get('type')=='message' for part in item.get('content',[]) if part.get('type')=='output_text').strip()
        if not text: raise ValueError('Empty response')
        plan.body=text[:12000];plan.save(update_fields=['body'])
    except (requests.RequestException,ValueError,TypeError):
        plan.body='برنامه دریافت نشد. برای دریافت برنامه تمرین با استاد هماهنگ کنید.';plan.save(update_fields=['body'])
        messages.error(request,'سرویس هوش مصنوعی پاسخ قابل استفاده نداد.')
    return redirect('placement_result',pk=pk)
