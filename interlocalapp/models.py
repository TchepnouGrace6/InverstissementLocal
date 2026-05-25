from django.db import models
from django.utils import timezone

class Utilisateur(models.Model):
    ROLES = [
        ('porteur de projet', 'Porteur de Projet'),
        ('investisseur', 'Investisseur'),
        ('administrateur', 'Administrateur'),
    ]
    
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    telephone = models.CharField(max_length=15)
    adresse = models.TextField()
    email = models.EmailField()
    password = models.CharField(max_length=128)  # 100 trop court pour les hashes Django
    role = models.CharField(max_length=20, choices=ROLES, default='porteur de projet')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nom} {self.email} ({self.role})"

class Categorie(models.Model):
    nom = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.nom}"


class Projet(models.Model):
    STATUT_CHOICES = (
        ('propose', 'Proposé'),
        ('validé', 'Validé'),    # ← accent, correspond aux tests
        ('financé', 'Financé'),  # ← accent, correspond aux tests
    )

    porteur = models.ForeignKey(
        Utilisateur,
        on_delete=models.CASCADE,
        related_name='projets',
        limit_choices_to={'role': 'porteur de projet'}
    )

    categorie = models.ForeignKey(
        Categorie,
        on_delete=models.SET_NULL,
        null=True
    )

    titre = models.CharField(max_length=200)
    description = models.TextField()
    montant_objectif = models.DecimalField(max_digits=12, decimal_places=2)
    montant_collecte = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    date_debut = models.DateField(default=timezone.now)
    date_fin = models.DateField()
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='propose'
    )

    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.titre} {self.description} ({self.statut})"


class Investissement(models.Model):
    investisseur = models.ForeignKey(
        Utilisateur,
        on_delete=models.CASCADE,
        related_name='investissements',
        limit_choices_to={'role': 'investisseur'}  # ← minuscule, corrigé
    )

    projet = models.ForeignKey(
        Projet,
        on_delete=models.CASCADE,
        related_name='investissements'
    )

    montant = models.DecimalField(max_digits=12, decimal_places=2)
    date_investissement = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.investisseur.nom} → {self.projet.titre}"


class ValidationProjet(models.Model):
    projet = models.OneToOneField(Projet, on_delete=models.CASCADE)
    admin = models.ForeignKey(
        Utilisateur,
        on_delete=models.SET_NULL,
        null=True,
        limit_choices_to={'role': 'administrateur'}  # ← minuscule, corrigé
    )
    date_validation = models.DateTimeField(auto_now_add=True)
    commentaire = models.TextField(blank=True)

    def __str__(self):
        return f"Validation de {self.projet.titre}"