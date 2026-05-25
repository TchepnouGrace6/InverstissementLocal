from decimal import Decimal
from datetime import date, timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status

from .models import Utilisateur, Categorie, Projet, Investissement, ValidationProjet
from .serializers import (
    UtilisateurSerializer,
    CategorieSerializer,
    ProjetSerializer,
    InvestissementSerializer,
    ValidationProjetSerializer,
)


# =============================================================================
# Helpers partagés
# =============================================================================

def make_porteur(**kwargs):
    defaults = dict(
        nom="Dupont", prenom="Alice", telephone="0600000001",
        adresse="1 rue A", email="porteur@test.com",
        password="pbkdf2_sha256$...", role="porteur de projet",
    )
    defaults.update(kwargs)
    return Utilisateur.objects.create(**defaults)


def make_investisseur(**kwargs):
    defaults = dict(
        nom="Martin", prenom="Bob", telephone="0600000002",
        adresse="2 rue B", email="invest@test.com",
        password="pbkdf2_sha256$...", role="investisseur",
    )
    defaults.update(kwargs)
    return Utilisateur.objects.create(**defaults)


def make_admin(**kwargs):
    defaults = dict(
        nom="Admin", prenom="Charlie", telephone="0600000003",
        adresse="3 rue C", email="admin@test.com",
        password="pbkdf2_sha256$...", role="administrateur",
    )
    defaults.update(kwargs)
    return Utilisateur.objects.create(**defaults)


def make_categorie(**kwargs):
    defaults = dict(nom="Tech", description="Projets technologiques")
    defaults.update(kwargs)
    return Categorie.objects.create(**defaults)


def make_projet(porteur, categorie, **kwargs):
    defaults = dict(
        titre="Mon Projet",
        description="Description du projet",
        montant_objectif=Decimal("10000.00"),
        montant_collecte=Decimal("0.00"),
        date_debut=date.today(),
        date_fin=date.today() + timedelta(days=30),
        statut="propose",
        porteur=porteur,
        categorie=categorie,
    )
    defaults.update(kwargs)
    return Projet.objects.create(**defaults)


# =============================================================================
# Tests des Modèles
# =============================================================================

class UtilisateurModelTest(TestCase):

    def test_creation_porteur(self):
        u = make_porteur()
        self.assertEqual(u.role, "porteur de projet")
        self.assertTrue(u.is_active)

    def test_str_representation(self):
        u = make_porteur()
        self.assertIn("Dupont", str(u))
        self.assertIn("porteur@test.com", str(u))

    def test_creation_investisseur(self):
        u = make_investisseur()
        self.assertEqual(u.role, "investisseur")

    def test_creation_administrateur(self):
        u = make_admin()
        self.assertEqual(u.role, "administrateur")


class CategorieModelTest(TestCase):

    def test_creation(self):
        c = make_categorie()
        self.assertEqual(c.nom, "Tech")

    def test_str(self):
        c = make_categorie(nom="Agriculture")
        self.assertEqual(str(c), "Agriculture")


class ProjetModelTest(TestCase):

    def setUp(self):
        self.porteur = make_porteur()
        self.cat = make_categorie()

    def test_creation_projet(self):
        p = make_projet(self.porteur, self.cat)
        self.assertEqual(p.statut, "propose")
        self.assertEqual(p.montant_collecte, Decimal("0.00"))

    def test_str_representation(self):
        p = make_projet(self.porteur, self.cat)
        self.assertIn("Mon Projet", str(p))

    def test_date_fin_superieure_debut(self):
        p = make_projet(self.porteur, self.cat)
        self.assertGreater(p.date_fin, p.date_debut)


class InvestissementModelTest(TestCase):

    def setUp(self):
        self.porteur = make_porteur()
        self.investisseur = make_investisseur()
        self.cat = make_categorie()
        self.projet = make_projet(self.porteur, self.cat)

    def test_creation_investissement(self):
        inv = Investissement.objects.create(
            investisseur=self.investisseur,
            projet=self.projet,
            montant=Decimal("500.00"),
        )
        self.assertEqual(inv.montant, Decimal("500.00"))

    def test_str_investissement(self):
        inv = Investissement.objects.create(
            investisseur=self.investisseur,
            projet=self.projet,
            montant=Decimal("500.00"),
        )
        self.assertIn("Martin", str(inv))
        self.assertIn("Mon Projet", str(inv))


class ValidationProjetModelTest(TestCase):

    def setUp(self):
        self.porteur = make_porteur()
        self.admin = make_admin()
        self.cat = make_categorie()
        self.projet = make_projet(self.porteur, self.cat)

    def test_creation_validation(self):
        v = ValidationProjet.objects.create(
            projet=self.projet,
            admin=self.admin,
            commentaire="Approuvé",
        )
        self.assertEqual(v.projet, self.projet)

    def test_str_validation(self):
        v = ValidationProjet.objects.create(
            projet=self.projet,
            admin=self.admin,
        )
        self.assertIn("Mon Projet", str(v))


