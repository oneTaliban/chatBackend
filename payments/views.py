from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from django.conf import settings
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from .models import Donation, SubscriptionPlan, UserSubscription, PaymentWebhook, Payment
from .serializers import DonationSerializer, SubscriptionPlanSerializer, UserSubscriptionSerializer, PaymentCreateSerializer, PaymentSerializer

import stripe
import base64
import requests
import json

from datetime import datetime

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
    

@api_view(['post'])
@permission_classes([IsAuthenticated])
def create_payment(request):
    '''Unified payment endpoint'''
    serializer = PaymentCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data
    payment_method = data['payment_method']

    try:
        if payment_method == 'stripe':
            return create_stripe_payment_intent(request)
        elif payment_method == 'mpesa':
            return initiate_mpesa_payment(request)
        elif payment_method == 'bitcoin':
            return create_bitcoin_payment(request)
        else:
            return Response(
                {'error': 'Unsupported payment method'},
                status=status.HTTP_400_BAD_REQUEST
            )

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)



# payment views

#M-pesa
@api_view(['post'])
@permission_classes([IsAuthenticated])
def initiate_mpesa_payment(request):
    try:
        data = request.data
        phone = data['phone']
        amount = data['amount']

        #Get M-pesa access token
        auth_string = f"{settings.MPESA_CONSUMER_KEY}:{settings.MPESA_CONSUMER_SECRET}"
        encoded_auth = base64.b64encode(auth_string.encode()).decode()
        token_response = requests.get(
            'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials',
            headers={'Authorization': f'Basic {encoded_auth}'}
        )
        access_token = token_response.json()['access_token']

        #prepare STK Push
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        business_shortcode = settings.MPESA_BUSINESS_SHORTCODE
        passkey = settings.MPESA_PASSKEY

        password = base64.b64encode(
            f"{business_shortcode}{passkey}{timestamp}".encode()
        ).decode()

        stk_payload = {
            'BusinessShortCode': business_shortcode,
            'Password': password,
            'Timestamp': timestamp,
            'TransactionType': 'CustomerPayBillOnline',
            'Amount': amount,
            'PartyA': f"254{phone[-9:]}", #Format phone number
            'PartyB': business_shortcode,
            'PhoneNumber': f"254{phone[-9:]}",
            'CallBackUrl': f'{settings.BASE_URL}/api/mpesa/callback/',
            'AccountReference': f"ORDER{timezone.now().timestamp()}",
            'TransactionDesc': 'Payment for goods/services'
        }

        stk_response = requests.post(
            'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest',
            json=stk_payload,
            headers={
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
        )

        response_data = stk_response.json()
        if response_data.get('ResponseCode') == '0':
            #Create pending payment record
            payment = Payment.objects.create(
                user=request.user,
                payment_method = 'mpesa',
                amount= amount,
                status='pending',
                transaction_id = response_data['CheckoutRequestID'],
                payment_details = {'mpesa_response': response_data}
            )

            return Response({
                'success': True,
                'checkout_request_id': response_data['CheckoutRequestID'],
                'payment_id': payment.id
            })
        else:
            return Response({
                'error': response_data.get('ResponseDescription', 'M-Pesa payment failed')
            }, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['post'])
@csrf_exempt
def mpesa_callback(request):
    '''Handle M-pesa STK Push callback'''
    callback_data = request.data

    try:
        result_code = callback_data['Body']['stkCallback']['ResultCode']
        checkout_request_id = callback_data['Body']['stkCallback']['CheckoutRequestID']

        payment = Payment.objects.get(transaction_id=checkout_request_id)

        if result_code == 0:
            payment.status = 'completed'
            #Extract transaction details
            callback_items = callback_data['Body']['stkCallback']['CallbackMetadata']['Item']
        for item in callback_items:
            if item['Name'] == 'MpesaReceiptNumber':
                payment.payment_details['receipt_number'] = item['Value']

            if item['Name'] == 'PhoneNumber':
                payment.payment_details['phone'] = item['Value']
        else:
            payment.status = 'failed'
        
        payment.payment_details['callback_data'] = callback_data
        payment.save()

    except Exception as e:
        print(f"M-Pesa callback error: {e}")
    return Response({'success': True})

#stripe
@api_view(['post'])
@permission_classes([IsAuthenticated])
def create_stripe_payment_intent(request):
    try: 
        data = request.data
        amount = int(float(data['amount']) * 100) #cents

        #create stripe payment intent
        intent = stripe.PaymentIntent.create(
            amount=amount,
            currency = data.get('currency', 'usd'),
            automatic_payment_methods={'enabled': True},
            metadat={
                'user_id': request.user.id,
                'order_id': data.get('order_id', '')
            }
        )

        #create a payment record
        payment = Payment.objects.create(
            user = request.user,
            payment_method = 'stripe',
            amount=data['amount'],
            currency=data.get('currency', 'USD'),
            status='pending',
            transaction_id = intent.id,
            payment_details={'client_secret': intent.client_secret},
        )

        return Response({
            'client_secret': intent.client_secret,
            'payment_id': payment.id
        })
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['post'])
@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        return Response({'error': 'Invalid payload'} , status=400)
    except stripe.error.SignatureVerificationError as e:
        return Response({'error': 'Invalid signature'}, status=400)

    #Handle the event
    if event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        try:
            payment = Payment.objects.get(transaction_id=payment_intent['id'])
            payment.status = 'completed'
            payment.payment_details['stripe_data'] = payment_intent
            payment.save()

            #To trigger post-payment actions here
        except Payment.DoesNotExist:
            pass

        return Response({'success': True})
#bitcoin
def create_bitcoin_payment(request):
    pass