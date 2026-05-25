# ============================================
# STAGE 1 : Build
# ============================================
FROM python:3.13-slim AS builder

WORKDIR /app

# Copier et installer les dépendances
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ============================================
# STAGE 2 : Production (image finale légère)
# ============================================
FROM python:3.13-slim AS production

WORKDIR /app

# Créer un utilisateur non-root (sécurité)
RUN addgroup --system appgroup && \
    adduser --system --ingroup appgroup appuser

# Copier uniquement les dépendances installées depuis le stage 1
COPY --from=builder /usr/local/lib/python3.13/site-packages/ \
     /usr/local/lib/python3.13/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# Copier le code source
COPY . .

# Donner les droits à l'utilisateur non-root
RUN chown -R appuser:appgroup /app

# Basculer vers l'utilisateur non-root
USER appuser

# Exposer le port
EXPOSE 8000

# Lancer l'application Django
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]