from django.urls import path, include
from rest_framework import routers
from .view import (
    UtilisateurViewSet,
    CategorieViewSet,
    ProjetViewSet,
    InvestissementViewSet,
    ValidationProjetViewSet,
    accueil,
    liste_projets,
    detail_projet,
    liste_utilisateurs,
    liste_investissements,
)

router = routers.DefaultRouter()
router.register('utilisateurs', UtilisateurViewSet)
router.register('categories', CategorieViewSet)
router.register('projets', ProjetViewSet)
router.register('investissements', InvestissementViewSet)
router.register('validations', ValidationProjetViewSet)

urlpatterns = [
    path('', accueil, name='accueil'),
    path('projets/', liste_projets, name='projets'),
    path('projets/<int:pk>/', detail_projet, name='detail_projet'),
    path('utilisateurs/', liste_utilisateurs, name='utilisateurs'),
    path('investissements/', liste_investissements, name='investissements'),
    path('api/', include(router.urls)),
]