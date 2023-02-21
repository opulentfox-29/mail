from rest_framework import serializers

from home.models import Proton


class ProtonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Proton
        fields = ('login', 'password', 'duck_name')

    def create(self, validated_data):
        return Proton.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.login = validated_data.get('login', instance.login)
        instance.password = validated_data.get('password', instance.password)
        instance.duck_name = validated_data.get('duck_name', instance.duck_name)
        instance.save()
        return instance
