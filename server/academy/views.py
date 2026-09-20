import csv, hashlib, secrets, uuid
from datetime import timedelta
from functools import wraps
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.db import transaction, IntegrityError
from django.db.models import Q, Sum, Count, F
from django.http import HttpResponse, HttpResponseForbidden
from django.views.decorators.http import require_POST, require_http_methods
from django.utils import timezone
from django.conf import settings
from .models import *
from .forms import *
from . import placement as engine


def is_admin(user): return user.is_authenticated and (user.role=='admin' or user.is_superuser)
def roles(*allowed):
    def decorator(fn):
        @login_required
        @wraps(fn)
        def inner(request,*a,**kw):
            if not is_admin(request.user) and request.user.role not in allowed: return HttpResponseForbidden('دسترسی به این بخش مجاز نیست.')
            return fn(request,*a,**kw)
        return inner
    return decorator

def audit(user,action,detail=''): Audit.objects.create(actor=user if user.is_authenticated else None,action=action,detail=detail[:250])
def accessible_courses(user):
    if is_admin(user): return Course.objects.all()
    if user.role=='teacher': return Course.objects.filter(teacher=user)
    return Course.objects.filter(enrollments__student=user)

def filtered_courses(request):
    qs=Course.objects.filter(published=True).select_related('teacher').order_by('id')
    for key in ['category','mode']:
        if request.GET.get(key): qs=qs.filter(**{key:request.GET[key]})
    if request.GET.get('q'): qs=qs.filter(title__icontains=request.GET['q'][:100])
    return qs

def home(request):
    courses=Course.objects.filter(published=True).select_related('teacher').order_by('id')
    teachers=User.objects.filter(role='teacher',is_active=True,teaching__published=True).distinct()[:4]
    return render(request,'academy/home.html',{'courses':courses[:3],'course_count':courses.count(),'featured':courses.filter(category='ielts').first() or courses.first(),'teachers':teachers})
def catalog(request): return render(request,'academy/catalog.html',{'courses':filtered_courses(request)})
def course_detail(request,pk):
    c=get_object_or_404(Course,pk=pk,published=True)
    return render(request,'academy/course.html',{'course':c})

@require_http_methods(['GET','POST'])
def signup(request):
    if request.user.is_authenticated: return redirect('dashboard')
    form=SignupForm(request.POST or None)
    if request.method=='POST' and form.is_valid():
        try:
            with transaction.atomic(): user=form.save()
        except IntegrityError: form.add_error(None,'نام کاربری یا ایمیل قبلاً ثبت شده است.')
        else:
            login(request,user);audit(user,'ثبت‌نام');return redirect('dashboard')
    return render(request,'registration/auth.html',{'form':form,'signup':True})

@require_http_methods(['GET','POST'])
def signin(request):
    if request.user.is_authenticated: return redirect('dashboard')
    form=LoginForm(request,data=request.POST or None)
    if request.method=='POST':
        # Account and client-address counters are independent. Behind the bundled
        # proxy REMOTE_ADDR is the proxy address: conservatively shares the IP cap.
        inputs=[('account:'+request.POST.get('username','').strip().lower(),8),('ip:'+request.META.get('REMOTE_ADDR',''),40)]
        attempts=[]
        for raw,limit in inputs:
            key=hashlib.sha256(raw.encode()).hexdigest()
            attempt,_=LoginAttempt.objects.get_or_create(key=key)
            if timezone.now()-attempt.started>timedelta(minutes=15):
                attempt.count=0;attempt.started=timezone.now();attempt.save()
            attempts.append((attempt,limit))
        if any(a.count>=limit for a,limit in attempts):
            form.add_error(None,'تلاش‌های ورود بیش از حد است. ۱۵ دقیقه دیگر امتحان کنید.')
        elif form.is_valid():
            user=form.get_user();login(request,user);attempts[0][0].delete();audit(user,'ورود موفق');return redirect('dashboard')
        else:
            LoginAttempt.objects.filter(pk__in=[a.pk for a,_ in attempts]).update(count=F('count')+1)
            audit(request.user,'ورود ناموفق')
    return render(request,'registration/auth.html',{'form':form})

@login_required
@require_POST
def signout(request):
    audit(request.user,'خروج');logout(request);return redirect('home')