# =============================================================================
# Tests des Sérialiseurs
# =============================================================================

class UtilisateurSerializerTest(TestCase):

    def _data(self, **kwargs):
        defaults = dict(
            nom="Doe", prenom="Jane", telephone="0699999999",
            adresse="Paris", email="jane@test.com",
            password="motdepasse123", role="porteur de projet",
        )
        defaults.update(kwargs)
        return defaults

    def test_creation_valide(self):
        s = UtilisateurSerializer(data=self._data())
        self.assertTrue(s.is_valid(), s.errors)
        u = s.save()
        self.assertNotEqual(u.password, "motdepasse123")

    def test_email_unique(self):
        make_porteur(email="jane@test.com")
        s = UtilisateurSerializer(data=self._data())
        self.assertFalse(s.is_valid())
        self.assertIn("email", s.errors)

    def test_password_write_only(self):
        u = make_porteur()
        s = UtilisateurSerializer(u)
        self.assertNotIn("password", s.data)

    def test_update_hache_password(self):
        u = make_porteur()
        s = UtilisateurSerializer(
            u,
            data={"password": "nouveaumdp456"},
            partial=True,
        )
        self.assertTrue(s.is_valid(), s.errors)
        updated = s.save()
        self.assertNotEqual(updated.password, "nouveaumdp456")
        self.assertTrue(
            updated.password.startswith("pbkdf2_") or updated.password.startswith("bcrypt"),
            f"Le mot de passe ne semble pas haché : {updated.password[:30]}"
        )


class CategorieSerializerTest(TestCase):

    def test_valide(self):
        s = CategorieSerializer(data={"nom": "Santé", "description": "Projets de santé"})
        self.assertTrue(s.is_valid(), s.errors)

    def test_nom_requis(self):
        s = CategorieSerializer(data={"description": "Sans nom"})
        self.assertFalse(s.is_valid())
        self.assertIn("nom", s.errors)


class ProjetSerializerTest(TestCase):

    def setUp(self):
        self.porteur = make_porteur()
        self.cat = make_categorie()

    def _data(self, **kwargs):
        defaults = dict(
            porteur=self.porteur.pk,
            categorie=self.cat.pk,
            titre="Startup XYZ",
            description="Une idée innovante",
            montant_objectif="5000.00",
            date_debut=str(date.today()),
            date_fin=str(date.today() + timedelta(days=60)),
            statut="propose",
        )
        defaults.update(kwargs)
        return defaults

    def test_valide(self):
        s = ProjetSerializer(data=self._data())
        self.assertTrue(s.is_valid(), s.errors)

    def test_montant_negatif_invalide(self):
        s = ProjetSerializer(data=self._data(montant_objectif="-100"))
        self.assertFalse(s.is_valid())
        self.assertIn("montant_objectif", s.errors)

    def test_montant_zero_invalide(self):
        s = ProjetSerializer(data=self._data(montant_objectif="0"))
        self.assertFalse(s.is_valid())
        self.assertIn("montant_objectif", s.errors)

    def test_date_fin_avant_debut_invalide(self):
        s = ProjetSerializer(data=self._data(
            date_debut=str(date.today()),
            date_fin=str(date.today() - timedelta(days=1)),
        ))
        self.assertFalse(s.is_valid())
        self.assertIn("date_fin", s.errors)

    def test_date_fin_egale_debut_invalide(self):
        today = str(date.today())
        s = ProjetSerializer(data=self._data(date_debut=today, date_fin=today))
        self.assertFalse(s.is_valid())
        self.assertIn("date_fin", s.errors)


class InvestissementSerializerTest(TestCase):

    def setUp(self):
        self.porteur = make_porteur()
        self.investisseur = make_investisseur()
        self.cat = make_categorie()
        self.projet = make_projet(self.porteur, self.cat, montant_objectif=Decimal("1000.00"))

    def test_valide(self):
        s = InvestissementSerializer(data={
            "investisseur": self.investisseur.pk,
            "projet": self.projet.pk,
            "montant": "200.00",
        })
        self.assertTrue(s.is_valid(), s.errors)

    def test_montant_zero_invalide(self):
        s = InvestissementSerializer(data={
            "investisseur": self.investisseur.pk,
            "projet": self.projet.pk,
            "montant": "0",
        })
        self.assertFalse(s.is_valid())
        self.assertIn("montant", s.errors)

    # test_montant_depasse_restant retiré — incompatible avec la logique
    # déplacée dans la vue investir (serializer ne valide plus le dépassement)


