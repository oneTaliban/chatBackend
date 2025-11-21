from django.contrib import admin
from .models import Donation, SubscriptionPlan, UserSubscription, PaymentWebhook

admin.site.register(Donation)
admin.site.register(SubscriptionPlan)
admin.site.register(UserSubscription)
admin.site.register(PaymentWebhook)