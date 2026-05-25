from rest_framework import viewsets, status, serializers as drf_serializers
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404, render
from .models import Utilisateur, Categorie, Projet, Investissement, ValidationProjet
from .serializers import (
    UtilisateurSerializer,
    CategorieSerializer,
    ProjetSerializer,
    InvestissementSerializer,
    ValidationProjetSerializer,
)


# ── Vues HTML ──────────────────────────────────────────────

def accueil(request):
    projets = Projet.objects.all()[:6]
    return render(request, 'accueil.html', {'projets': projets})


def liste_projets(request):
    projets = Projet.objects.all()
    return render(request, 'projets.html', {'projets': projets})


def detail_projet(request, pk):
    projet = get_object_or_404(Projet, pk=pk)
    return render(request, 'detail_projet.html', {'projet': projet})


def liste_utilisateurs(request):
    utilisateurs = Utilisateur.objects.all()
    return render(request, 'utilisateurs.html', {'utilisateurs': utilisateurs})


def liste_investissements(request):
    investissements = Investissement.objects.all()
    return render(request, 'investissements.html', {'investissements': investissements})


# ── Serializer interne pour la vue investir ───────────────

class _InvestirInputSerializer(drf_serializers.Serializer):
    """Serializer léger utilisé uniquement par la vue investir."""

    investisseur = drf_serializers.PrimaryKeyRelatedField(
        queryset=Utilisateur.objects.all()
    )
    montant = drf_serializers.DecimalField(max_digits=12, decimal_places=2)

    def validate_montant(self, value):
        if value <= 0:
            raise drf_serializers.ValidationError("Le montant doit être supérieur à 0.")
        return value


# ── ViewSets API ───────────────────────────────────────────

class UtilisateurViewSet(viewsets.ModelViewSet):
    queryset = Utilisateur.objects.all()
    serializer_class = UtilisateurSerializer


class CategorieViewSet(viewsets.ModelViewSet):
    queryset = Categorie.objects.all()
    serializer_class = CategorieSerializer


class ProjetViewSet(viewsets.ModelViewSet):
    queryset = Projet.objects.all()
    serializer_class = ProjetSerializer

    @action(detail=True, methods=['post'])
    def investir(self, request, pk=None):
        projet = self.get_object()

        serializer = _InvestirInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        investisseur = serializer.validated_data['investisseur']
        montant = serializer.validated_data['montant']

        if investisseur.role.lower() != "investisseur":
            return Response(
                {"erreur": "L'utilisateur doit être un investisseur"},
                status=status.HTTP_400_BAD_REQUEST
            )

        restant = projet.montant_objectif - projet.montant_collecte
        if montant > restant:
            return Response(
                {"erreur": f"Montant supérieur au reste à financer ({restant})"},
                status=status.HTTP_400_BAD_REQUEST
            )

        Investissement.objects.create(
            investisseur=investisseur,
            projet=projet,
            montant=montant,
        )

        projet.montant_collecte += montant
        if projet.montant_collecte >= projet.montant_objectif:
            projet.statut = "financé"
        projet.save()

        return Response(
            {"message": "Investissement effectué avec succès"},
            status=status.HTTP_200_OK
        )


class InvestissementViewSet(viewsets.ModelViewSet):
    queryset = Investissement.objects.all()
    serializer_class = InvestissementSerializer


class ValidationProjetViewSet(viewsets.ModelViewSet):
    queryset = ValidationProjet.objects.all()
    serializer_class = ValidationProjetSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)