@login_required
def dashboard(request):
    user=request.user;qs=accessible_courses(user).select_related('teacher').order_by('id')
    lessons=Lesson.objects.filter(course__in=qs,starts__gte=timezone.now()).order_by('starts')[:5]
    latest=PlacementResult.objects.filter(student=user).order_by('-created').first()
    orders=Order.objects.all() if is_admin(user) else Order.objects.filter(student=user)
    data={'courses':qs,'lessons':lessons,'latest':latest,'is_admin_panel':is_admin(user),'paid':orders.filter(status='paid').aggregate(s=Sum('amount'))['s'] or 0,'enrollment_count':Enrollment.objects.count() if is_admin(user) else Enrollment.objects.filter(course__in=qs).count(),'ticket_count':Ticket.objects.filter(status='open').count() if is_admin(user) else Ticket.objects.filter(owner=user,status='open').count(),'audit_rows':Audit.objects.select_related('actor').order_by('-created')[:5] if is_admin(user) else [],'now':timezone.now()}
    progress=[]
    for c in qs:
        done=c.lessons.filter(completed=True).count()
        progress.append({'course':c,'done':done,'percent':min(100,round(done/max(c.total_sessions,1)*100))})
    data['progress']=progress
    return render(request,'academy/dashboard.html',data)

@login_required
def classes(request): return render(request,'academy/classes.html',{'courses':accessible_courses(request.user).order_by('id')})

@login_required
def classroom(request,pk):
    c=get_object_or_404(accessible_courses(request.user),pk=pk)
    return render(request,'academy/classroom.html',{'course':c,'lessons':c.lessons.order_by('starts'),'students':c.enrollments.select_related('student'),'can_manage':is_admin(request.user) or c.teacher_id==request.user.id,'grades':Grade.objects.filter(course=c) if is_admin(request.user) or c.teacher_id==request.user.id else Grade.objects.filter(course=c,student=request.user)})

@roles('teacher')
def lesson_edit(request,pk,lesson_id=None):
    c=get_object_or_404(accessible_courses(request.user),pk=pk)
    obj=get_object_or_404(Lesson,pk=lesson_id,course=c) if lesson_id else None
    form=LessonForm(request.POST or None,instance=obj)
    if request.method=='POST' and form.is_valid():
        lesson=form.save(commit=False);lesson.course=c;lesson.save();audit(request.user,'ویرایش جلسه',str(lesson));messages.success(request,'جلسه ذخیره شد.');return redirect('classroom',pk=c.pk)
    return render(request,'academy/form.html',{'form':form,'title':'تنظیم جلسه و منابع آموزشی'})

@roles('teacher')
def attendance(request,pk):
    lesson=get_object_or_404(Lesson,pk=pk,course__in=accessible_courses(request.user))
    students=User.objects.filter(enrollments__course=lesson.course).order_by('first_name')
    if request.method=='POST':
        selected=set(request.POST.getlist('present'))
        with transaction.atomic():
            for student in students: Attendance.objects.update_or_create(lesson=lesson,student=student,defaults={'present':str(student.pk) in selected})
        audit(request.user,'ثبت حضور‌وغیاب',str(lesson));messages.success(request,'حضور‌وغیاب ذخیره شد.');return redirect('classroom',pk=lesson.course_id)
    selected=set(Attendance.objects.filter(lesson=lesson,present=True).values_list('student_id',flat=True))
    return render(request,'academy/attendance.html',{'lesson':lesson,'rows':[{'user':u,'present':u.pk in selected} for u in students]})

@roles('teacher')
def grade_add(request,pk):
    c=get_object_or_404(accessible_courses(request.user),pk=pk)
    form=GradeForm(request.POST or None);form.fields['student'].queryset=User.objects.filter(enrollments__course=c)
    if request.method=='POST' and form.is_valid():
        grade=form.save(commit=False);grade.course=c;grade.save();audit(request.user,'ثبت نمره',str(c));messages.success(request,'نمره ذخیره شد.');return redirect('classroom',pk=pk)
    return render(request,'academy/form.html',{'form':form,'title':'ثبت نمره و بازخورد'})

@login_required
def records(request):
    return render(request,'academy/records.html',{'grades':Grade.objects.filter(student=request.user).select_related('course'),'results':PlacementResult.objects.filter(student=request.user).order_by('-created'),'attendance':Attendance.objects.filter(student=request.user).select_related('lesson__course').order_by('-lesson__starts')})

