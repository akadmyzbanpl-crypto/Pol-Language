from django.test import TestCase, override_settings
from .models import Course, User

@override_settings(SECURE_SSL_REDIRECT=False, POL_SITE_ORIGIN='https://example.com', POL_DEMO=False)
class PublicCatalogTests(TestCase):
    def setUp(self):
        teacher=User.objects.create_user(username='private-login', email='private@example.com', password='Test-password-3291', role='teacher', first_name='مدرس', last_name='آموزشگاه')
        self.course=Course.objects.create(title='English course', category='general', mode='onsite', description='Public copy', price=2400000, teacher=teacher, published=True, syllabus='Unit one\nUnit two')
        Course.objects.create(title='PRIVATE DRAFT', category='general', mode='online', description='PRIVATE DRAFT', price=1, published=False)

    def test_only_public_course_and_public_teacher_fields_are_exposed(self):
        response=self.client.get('/api/public/catalog/')
        self.assertEqual(response.status_code,200)
        body=response.json()
        self.assertEqual(len(body['courses']),1)
        self.assertEqual(body['courses'][0]['price'],2400000)
        self.assertEqual(body['courses'][0]['serverPath'],f'/courses/{self.course.pk}/')
        self.assertEqual(body['courses'][0]['syllabus'],['Unit one','Unit two'])
        self.assertEqual(body['teachers'][0]['name'],'مدرس آموزشگاه')
        self.assertNotIn('PRIVATE DRAFT',response.content.decode())
        self.assertNotIn('private@example.com',response.content.decode())
        self.assertNotIn('private-login',response.content.decode())
        self.assertNotIn('password',response.content.decode())

    def test_cors_is_scoped_and_no_credentials_are_enabled(self):
        response=self.client.get('/api/public/catalog/', HTTP_ORIGIN='https://example.com')
        self.assertEqual(response['Access-Control-Allow-Origin'],'https://example.com')
        self.assertNotIn('Access-Control-Allow-Credentials',response)
        self.assertIn('Origin',response['Vary'])
        response=self.client.get('/api/public/catalog/', HTTP_ORIGIN='https://other.example')
        self.assertNotIn('Access-Control-Allow-Origin',response)

    def test_endpoint_cannot_write_and_unpublishing_removes_a_course(self):
        self.assertEqual(self.client.post('/api/public/catalog/', {'published':True}).status_code,405)
        self.course.published=False
        self.course.save(update_fields=['published'])
        response=self.client.get('/api/public/catalog/')
        self.assertEqual(response.json()['courses'],[])
        self.assertEqual(response.json()['teachers'],[])