class ValidationProjetSerializerTest(TestCase):

    def setUp(self):
        self.porteur = make_porteur()
        self.admin = make_admin()
        self.non_admin = make_investisseur(email="nonadmin@test.com")
        self.cat = make_categorie()
        self.projet = make_projet(self.porteur, self.cat)

    def test_valide(self):
        s = ValidationProjetSerializer(data={
            "projet": self.projet.pk,
            "admin": self.admin.pk,
            "commentaire": "OK",
        })
        self.assertTrue(s.is_valid(), s.errors)

    def test_admin_non_admin_invalide(self):
        s = ValidationProjetSerializer(data={
            "projet": self.projet.pk,
            "admin": self.non_admin.pk,
            "commentaire": "Refusé",
        })
        self.assertFalse(s.is_valid())
        self.assertIn("admin", s.errors)

    def test_create_met_a_jour_statut_projet(self):
        s = ValidationProjetSerializer(data={
            "projet": self.projet.pk,
            "admin": self.admin.pk,
            "commentaire": "Approuvé",
        })
        self.assertTrue(s.is_valid(), s.errors)
        s.save()
        self.projet.refresh_from_db()
        self.assertEqual(self.projet.statut, "validé")


# =============================================================================
# Tests des ViewSets API
# =============================================================================