@roles('student')
@require_http_methods(['GET','POST'])
def placement(request):
    state=request.session.get('placement')
    if request.method=='POST' and request.POST.get('action')=='start':
        state={'answers':[],'nonce':secrets.token_urlsafe(18)}
        state['q']=engine.next_question([]);request.session['placement']=state
        return redirect('placement')
    if request.method=='POST' and state:
        if request.POST.get('nonce')!=state['nonce']: return redirect('placement')
        try: selected=int(request.POST.get('answer',''))
        except ValueError: selected=-1
        if selected not in range(4): messages.error(request,'یک گزینه انتخاب کنید.')
        else:
            q=state['q'];state['answers'].append({'q':q,'answer':selected,'correct':selected==engine.QUESTIONS[q][3]})
            if len(state['answers'])==12:
                score,level=engine.result(state['answers'])
                result=PlacementResult.objects.create(student=request.user,score=score,level=level,answers=state['answers'])
                del request.session['placement'];audit(request.user,'اتمام تعیین سطح',level)
                return redirect('placement_result',pk=result.pk)
            state['q']=engine.next_question(state['answers']);state['nonce']=secrets.token_urlsafe(18)
            request.session['placement']=state
            return redirect('placement')
    data={}
    if state:
        q=engine.QUESTIONS[state['q']]
        data={'question':q[1],'options':list(enumerate(q[2])),'step':len(state['answers'])+1,'percent':round(len(state['answers'])/12*100),'nonce':state['nonce']}
    return render(request,'academy/placement.html',data)

@login_required
def placement_result(request,pk):
    result=get_object_or_404(PlacementResult,pk=pk,student=request.user)
    return render(request,'academy/result.html',{'result':result,'plan':StudyPlan.objects.filter(result=result).first(),'ai_enabled':bool(settings.OPENAI_API_KEY and settings.OPENAI_MODEL),'courses':Course.objects.filter(published=True,level=result.level)})

@roles('student')
@require_POST
def enroll(request,pk):
    with transaction.atomic():
        c=get_object_or_404(Course.objects.select_for_update(),pk=pk,published=True)
        if Enrollment.objects.filter(student=request.user,course=c).exists(): return redirect('classroom',pk=pk)
        if not c.seats: messages.error(request,'ظرفیت دوره تکمیل شده است.');return redirect('course',pk=pk)
        order,_=Order.objects.get_or_create(student=request.user,course=c,defaults={'amount':c.price})
    return redirect('order',pk=order.pk)

@login_required
def order_detail(request,pk):
    qs=Order.objects.all() if is_admin(request.user) else Order.objects.filter(student=request.user)
    order=get_object_or_404(qs.select_related('course','student'),pk=pk)
    return render(request,'academy/order.html',{'order':order})

@login_required
def orders(request):
    qs=Order.objects.all() if is_admin(request.user) else Order.objects.filter(student=request.user)
    return render(request,'academy/orders.html',{'orders':qs.select_related('student','course').order_by('-created'),'is_admin_panel':is_admin(request.user)})

@roles('admin')
@require_POST
def approve_order(request,pk):
    order=get_object_or_404(Order,pk=pk)
    if not request.POST.get('reference','').strip():
        messages.error(request,'شماره رسید پرداخت را وارد کنید.');return redirect('order',pk=pk)
    from .payments import settle
    settle(order.pk,request.POST['reference'].strip()[:128],request.user)
    messages.success(request,'وضعیت رسید بررسی و ثبت شد.');return redirect('order',pk=pk)

@roles('admin')
def manage_courses(request): return render(request,'academy/manage_courses.html',{'courses':Course.objects.all().order_by('-created')})

@roles('admin')
def course_edit(request,pk=None):
    form=CourseForm(request.POST or None,instance=get_object_or_404(Course,pk=pk) if pk else None)
    if request.method=='POST' and form.is_valid():
        c=form.save();audit(request.user,'ویرایش دوره',str(c));messages.success(request,'دوره ذخیره شد.');return redirect('manage_courses')
    return render(request,'academy/form.html',{'form':form,'title':'ویرایش دوره' if pk else 'افزودن دوره انگلیسی'})

@roles('admin')
def users(request):
    qs=User.objects.all().order_by('-date_joined')
    q=request.GET.get('q','')[:100]
    if q: qs=qs.filter(Q(username__icontains=q)|Q(first_name__icontains=q)|Q(email__icontains=q))
    return render(request,'academy/users.html',{'users':qs[:200]})

@roles('admin')
@require_POST
def user_role(request,pk):
    user=get_object_or_404(User,pk=pk)
    role=request.POST.get('role')
    if user.pk==request.user.pk or user.is_superuser: return HttpResponseForbidden('نقش این حساب از این صفحه تغییر نمی‌کند.')
    if role not in ['student','teacher','admin']: return HttpResponse('نقش نامعتبر',status=400)
    user.role=role;user.save(update_fields=['role']);audit(request.user,'تغییر نقش',f'{user.pk}: {role}')
    messages.success(request,'نقش کاربر به‌روزرسانی شد.');return redirect('users')

@roles('admin')
def security(request): return render(request,'academy/security.html',{'rows':Audit.objects.select_related('actor').order_by('-created')[:200]})

