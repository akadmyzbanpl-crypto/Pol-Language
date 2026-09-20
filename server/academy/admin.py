from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Course, Lesson, Enrollment, Order, Audit, PlacementResult
admin.site.site_header='مدیریت سیستمی آموزشگاه پل'
@admin.register(User)
class PolUserAdmin(UserAdmin):
    fieldsets=UserAdmin.fieldsets+(('نقش آموزشی',{'fields':('role',)}),)
    list_display=('username','email','role','is_active','is_staff')
@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display=('title','mode','level','price','published')
    list_filter=('published','mode','category')
    search_fields=('title',)
@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display=('title','course','starts','completed')
@admin.register(Audit)
class AuditAdmin(admin.ModelAdmin):
    list_display=('created','actor','action','detail')
    def has_add_permission(self,request): return False
    def has_change_permission(self,request,obj=None): return False
    def has_delete_permission(self,request,obj=None): return False
