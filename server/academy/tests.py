from django.test import TestCase,Client,override_settings
from django.urls import reverse
from django.utils import timezone
from unittest.mock import patch,Mock
from .models import *
from .payments import settle
from .placement import QUESTIONS

@override_settings(DEBUG=True,SECURE_SSL_REDIRECT=False,SESSION_COOKIE_SECURE=False,CSRF_COOKIE_SECURE=False)
class PlatformTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.student=User.objects.create_user('learner','learner@example.invalid','Strong-demo-938!',role='student')
        cls.other=User.objects.create_user('other','other@example.invalid','Strong-demo-938!',role='student')
        cls.teacher=User.objects.create_user('teacher','teacher@example.invalid','Strong-demo-938!',role='teacher')
        cls.admin=User.objects.create_user('manager','manager@example.invalid','Strong-demo-938!',role='admin')
        cls.course=Course.objects.create(title='English General',category='general',mode='online',price=1200000,capacity=2,teacher=cls.teacher,published=True,description='English course')
        cls.unassigned=Course.objects.create(title='Other course',category='ielts',mode='onsite',price=3000000,published=True)
        cls.lesson=Lesson.objects.create(course=cls.course,title='Lesson 1',starts=timezone.now())
        Enrollment.objects.create(student=cls.student,course=cls.course)

    def test_public_and_role_pages_render(self):
        for path in ['/','/courses/','/courses/1/','/login/','/signup/']:
            self.assertEqual(self.client.get(path).status_code,200,path)
        for user in [self.student,self.teacher,self.admin]:
            self.client.force_login(user)
            for path in ['/dashboard/','/classes/','/classes/1/','/messages/','/tickets/','/tickets/new/','/orders/','/records/']:
                self.assertEqual(self.client.get(path).status_code,200,(user.role,path))
        for path in ['/manage/courses/','/manage/courses/new/','/manage/courses/1/','/manage/users/','/manage/security/','/messages/new/','/classes/1/lesson/new/','/lessons/1/attendance/','/classes/1/grade/']:
            self.assertEqual(self.client.get(path).status_code,200,path)

    def test_signup_cannot_promote_role(self):
        response=self.client.post('/signup/',{'first_name':'New Student','email':'NEW@example.invalid','username':'newperson','password1':'Strong-unique-99817!','password2':'Strong-unique-99817!','role':'admin','is_staff':'1'})
        self.assertEqual(response.status_code,302)
        user=User.objects.get(username='newperson');self.assertEqual(user.role,'student');self.assertFalse(user.is_staff);self.assertEqual(user.email,'new@example.invalid')
        self.assertTrue(user.check_password('Strong-unique-99817!'))

    def test_role_and_record_isolation(self):
        t=Ticket.objects.create(owner=self.other,subject='Private other ticket',body='secret')
        o=Order.objects.create(student=self.other,course=self.course,amount=1200000)
        self.client.force_login(self.student)
        for path in ['/manage/users/','/manage/security/','/manage/courses/','/messages/new/','/classes/1/grade/','/lessons/1/attendance/']:
            self.assertEqual(self.client.get(path).status_code,403,path)
        for path in [f'/tickets/{t.pk}/',f'/orders/{o.pk}/','/classes/2/']:
            self.assertEqual(self.client.get(path).status_code,404,path)
        self.client.force_login(self.teacher)
        self.assertEqual(self.client.get('/classes/2/').status_code,404)
        self.assertEqual(self.client.get('/classes/2/lesson/new/').status_code,404)

    def test_csrf_and_mutation_methods(self):
        client=Client(enforce_csrf_checks=True);client.force_login(self.student)
        self.assertEqual(client.post('/enroll/2/').status_code,403)
        self.assertEqual(client.get('/enroll/2/').status_code,405)
        self.assertEqual(client.get('/logout/').status_code,405)

    def test_price_capacity_and_idempotency(self):
        self.client.force_login(self.other)
        self.client.post('/enroll/1/',{'amount':'1'})
        order=Order.objects.get(student=self.other,course=self.course)
        self.assertEqual(order.amount,1200000)
        self.client.post('/enroll/1/');self.assertEqual(Order.objects.count(),1)
        settle(order.pk,'receipt-123',self.admin);settle(order.pk,'receipt-123',self.admin)
        self.assertEqual(Enrollment.objects.filter(student=self.other,course=self.course).count(),1)
        extra=User.objects.create_user('extra','extra@example.invalid')
        order2=Order.objects.create(student=extra,course=self.course,amount=1200000)
        result=settle(order2.pk,'receipt-456',self.admin)
        self.assertEqual(result.status,'review');self.assertFalse(Enrollment.objects.filter(student=extra).exists())

    def test_student_cannot_approve_payment(self):
        order=Order.objects.create(student=self.other,course=self.course,amount=1200000)
        self.client.force_login(self.other)
        self.assertEqual(self.client.post(reverse('approve_order',args=[order.pk]),{'reference':'fake'}).status_code,403)
        order.refresh_from_db();self.assertEqual(order.status,'pending')

    def test_placement_server_scoring_and_duplicate_submit(self):
        self.client.force_login(self.student)
        self.assertEqual(self.client.get('/placement/').status_code,200)
        self.client.post('/placement/',{'action':'start'})
        first=self.client.session['placement'];first_data={'nonce':first['nonce'],'answer':QUESTIONS[first['q']][3]}
        self.client.post('/placement/',first_data)
        self.client.post('/placement/',first_data)
        self.assertEqual(len(self.client.session['placement']['answers']),1)
        for _ in range(11):
            state=self.client.session['placement'];q=state['q']
            self.client.post('/placement/',{'nonce':state['nonce'],'answer':QUESTIONS[q][3],'score':'0','level':'fake'})
        r=PlacementResult.objects.get(student=self.student)
        self.assertEqual(r.score,100);self.assertEqual(len(r.answers),12)
        self.assertEqual(self.client.get(reverse('placement_result',args=[r.pk])).status_code,200)
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(reverse('placement_result',args=[r.pk])).status_code,404)

    def test_attendance_scope_and_grade_validation(self):
        self.client.force_login(self.teacher)
        self.client.post('/lessons/1/attendance/',{'present':[self.student.pk,self.other.pk]})
        self.assertTrue(Attendance.objects.get(student=self.student,lesson=self.lesson).present)
        self.assertFalse(Attendance.objects.filter(student=self.other).exists())
        response=self.client.post('/classes/1/grade/',{'student':self.other.pk,'title':'Exam','score':95})
        self.assertEqual(response.status_code,200);self.assertFalse(Grade.objects.exists())
        self.client.post('/classes/1/grade/',{'student':self.student.pk,'title':'Exam','score':101})
        self.assertFalse(Grade.objects.exists())
        self.client.post('/classes/1/grade/',{'student':self.student.pk,'title':'Exam','score':95,'feedback':'Good'})
        self.assertEqual(Grade.objects.get().score,95)

    def test_messages_broadcast_and_xss(self):
        self.client.force_login(self.teacher)
        self.client.post('/messages/new/',{'audience':'all','subject':'bad','body':'bad'})
        self.assertFalse(Message.objects.exists())
        self.client.force_login(self.admin)
        self.client.post('/messages/new/',{'audience':'student','subject':'Notice','body':'<script>alert(1)</script>'})
        self.client.force_login(self.student);response=self.client.get('/messages/')
        self.assertContains(response,'&lt;script&gt;');self.assertNotContains(response,'<script>alert')
        self.client.force_login(self.teacher);self.assertNotContains(self.client.get('/messages/'),'Notice')

    def test_live_chat_control_and_membership(self):
        self.client.force_login(self.other)
        self.assertEqual(self.client.post('/classes/1/live/').status_code,404)
        self.client.force_login(self.teacher)
        self.client.post('/classes/1/live/',{'action':'control'})
        self.client.force_login(self.student)
        self.client.post('/classes/1/live/',{'action':'message','body':'blocked'})
        self.assertFalse(ClassMessage.objects.exists())
        self.assertEqual(self.client.post('/classes/1/live/',{'action':'control'}).status_code,403)
        response=self.client.post('/classes/1/live/',{'action':'hand'})
        self.assertTrue(any(p['hand'] for p in response.json()['peers']))

    def test_login_throttling(self):
        for _ in range(9): response=self.client.post('/login/',{'username':'learner','password':'wrong'})
        self.assertContains(response,'تلاش‌های ورود بیش از حد')
        response=self.client.post('/login/',{'username':'learner','password':'Strong-demo-938!'})
        self.assertNotIn('_auth_user_id',self.client.session)

    @override_settings(ZARINPAL_MERCHANT_ID='merchant-test')
    @patch('academy.payments.requests.post')
    def test_gateway_amount_verify_and_replay(self,mock_post):
        order=Order.objects.create(student=self.other,course=self.course,amount=1200000)
        self.client.force_login(self.other)
        mock_post.return_value=Mock(json=lambda:{'data':{'code':100,'authority':'A00001'}},raise_for_status=lambda:None)
        self.client.post(reverse('pay',args=[order.pk]))
        self.assertEqual(mock_post.call_args.kwargs['json']['amount'],12000000)
        order.refresh_from_db();self.assertEqual(order.status,'pending')
        mock_post.return_value=Mock(json=lambda:{'data':{'code':100,'ref_id':987654}},raise_for_status=lambda:None)
        self.client.get('/payment/callback/?Authority=A00001&Status=OK')
        self.client.get('/payment/callback/?Authority=A00001&Status=OK')
        order.refresh_from_db();self.assertEqual(order.status,'paid')
        self.assertEqual(Enrollment.objects.filter(student=self.other,course=self.course).count(),1)

    @override_settings(GOOGLE_CLIENT_ID='',GOOGLE_CLIENT_SECRET='')
    def test_missing_google_configuration(self):
        self.assertRedirects(self.client.get('/auth/google/'),'/login/')

    @override_settings(OPENAI_API_KEY='test-key',OPENAI_MODEL='test-model')
    @patch('academy.ai.requests.post')
    def test_ai_opt_in_minimal_data_and_one_request(self,mock_post):
        r=PlacementResult.objects.create(student=self.student,score=60,level='B1')
        self.client.force_login(self.student);url=reverse('study_plan',args=[r.pk])
        self.client.post(url);mock_post.assert_not_called()
        mock_post.return_value=Mock(json=lambda:{'output':[{'type':'message','content':[{'type':'output_text','text':'تمرین روز اول'}]}]},raise_for_status=lambda:None)
        self.client.post(url,{'consent':'yes'});self.client.post(url,{'consent':'yes'})
        self.assertEqual(mock_post.call_count,1)
        payload=mock_post.call_args.kwargs['json'];self.assertNotIn(self.student.email,str(payload));self.assertFalse(payload['store'])
        self.assertEqual(StudyPlan.objects.get().body,'تمرین روز اول')
