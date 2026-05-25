from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from .models import Utilisateur, Categorie, Projet, Investissement, ValidationProjet


# -----------------------------
# UtilisateurSerializer
# -----------------------------
class UtilisateurSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = Utilisateur
        fields = ["id", "nom", "prenom", "telephone", "adresse", "email", "password", "role"]

    def validate_email(self, value):
        qs = Utilisateur.objects.filter(email=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Cet e-mail est déjà utilisé.")
        return value

    def create(self, validated_data):
        validated_data['password'] = make_password(validated_data['password'])
        return super().create(validated_data)

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        instance = super().update(instance, validated_data)
        if password:
            instance.password = make_password(password)
            instance.save()
        return instance


# -----------------------------
# CategorieSerializer
# -----------------------------
class CategorieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categorie
        fields = ["id", "nom", "description"]


# -----------------------------
# ProjetSerializer
# -----------------------------
class ProjetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Projet
        fields = [
            "id", "porteur", "categorie", "titre", "description",
            "montant_objectif", "montant_collecte",
            "date_debut", "date_fin", "statut", "date_creation"
        ]

    def validate_montant_objectif(self, value):
        if value is None or value <= 0:
            raise serializers.ValidationError("Le montant objectif doit être supérieur à 0.")
        return value

    def validate_date_fin(self, value):
        date_debut = self.initial_data.get("date_debut")
        if date_debut:
            date_debut = timezone.datetime.strptime(date_debut, "%Y-%m-%d").date()
        else:
            date_debut = timezone.now().date()
        if value <= date_debut:
            raise serializers.ValidationError("La date de fin doit être postérieure à la date de début.")
        return value


# -----------------------------
# InvestissementSerializer
# -----------------------------
class InvestissementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Investissement
        fields = ["id", "investisseur", "projet", "montant", "date_investissement"]

    def validate_montant(self, value):
        if value is None or value <= 0:
            raise serializers.ValidationError("Le montant doit être supérieur à 0.")
        return value

    # validate() supprimée — la logique de dépassement est gérée dans la vue investir


# -----------------------------
# ValidationProjetSerializer
# -----------------------------
class ValidationProjetSerializer(serializers.ModelSerializer):
    class Meta:
        model = ValidationProjet
        fields = ["id", "projet", "admin", "commentaire", "date_validation"]

    def validate_admin(self, value):
        if value.role.lower() != "administrateur":
            raise serializers.ValidationError("L'utilisateur doit être un administrateur.")
        return value

    def create(self, validated_data):
        projet = validated_data["projet"]
        projet.statut = "validé"
        projet.save()
        return super().create(validated_data)