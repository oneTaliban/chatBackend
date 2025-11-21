from rest_framework import serializers

from .models import Donation , SubscriptionPlan, UserSubscription, PaymentWebhook

class DonationSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source = 'user.email',  read_only=True)

    class Meta:
        model = Donation
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at', 'status')

    def create(self, validated_data):
        #setting user from request if not anonymous
        request = self.context.get('request')
        if request and request.user.is_authenticated and not validated_data.get('is_anonymous'):
            validated_data['user'] = request.user
            validated_data['donor_email'] = request.user.email
        return super().create(validated_data)

class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = '__all__'

class UserSubscriptionSerializer(serializers.ModelSerializer):
    plan_details = SubscriptionPlanSerializer(source = 'plan', read_only=True)
    user_email = serializers.EmailField(source = 'user.email', read_only=True)

    class Meta:
        model = UserSubscription
        fields = '__all__'