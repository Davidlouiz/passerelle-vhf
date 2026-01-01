# Passerelle VHF - Balises Météo Vocales

> Système autohébergé qui annonce vocalement sur radio VHF les mesures de vent provenant de stations météo en ligne.

**🎯 Pour qui ?** Pilotes de parapente, deltaplane, kitesurf, vélivoles et tous les passionnés de sports aériens qui souhaitent automatiser les annonces météo sur leur fréquence VHF locale.

## ✨ Fonctionnalités

- 🌊 **Multi-canaux** : Gérez plusieurs balises indépendantes sur différentes fréquences
- 🌐 **Multi-sources** : Compatible FFVL (Fédération Française de Vol Libre) et OpenWindMap/Pioupiou
- 🔊 **Voix françaises naturelles** : 6 voix de synthèse vocale hors ligne (pas d'internet requis pour la synthèse)
- 📡 **Contrôle radio automatique** : PTT (Push-To-Talk) via GPIO pour Raspberry Pi
- 🔒 **Sécurité maximale** : Aucune émission parasite en cas d'erreur (architecture fail-safe)
- ⏰ **Planification intelligente** : Programmez plusieurs annonces par heure avec des décalages personnalisés
- 🎯 **Fiabilité garantie** : Protection anti-boucle et anti-duplication des annonces
- 🖥️ **Interface web intuitive** : Configuration et surveillance sans ligne de commande

## 📋 Prérequis

### Matériel nécessaire

- **Raspberry Pi** (testé sur Pi 3B+ et Pi 4, 2 Go RAM minimum recommandés)
- **Carte microSD** de 8 Go minimum (16 Go recommandés pour les logs)
- **Radio VHF** compatible avec un contrôle PTT externe
- **Câble PTT** : connexion GPIO Raspberry Pi vers radio (voir [docs/INSTALLATION.md](docs/INSTALLATION.md) pour le câblage)
- **Alimentation** 5V pour le Raspberry Pi
- **Connexion Internet** (Ethernet ou WiFi) pour récupérer les mesures météo

### Logiciel

- **Raspberry Pi OS** (anciennement Raspbian) - version Bullseye ou supérieure
- **Python 3.10+** (installé par défaut sur les versions récentes)
- Pas besoin de connaissances en programmation !

### Légal ⚖️

⚠️ **Important** : Vérifiez la réglementation radio de votre pays avant toute émission. En France, vous devez respecter :
- Les conditions d'utilisation de votre licence radio (VHF aéronautique)
- Les fréquences autorisées pour votre activité
- Les temps d'émission maximaux autorisés

## 🚀 Installation rapide

### Étape 1 : Télécharger le système

Connectez-vous à votre Raspberry Pi en SSH et exécutez :

```bash
# Télécharger le code
sudo git clone https://github.com/votre-utilisateur/passerelle-vhf /opt/vhf-balise

# Aller dans le dossier
cd /opt/vhf-balise

# Lancer l'installation automatique
sudo ./install.sh
```

L'installation prend environ 5-10 minutes et installe automatiquement :
- Toutes les dépendances Python nécessaires
- Les 6 voix françaises de synthèse vocale
- Les services système pour démarrage automatique
- La base de données

### Étape 2 : Premier démarrage

Une fois l'installation terminée :

```bash
# Vérifier que les services sont actifs
sudo systemctl status vhf-balise-web
sudo systemctl status vhf-balise-runner
```

Vous devriez voir `active (running)` en vert.

### Étape 3 : Configuration initiale via l'interface web

1. **Accéder à l'interface** : Ouvrez votre navigateur et allez sur :
   ```
   http://<adresse-ip-du-raspberry>:8000
   ```
   
   💡 *Pour trouver l'IP du Raspberry Pi : `hostname -I`*

2. **Première connexion** :
   - Utilisateur : `admin`
   - Mot de passe : `admin`

3. **⚠️ Changement de mot de passe obligatoire** :
   - Le système vous demandera de changer le mot de passe
   - Choisissez un mot de passe fort et mémorisez-le !

4. **Configurer votre première source de données** :
   - Allez dans "⚙️ Configuration → Providers"
   - Si vous utilisez les balises FFVL, entrez votre clé API FFVL
   - Si vous utilisez Pioupiou (OpenWindMap), rien à configurer !

5. **Activer le système** :
   - Allez dans "⚙️ Configuration → Paramètres système"
   - Configurez le numéro de pin GPIO pour votre PTT (par défaut : GPIO 17)
   - ✅ Activez "Émissions autorisées" (master_enabled)
   - Sauvegardez

6. **Créer votre première balise** :
   - Allez dans "📡 Balises"
   - Cliquez sur "➕ Nouvelle balise"
   - Suivez l'assistant de configuration (voir [GUIDE_UTILISATEUR.md](docs/GUIDE_UTILISATEUR.md))

### 📖 Pour aller plus loin

- **[Guide d'installation détaillé](docs/INSTALLATION.md)** : Câblage PTT, résolution de problèmes, optimisations
- **[Guide utilisateur complet](docs/GUIDE_UTILISATEUR.md)** : Utilisation au quotidien de l'interface web
- **[FAQ - Questions fréquentes](docs/FAQ.md)** : Problèmes courants et solutions

## 🏗️ Architecture technique

Le système fonctionne avec deux processus indépendants qui communiquent via une base de données SQLite :

```
┌─────────────────────┐
│  Interface Web      │  ← Vous configurez ici
│  (Port 8000)        │
│  FastAPI + HTML/JS  │
└──────────┬──────────┘
           │
           ▼
    ┌──────────────┐
    │   Base de    │
    │   données    │
    │   SQLite     │
    └──────┬───────┘
           │
           ▼
┌──────────────────────┐
│   Runner/Scheduler   │  ← Exécute les annonces
│   - Récupère météo   │
│   - Synthétise audio │
│   - Contrôle PTT     │
└──────────┬───────────┘
           │
           ▼
        📡 Radio VHF
```

### Structure des dossiers

```
/opt/vhf-balise/
├── app/                    # 🐍 Code Python du système
│   ├── main.py            # Application web (FastAPI)
│   ├── runner.py          # Moteur d'exécution des annonces
│   ├── models.py          # Structure de la base de données
│   ├── providers/         # Connexion aux sources météo (FFVL, Pioupiou)
│   ├── tts/               # Synthèse vocale (Piper)
│   ├── ptt/               # Contrôle du PTT radio
│   └── ...
├── data/                  # 💾 Données de votre installation
│   ├── vhf-balise.db     # Base de données (votre configuration)
│   ├── audio_cache/       # Fichiers audio pré-générés (cache)
│   ├── logs/              # Historique de fonctionnement
│   └── tts_models/        # Modèles de voix françaises (6 voix)
├── docs/                  # 📖 Documentation détaillée
└── static/                # 🌐 Interface web (HTML/CSS/JavaScript)
```

## 🔧 Gestion quotidienne

### Démarrer/Arrêter le système

```bash
# Démarrer les deux services
sudo systemctl start vhf-balise-web      # Interface web
sudo systemctl start vhf-balise-runner   # Moteur d'annonces

# Arrêter les services
sudo systemctl stop vhf-balise-web
sudo systemctl stop vhf-balise-runner

# Redémarrer (après une mise à jour par exemple)
sudo systemctl restart vhf-balise-web
sudo systemctl restart vhf-balise-runner

# Vérifier l'état
sudo systemctl status vhf-balise-web
sudo systemctl status vhf-balise-runner
```

### Activer le démarrage automatique

Pour que le système démarre automatiquement au démarrage du Raspberry Pi :

```bash
sudo systemctl enable vhf-balise-web
sudo systemctl enable vhf-balise-runner
```

### Consulter les logs en temps réel

```bash
# Logs de l'interface web
sudo journalctl -u vhf-balise-web -f

# Logs du moteur d'annonces (transmission radio)
sudo journalctl -u vhf-balise-runner -f

# Ou consulter les fichiers de logs directement
tail -f /opt/vhf-balise/data/logs/runner.log
```

### Résoudre un problème

1. **Le système ne démarre pas** :
   ```bash
   sudo systemctl status vhf-balise-web
   sudo journalctl -u vhf-balise-web -n 50
   ```

2. **Le runner refuse de démarrer (erreur "Un autre runner tourne déjà")** :
   
   **Diagnostic** : Vérifier si un processus runner tourne réellement :
   ```bash
   pgrep -fa "python.*app.runner"
   ```
   
   **Solution 1** : Si des processus sont listés, les arrêter :
   ```bash
   sudo systemctl stop vhf-balise-runner
   # Ou en manuel : pkill -TERM -f "python.*app.runner"
   ```
   
   **Solution 2** : Si aucun processus n'est listé mais l'erreur persiste (verrou PID bloqué) :
   ```bash
   # Option A : Déblocage automatique via script
   cd /opt/vhf-balise
   sudo ./unlock_runner.sh
   
   # Option B : Déblocage manuel
   sudo rm -f /opt/vhf-balise/data/runner.pid
   
   # Option C : Démarrage forcé (en développement uniquement)
   python -m app.runner --force
   ```
   
   ℹ️ **Note** : Le système nettoie normalement automatiquement les verrous obsolètes. Si ce problème persiste, vérifiez les permissions sur le dossier `data/`.

3. **Pas d'annonces radio** :
   - Vérifiez dans l'interface web que "Émissions autorisées" est activé
   - Consultez l'historique des émissions dans l'interface
   - Vérifiez les logs : `sudo journalctl -u vhf-balise-runner -f`

4. **Connexion perdue à l'interface web** :
   ```bash
   sudo systemctl restart vhf-balise-web
   ```

Voir [FAQ.md](docs/FAQ.md) pour plus de solutions aux problèmes courants.

## 🛠️ Pour les développeurs

### Environnement de développement local

```bash
# Créer un environnement virtuel Python
python3 -m venv venv
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt

# Lancer en mode développement (rechargement automatique)
# Terminal 1 : API web
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 : Runner
python -m app.runner
```

### Lancer les tests

```bash
pytest tests/ -v
```

### Contribuer

Nous accueillons les contributions ! Consultez [CONTRIBUTING.md](CONTRIBUTING.md) pour :
- Ajouter un nouveau provider météo
- Améliorer les voix ou templates
- Corriger des bugs
- Améliorer la documentation

## 🔒 Sécurité et Fail-Safe

Le système est conçu avec une architecture **fail-safe** (sécurité par défaut) :

⚠️ **Règles de sécurité absolues** :
- ✅ **Journalisation avant émission** : Chaque annonce est enregistrée en base de données AVANT toute émission radio
- ✅ **Pas de mesure périmée** : Aucune annonce si les données météo sont trop anciennes
- ✅ **Fail-closed** : En cas d'erreur, le système bloque l'émission (pas de transmission parasite)
- ✅ **Timeout PTT** : Le PTT (Push-To-Talk) est automatiquement coupé après 30 secondes maximum
- ✅ **Protection anti-boucle** : Système d'idempotence qui empêche les duplications d'annonces
- ✅ **Verrou global** : Une seule émission à la fois, même avec plusieurs balises configurées

Ces mécanismes garantissent qu'aucune émission radio parasite ne peut se produire en cas de dysfonctionnement.

## 🌐 Sources de données météo supportées

### FFVL (Fédération Française de Vol Libre)

- **Site web** : [balisemeteo.com](https://www.balisemeteo.com/)
- **Clé API requise** : Oui (gratuite sur demande auprès de la FFVL)
- **Exemple d'URL** : `https://www.balisemeteo.com/balise.php?idBalise=67`
- **Données disponibles** : Vent moyen, rafales, direction, température, etc.

### OpenWindMap / Pioupiou

- **Site web** : [openwindmap.org](https://www.openwindmap.org/)
- **Clé API requise** : Non (accès public gratuit)
- **Exemple d'URL** : `https://www.openwindmap.org/pioupiou-385`
- **API** : `http://api.pioupiou.fr/v1/live/{station_id}`
- **Données disponibles** : Vent moyen, rafales, direction

💡 **Bon à savoir** : Vous pouvez mélanger les deux sources ! Par exemple, une balise FFVL à Annecy et une Pioupiou à Millau sur la même installation.

## 📝 Licence et Support

### Licence

À définir (projet en développement actif)

### Documentation complète

- 📖 **[Guide d'installation détaillé](docs/INSTALLATION.md)** - Installation pas-à-pas avec câblage PTT
- 👤 **[Guide utilisateur](docs/GUIDE_UTILISATEUR.md)** - Utilisation quotidienne de l'interface web
- ❓ **[FAQ](docs/FAQ.md)** - Questions fréquentes et dépannage
- 🎤 **[Guide des voix](docs/voix-disponibles.md)** - Choisir et personnaliser les voix françaises
- 📝 **[Variables de template](docs/variables-template.md)** - Personnaliser vos annonces
- 🔧 **[Guide développeur](CONTRIBUTING.md)** - Contribuer au projet

### Support technique

📧 Pour toute question ou problème :
1. Consultez d'abord la [FAQ](docs/FAQ.md)
2. Vérifiez les [issues GitHub](https://github.com/votre-utilisateur/passerelle-vhf/issues)
3. Créez une nouvelle issue si besoin

### Remerciements

Merci aux contributeurs et aux projets open source utilisés :
- [Piper TTS](https://github.com/rhasspy/piper) - Synthèse vocale
- [FastAPI](https://fastapi.tiangolo.com/) - Framework web
- FFVL et OpenWindMap pour les données météo

---

**⚠️ Rappel légal** : Ce système émet sur des fréquences radio réglementées. Assurez-vous d'avoir les autorisations nécessaires avant toute émission sur VHF aéronautique.

**🚀 Bon vol !**