@login_required
def inbox(request):
    user=request.user
    qs=Message.objects.filter(Q(recipient=user)|Q(sender=user)|Q(audience='all')|Q(audience=user.role)).select_related('sender','recipient').order_by('-created')
    return render(request,'academy/inbox.html',{'rows':qs[:100]})

@roles('teacher')
def compose(request):
    form=MessageForm(request.POST or None,user=request.user)
    if request.method=='POST' and form.is_valid():
        d=form.cleaned_data
        Message.objects.create(sender=request.user,recipient=d['recipient'] if d['audience']=='direct' else None,audience=d['audience'],subject=d['subject'],body=d['body'])
        audit(request.user,'ارسال پیام',d['audience']);messages.success(request,'پیام ارسال شد.');return redirect('inbox')
    return render(request,'academy/form.html',{'form':form,'title':'ارسال پیام'})

@login_required
def tickets(request):
    qs=Ticket.objects.all() if is_admin(request.user) else Ticket.objects.filter(owner=request.user)
    return render(request,'academy/tickets.html',{'tickets':qs.select_related('owner').order_by('-created')})

@login_required
def ticket_new(request):
    form=TicketForm(request.POST or None)
    if request.method=='POST' and form.is_valid():
        t=form.save(commit=False);t.owner=request.user;t.save();messages.success(request,'درخواست پشتیبانی ثبت شد.');return redirect('ticket',pk=t.pk)
    return render(request,'academy/form.html',{'form':form,'title':'درخواست پشتیبانی جدید'})

@login_required
def ticket_detail(request,pk):
    qs=Ticket.objects.all() if is_admin(request.user) else Ticket.objects.filter(owner=request.user)
    t=get_object_or_404(qs,pk=pk)
    if request.method=='POST':
        body=request.POST.get('body','').strip()[:10000]
        if body:
            TicketReply.objects.create(ticket=t,author=request.user,body=body)
            t.status='open';t.save(update_fields=['status'])
        if is_admin(request.user) and request.POST.get('close')=='1': t.status='closed';t.save(update_fields=['status'])
        return redirect('ticket',pk=pk)
    return render(request,'academy/ticket.html',{'ticket':t})

@roles('admin')
def export_orders(request):
    response=HttpResponse(content_type='text/csv; charset=utf-8-sig');response['Content-Disposition']='attachment; filename="pol-orders.csv"';response.write('\ufeff')
    writer=csv.writer(response);writer.writerow(['شناسه','دانشجو','دوره','مبلغ تومان','وضعیت','تاریخ'])
    def safe(v):
        s=str(v)
        return "'"+s if s and s[0] in '=+-@\t\r' else s
    for o in Order.objects.select_related('student','course').order_by('-created').iterator(): writer.writerow([safe(v) for v in [o.pk,o.student,o.course,o.amount,o.get_status_display(),o.created.isoformat()]])
    audit(request.user,'خروجی گزارش مالی');return response

@login_required
@require_POST
def live_update(request,pk):
    from django.http import JsonResponse
    c=get_object_or_404(accessible_courses(request.user),pk=pk)
    control,_=ClassroomControl.objects.get_or_create(course=c)
    presence,_=LivePresence.objects.get_or_create(course=c,user=request.user)
    action=request.POST.get('action','heartbeat')
    can_manage=is_admin(request.user) or c.teacher_id==request.user.id
    if action=='hand': presence.hand=not presence.hand
    if action=='control':
        if not can_manage: return HttpResponseForbidden()
        control.chat_open=not control.chat_open;control.save()
    if action=='message':
        text=request.POST.get('body','').strip()[:500]
        recent=ClassMessage.objects.filter(course=c,author=request.user,created__gte=timezone.now()-timedelta(seconds=2)).exists()
        if text and not recent and (control.chat_open or can_manage): ClassMessage.objects.create(course=c,author=request.user,body=text)
    presence.save()
    peers=LivePresence.objects.filter(course=c,last_seen__gte=timezone.now()-timedelta(seconds=35)).select_related('user')
    chat=ClassMessage.objects.filter(course=c).select_related('author').order_by('-created')[:30]
    return JsonResponse({'chat_open':control.chat_open,'peers':[{'name':str(p.user),'hand':p.hand,'role':p.user.get_role_display()} for p in peers],'messages':[{'name':str(m.author),'body':m.body} for m in reversed(list(chat))]})

@roles('admin')
def metrics(request):
    from django.http import JsonResponse
    response=JsonResponse({'enrollments':Enrollment.objects.count(),'paid':Order.objects.filter(status='paid').aggregate(total=Sum('amount'))['total'] or 0,'tickets':Ticket.objects.filter(status='open').count(),'time':timezone.localtime().strftime('%H:%M:%S')})
    response['Cache-Control']='no-store'
    return response
