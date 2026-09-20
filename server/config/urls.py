from django.contrib import admin
from django.urls import path
from academy import views as v, payments as p, oauth as o, ai
from academy import public
urlpatterns=[
 path('api/public/catalog/',public.catalog,name='public_catalog'),
 path('',v.home,name='home'),path('courses/',v.catalog,name='catalog'),path('courses/<int:pk>/',v.course_detail,name='course'),
 path('signup/',v.signup,name='signup'),path('login/',v.signin,name='login'),path('logout/',v.signout,name='logout'),
 path('auth/google/',o.google_start,name='google'),path('auth/google/callback/',o.google_callback),
 path('dashboard/',v.dashboard,name='dashboard'),path('classes/',v.classes,name='classes'),path('classes/<int:pk>/',v.classroom,name='classroom'),
 path('classes/<int:pk>/lesson/new/',v.lesson_edit,name='lesson_new'),path('classes/<int:pk>/lesson/<int:lesson_id>/',v.lesson_edit,name='lesson_edit'),
 path('lessons/<int:pk>/attendance/',v.attendance,name='attendance'),path('classes/<int:pk>/grade/',v.grade_add,name='grade_add'),path('records/',v.records,name='records'),
 path('placement/',v.placement,name='placement'),path('placement/results/<int:pk>/',v.placement_result,name='placement_result'),
 path('enroll/<int:pk>/',v.enroll,name='enroll'),path('orders/',v.orders,name='orders'),path('orders/<uuid:pk>/',v.order_detail,name='order'),
 path('orders/<uuid:pk>/pay/',p.pay,name='pay'),path('payment/callback/',p.callback,name='payment_callback'),path('orders/<uuid:pk>/approve/',v.approve_order,name='approve_order'),
 path('manage/courses/',v.manage_courses,name='manage_courses'),path('manage/courses/new/',v.course_edit,name='course_new'),path('manage/courses/<int:pk>/',v.course_edit,name='course_edit'),
 path('manage/users/',v.users,name='users'),path('manage/users/<int:pk>/role/',v.user_role,name='user_role'),path('manage/security/',v.security,name='security'),path('manage/orders.csv',v.export_orders,name='export_orders'),
 path('messages/',v.inbox,name='inbox'),path('messages/new/',v.compose,name='compose'),path('tickets/',v.tickets,name='tickets'),path('tickets/new/',v.ticket_new,name='ticket_new'),path('tickets/<int:pk>/',v.ticket_detail,name='ticket'),
 path('classes/<int:pk>/live/',v.live_update,name='live_update'),path('placement/results/<int:pk>/plan/',ai.study_plan,name='study_plan'),path('manage/metrics/',v.metrics,name='metrics'),path('system-admin/',admin.site.urls),
]
