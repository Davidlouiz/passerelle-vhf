# Changelog - Passerelle VHF

Toutes les modifications notables de ce projet seront documentées dans ce fichier.

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/),
et ce projet adhère au [Semantic Versioning](https://semver.org/lang/fr/).

## [Non publié]

### Ajouté
- Structure initiale du projet
- Schéma de base de données SQLite complet
- Backend FastAPI avec endpoints de base
- Système multi-providers (FFVL, OpenWindMap)
- Moteur TTS Piper avec cache audio
- Contrôle PTT via GPIO (+ mode mock)
- Runner/Scheduler avec polling et planification TX
- Frontend HTML/CSS/JS de base (connexion, tableau de bord)
- Système de templates pour annonces vocales
- Service de transmission avec verrou TX global
- Tests unitaires (template, URL parsing, scheduling, idempotence)
- Tests d'intégration fail-safe
- Script d'installation automatique
- Services systemd (web + runner)
- Documentation complète (README, CONTRIBUTING)
- Instructions Copilot pour AI agents

### Sécurité
- Architecture fail-safe (fail-closed)
- Règle de péremption stricte des mesures
- Idempotence via tx_id unique
- Journalisation PENDING avant émission
- Watchdog PTT (30s max)
- Authentification JWT avec changement de mot de passe obligatoire

## [0.1.0] - À venir

Version initiale publique

### Fonctionnalités V1
- [ ] Multi-canaux indépendants
- [ ] Multi-providers (FFVL + OpenWindMap)
- [ ] Synthèse vocale hors ligne (Piper)
- [ ] Contrôle PTT GPIO
- [ ] Interface web complète
- [ ] Planification flexible (offsets multiples)
- [ ] Tests manuels (prévisualisation + TX radio)
- [ ] Gestion des collisions (ordre aléatoire + pause)

### À développer
- [ ] Endpoints API complets
- [ ] Interface web complète (tous les écrans)
- [ ] Implémentation complète du runner
- [ ] Procédure TX complète (PENDING → SENT/FAILED)
- [ ] Gestion des credentials providers
- [ ] Simulation timeline
- [ ] Historique TX avec filtres
- [ ] Logs système avec filtres
- [ ] Téléchargement automatique voix Piper

### Améliorations futures (V2+)
- [ ] Multi-radio/multi-fréquence
- [ ] Providers additionnels
- [ ] Variables de template avancées
- [ ] Purge automatique cache audio (LRU)
- [ ] Métriques et monitoring
- [ ] Exposition sécurisée Internet (VPN, TLS)
- [ ] Application mobile
- [ ] Support HTTPS natif
- [ ] Backup/restore configuration
