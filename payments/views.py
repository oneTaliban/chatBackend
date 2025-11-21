from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from django.conf import settings

from .models import Donation, SubscriptionPlan, UserSubscription, PaymentWebhook
from .serializers import DonationSerializer, SubscriptionPlanSerializer, UserSubscriptionSerializer

import stripe

stripe.api_key = settings.STRIPE_SECRET_KEY

class DonationListCreateView(generics.ListCreateAPIView):
    serializer_class = DonationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Donation.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class SubscriptionPlanListView(generics.ListAPIView):
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [] # any can view subscription plans

    def get_queryset(self):
        return SubscriptionPlan.objects.filter(is_active=True)
    
class UseSubscriptionDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSubscriptionSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        subscription, created = UserSubscription.objects.get_or_create(
            user = self.request.user,
            defaults={
                'plan': SubscriptionPlan.objects.get(plan_type = 'free'),
                'status': 'active',
            }
        )
        return subscription


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_stripe_checkout_session(request):
    try:
        plan_id = request.data.get('plan_id')
        billing_period = request.data.get('billing_period', 'monthly')

        plan = SubscriptionPlan.objects.get(id=plan_id)
        price = plan.yearly_price if billing_period == 'yearly' else plan.monthly_price

        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[
                {
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': f"{plan.name} Plan",
                            'description': plan.description,
                        },
                        'unit_amount': int(price * 100), # converting to cents
                        'recurring': {
                            'interval': 'year' if billing_period == 'yearly' else 'month',
                        },
                    },
                    'quantity': 1,
                }
            ],
            mode='subscription',
            success_url=settings.FRONTEND_URL + '/subscription/success?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=settings.FRONTEND_URL + '/subscription/cancel',
            customer_email=request.user.email,
            metadata={
                'user_id':  str(request.user.id),
                'plan_id': str(plan.id),
            }
        )

        return Response({'checkout_url': checkout_session.url})
    
    except Exception as e:
        return Response({"checkout error": str(e)}, status=status.HTTP_400_BAD_REQUEST)