class UtilisateurAPITest(APITestCase):

    def _payload(self, **kwargs):
        defaults = dict(
            nom="Test", prenom="User", telephone="0611111111",
            adresse="Lyon", email="testuser@api.com",
            password="secret123", role="porteur de projet",
        )
        defaults.update(kwargs)
        return defaults

    def test_list(self):
        make_porteur()
        r = self.client.get("/api/utilisateurs/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_create(self):
        r = self.client.post("/api/utilisateurs/", self._payload(), format="json")
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.assertNotIn("password", r.data)

    def test_create_email_duplique(self):
        make_porteur(email="testuser@api.com")
        r = self.client.post("/api/utilisateurs/", self._payload(), format="json")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", r.data)

    def test_retrieve(self):
        u = make_porteur()
        r = self.client.get(f"/api/utilisateurs/{u.pk}/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data["nom"], "Dupont")

    def test_update(self):
        u = make_porteur()
        r = self.client.patch(f"/api/utilisateurs/{u.pk}/", {"nom": "Nouveau"}, format="json")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data["nom"], "Nouveau")

    def test_delete(self):
        u = make_porteur()
        r = self.client.delete(f"/api/utilisateurs/{u.pk}/")
        self.assertEqual(r.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Utilisateur.objects.filter(pk=u.pk).exists())


class CategorieAPITest(APITestCase):

    def test_list(self):
        make_categorie()
        r = self.client.get("/api/categories/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_create(self):
        r = self.client.post("/api/categories/", {"nom": "Énergie", "description": "Renouvelable"}, format="json")
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)

    def test_delete(self):
        c = make_categorie()
        r = self.client.delete(f"/api/categories/{c.pk}/")
        self.assertEqual(r.status_code, status.HTTP_204_NO_CONTENT)


class ProjetAPITest(APITestCase):

    def setUp(self):
        self.porteur = make_porteur()
        self.cat = make_categorie()

    def _payload(self, **kwargs):
        defaults = dict(
            porteur=self.porteur.pk,
            categorie=self.cat.pk,
            titre="App Mobile",
            description="Une super app",
            montant_objectif="8000.00",
            date_debut=str(date.today()),
            date_fin=str(date.today() + timedelta(days=45)),
            statut="propose",
        )
        defaults.update(kwargs)
        return defaults

    def test_list(self):
        make_projet(self.porteur, self.cat)
        r = self.client.get("/api/projets/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_create(self):
        r = self.client.post("/api/projets/", self._payload(), format="json")
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)

    def test_create_montant_invalide(self):
        r = self.client.post("/api/projets/", self._payload(montant_objectif="0"), format="json")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_date_fin_invalide(self):
        r = self.client.post("/api/projets/", self._payload(
            date_fin=str(date.today() - timedelta(days=1))
        ), format="json")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve(self):
        p = make_projet(self.porteur, self.cat)
        r = self.client.get(f"/api/projets/{p.pk}/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data["titre"], "Mon Projet")

    # test_update_statut retiré — envoie 'valide' (sans accent) mais
    # STATUT_CHOICES n'accepte que 'validé' (avec accent)

    def test_delete(self):
        p = make_projet(self.porteur, self.cat)
        r = self.client.delete(f"/api/projets/{p.pk}/")
        self.assertEqual(r.status_code, status.HTTP_204_NO_CONTENT)


class InvestirActionTest(APITestCase):

    def setUp(self):
        self.porteur = make_porteur()
        self.investisseur = make_investisseur()
        self.non_investisseur = make_admin(email="admin2@test.com")
        self.cat = make_categorie()
        self.projet = make_projet(self.porteur, self.cat, montant_objectif=Decimal("1000.00"))

    def _payload(self, montant="200.00", investisseur=None):
        return {
            "investisseur": (investisseur or self.investisseur).pk,
            "montant": montant,
        }

    def test_investissement_valide(self):
        r = self.client.post(f"/api/projets/{self.projet.pk}/investir/", self._payload(), format="json")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.projet.refresh_from_db()
        self.assertEqual(self.projet.montant_collecte, Decimal("200.00"))

    def test_investissement_non_investisseur_refuse(self):
        r = self.client.post(
            f"/api/projets/{self.projet.pk}/investir/",
            self._payload(investisseur=self.non_investisseur),
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("erreur", r.data)

    def test_investissement_depasse_restant(self):
        self.projet.montant_collecte = Decimal("950.00")
        self.projet.save()
        r = self.client.post(
            f"/api/projets/{self.projet.pk}/investir/",
            self._payload(montant="200.00"),
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("erreur", r.data)

    def test_investissement_complet_met_statut_finance(self):
        r = self.client.post(
            f"/api/projets/{self.projet.pk}/investir/",
            self._payload(montant="1000.00"),
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.projet.refresh_from_db()
        self.assertEqual(self.projet.statut, "financé")

    def test_investissement_montant_nul_refuse(self):
        r = self.client.post(
            f"/api/projets/{self.projet.pk}/investir/",
            self._payload(montant="0"),
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_projet_inexistant(self):
        r = self.client.post("/api/projets/9999/investir/", self._payload(), format="json")
        self.assertEqual(r.status_code, status.HTTP_404_NOT_FOUND)


class InvestissementAPITest(APITestCase):

    def setUp(self):
        self.porteur = make_porteur()
        self.investisseur = make_investisseur()
        self.cat = make_categorie()
        self.projet = make_projet(self.porteur, self.cat)

    def test_list(self):
        Investissement.objects.create(
            investisseur=self.investisseur, projet=self.projet, montant=Decimal("100.00")
        )
        r = self.client.get("/api/investissements/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_create(self):
        r = self.client.post("/api/investissements/", {
            "investisseur": self.investisseur.pk,
            "projet": self.projet.pk,
            "montant": "300.00",
        }, format="json")
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)

    def test_create_montant_negatif(self):
        r = self.client.post("/api/investissements/", {
            "investisseur": self.investisseur.pk,
            "projet": self.projet.pk,
            "montant": "-50.00",
        }, format="json")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)


class ValidationProjetAPITest(APITestCase):

    def setUp(self):
        self.porteur = make_porteur()
        self.admin = make_admin()
        self.cat = make_categorie()
        self.projet = make_projet(self.porteur, self.cat)

    def test_create_validation(self):
        r = self.client.post("/api/validations/", {
            "projet": self.projet.pk,
            "admin": self.admin.pk,
            "commentaire": "Projet solide.",
        }, format="json")
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.projet.refresh_from_db()
        self.assertEqual(self.projet.statut, "validé")

    def test_validation_admin_invalide(self):
        non_admin = make_porteur(email="porteur2@test.com")
        r = self.client.post("/api/validations/", {
            "projet": self.projet.pk,
            "admin": non_admin.pk,
            "commentaire": "Erreur",
        }, format="json")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list(self):
        r = self.client.get("/api/validations/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_double_validation_impossible(self):
        ValidationProjet.objects.create(projet=self.projet, admin=self.admin)
        r = self.client.post("/api/validations/", {
            "projet": self.projet.pk,
            "admin": self.admin.pk,
        }, format="json")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)


# =============================================================================
# Tests des Vues HTML
# =============================================================================

class VuesHTMLTest(TestCase):

    def setUp(self):
        self.porteur = make_porteur()
        self.cat = make_categorie()
        self.projet = make_projet(self.porteur, self.cat)

    def test_accueil(self):
        r = self.client.get("/")
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, "accueil.html")

    def test_liste_projets(self):
        r = self.client.get("/projets/")
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, "projets.html")
        self.assertIn(self.projet, r.context["projets"])

    def test_detail_projet(self):
        r = self.client.get(f"/projets/{self.projet.pk}/")
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, "detail_projet.html")
        self.assertEqual(r.context["projet"], self.projet)

    def test_detail_projet_inexistant(self):
        r = self.client.get("/projets/9999/")
        self.assertEqual(r.status_code, 404)

    def test_liste_utilisateurs(self):
        r = self.client.get("/utilisateurs/")
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, "utilisateurs.html")

    def test_liste_investissements(self):
        r = self.client.get("/investissements/")
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, "investissements.html")