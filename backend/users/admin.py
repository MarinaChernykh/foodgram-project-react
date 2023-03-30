from django.contrib import admin

from .models import User, Subscription


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'username', 'first_name',
        'last_name', 'email', 'role'
    )
    list_display_links = ('username',)
    list_filter = ('email', 'username')
    search_fields = ('username',)
    ordering = ('id',)


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'author')
    list_filter = ('user',)
    search_fields = ('user__username', 'author__username')
    ordering = ('user__id', 'author__id')


admin.site.site_header = 'FOODGRAM'
