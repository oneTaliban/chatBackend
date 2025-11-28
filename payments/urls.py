from django.urls import path, include
from . import views

urlpatterns = [
    #checkout
    path('create/', views.create_payment, name='create-payment'),
    path('stripe/create-intent/', views.create_stripe_payment_intent, name='stripe-create-intent'),
    path('stripe/webhook/', views.stripe_webhook, name='stripe-webhook'),
    path('mpesa/initiate/', views.initiate_mpesa_payment, name='mpesa-initiate'),
    path('mpesa/callback/', views.mpesa_callback, name='mpesa-callback'),
    # path('details/<int:pk>/', views.PaymentDetailView.as_view(), name='payment-detail'),
]