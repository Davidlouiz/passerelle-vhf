# 📚 Index de la documentation - Passerelle VHF

Bienvenue dans la documentation complète de la Passerelle VHF ! Ce fichier vous guide vers la bonne documentation selon vos besoins.

## 🚀 Par où commencer ?

### Je découvre le projet
👉 **[README.md](../README.md)** - Vue d'ensemble, fonctionnalités, installation rapide

### Je veux installer le système  
👉 **[docs/INSTALLATION.md](INSTALLATION.md)** - Guide pas-à-pas avec câblage PTT et vérifications

### Je veux utiliser l'interface web
👉 **[docs/GUIDE_UTILISATEUR.md](GUIDE_UTILISATEUR.md)** - Utilisation quotidienne et création de balises

### J'ai un problème
👉 **[docs/FAQ.md](FAQ.md)** - Questions fréquentes et dépannage

## 📖 Documentation complète

### Pour les utilisateurs

| Document | Description | Niveau |
|----------|-------------|--------|
| **[README.md](../README.md)** | Vue d'ensemble du système | 🟢 Débutant |
| **[INSTALLATION.md](INSTALLATION.md)** | Installation complète et câblage matériel | 🟡 Intermédiaire |
| **[GUIDE_UTILISATEUR.md](GUIDE_UTILISATEUR.md)** | Utilisation de l'interface web au quotidien | 🟢 Débutant |
| **[FAQ.md](FAQ.md)** | Questions fréquentes et solutions aux problèmes courants | 🟢 Débutant |
| **[voix-disponibles.md](voix-disponibles.md)** | Guide complet des voix françaises disponibles | 🟢 Débutant |
| **[variables-template.md](variables-template.md)** | Personnaliser les annonces vocales | 🟢 Débutant |
| **[personnalisation-prononciation.md](personnalisation-prononciation.md)** | Ajuster la prononciation (avancé) | 🔴 Avancé |

### Pour les développeurs

| Document | Description | Niveau |
|----------|-------------|--------|
| **[CONTRIBUTING.md](../CONTRIBUTING.md)** | Guide pour contribuer au projet | 🟡 Intermédiaire |
| **[CHANGELOG.md](../CHANGELOG.md)** | Historique des versions et modifications | 🟢 Tous |
| **[.github/copilot-instructions.md](../.github/copilot-instructions.md)** | Instructions pour agents IA et développeurs | 🔴 Développeur |

## 🎯 Par cas d'usage

### J'installe pour la première fois

1. 📖 [README.md](../README.md) - Comprendre le système
2. 🔧 [INSTALLATION.md](INSTALLATION.md) - Installer étape par étape
3. 👤 [GUIDE_UTILISATEUR.md](GUIDE_UTILISATEUR.md) - Créer ma première balise
4. 🎤 [voix-disponibles.md](voix-disponibles.md) - Choisir la meilleure voix

### Je configure mes annonces

1. 📝 [variables-template.md](variables-template.md) - Comprendre les variables
2. 👤 [GUIDE_UTILISATEUR.md](GUIDE_UTILISATEUR.md) - Section "Créer une balise"
3. 🎤 [voix-disponibles.md](voix-disponibles.md) - Choisir ou changer de voix

### J'ai un problème

1. ❓ [FAQ.md](FAQ.md) - Consulter les solutions courantes
2. 📖 [README.md](../README.md) - Section "Résoudre un problème"
3. 🔧 [INSTALLATION.md](INSTALLATION.md) - Section "Dépannage"

### Je veux contribuer au code

1. 💻 [CONTRIBUTING.md](../CONTRIBUTING.md) - Lire le guide développeur
2. 📋 [CHANGELOG.md](../CHANGELOG.md) - Voir l'état actuel du projet
3. 🤖 [.github/copilot-instructions.md](../.github/copilot-instructions.md) - Comprendre l'architecture

## 📋 Contenu par document

### README.md
- Vue d'ensemble du projet
- Caractéristiques principales
- Prérequis matériel et logiciel
- Installation rapide
- Architecture système
- Gestion quotidienne
- Sécurité fail-safe
- Sources météo supportées

### INSTALLATION.md
- Liste complète du matériel nécessaire
- Schémas de câblage PTT (relais et transistor)
- Identification des broches GPIO
- Installation logicielle pas-à-pas
- Configuration initiale via interface web
- Vérifications post-installation
- Dépannage installation
- Mises à jour futures

### GUIDE_UTILISATEUR.md
- Accès à l'interface web
- Tour complet de l'interface
- Créer et gérer des balises
- Comprendre les statuts d'émission
- Consulter l'historique
- Configuration système
- Maintenance courante
- Sauvegardes

### FAQ.md
- **Installation** : Matériel, compatibilités, durée
- **Câblage** : PTT, GPIO, radios compatibles
- **Réseau** : Accès local/distant, sécurité
- **Voix** : Choix, installation, personnalisation
- **Sources météo** : FFVL vs Pioupiou, clés API
- **Fonctionnement** : Planification, collisions
- **Problèmes** : Interface, annonces, audio, PTT
- **Sécurité** : Légalité, piratage, fail-safe
- **Maintenance** : Sauvegardes, mises à jour, optimisations

### voix-disponibles.md
- Guide de sélection de voix
- Tableau comparatif des 6 voix
- Recommandations selon Raspberry Pi
- Tester les voix
- Comparaison Medium vs Low
- Ajouter d'autres voix françaises
- Dépannage audio
- Astuces cache et performances

### variables-template.md
- Principe des templates
- Liste complète des variables
- 5 exemples de templates prêts à l'emploi
- Guide de création de template personnalisé
- Erreurs courantes à éviter
- Astuces de personnalisation
- Exemples par activité (parapente, kitesurf, planeur)

### personnalisation-prononciation.md
- Pourquoi personnaliser
- Prononciations actuelles optimisées
- Guide de modification (avancé)
- Exemples de personnalisations
- Tests de prononciation
- Retour aux valeurs par défaut

### CONTRIBUTING.md
- Configuration environnement de développement
- Architecture du code
- Règles de développement (fail-safe, tests, etc.)
- Ajouter un provider ou moteur TTS
- Conventions de code
- Debug courant
- Checklist avant Pull Request

### CHANGELOG.md
- Historique complet des modifications
- Fonctionnalités implémentées
- Améliorations de sécurité
- Roadmap des versions futures

## 🔍 Recherche rapide

**Vous cherchez à...**

| Besoin | Document | Section |
|--------|----------|---------|
| ...installer le système | INSTALLATION.md | Tout le document |
| ...créer une balise | GUIDE_UTILISATEUR.md | "Créer une nouvelle balise" |
| ...changer de voix | voix-disponibles.md | "Guide de sélection rapide" |
| ...personnaliser les annonces | variables-template.md | "Créer son propre template" |
| ...résoudre un bug | FAQ.md | "Problèmes courants" |
| ...câbler le PTT | INSTALLATION.md | "Câblage du PTT" |
| ...activer/désactiver émissions | GUIDE_UTILISATEUR.md | "Configuration → Paramètres système" |
| ...sauvegarder la config | GUIDE_UTILISATEUR.md | "Maintenance courante" |
| ...contribuer au code | CONTRIBUTING.md | Tout le document |

## 📞 Besoin d'aide supplémentaire ?

1. **Consultez d'abord la FAQ** : [FAQ.md](FAQ.md)
2. **Cherchez dans les issues GitHub** : Quelqu'un a peut-être eu le même problème
3. **Créez une nouvelle issue** : Décrivez votre problème avec logs et contexte
4. **Consultez les logs** : 
   ```bash
   sudo journalctl -u vhf-balise-runner -f
   sudo journalctl -u vhf-balise-web -f
   ```

## 🎓 Parcours d'apprentissage recommandé

### Niveau débutant (je découvre)
1. [README.md](../README.md) - 10 min
2. [GUIDE_UTILISATEUR.md](GUIDE_UTILISATEUR.md) - 30 min
3. [FAQ.md](FAQ.md) - Parcourir les questions - 15 min

### Niveau utilisateur (j'installe)
1. [INSTALLATION.md](INSTALLATION.md) - 1-2h en pratiquant
2. [voix-disponibles.md](voix-disponibles.md) - 15 min
3. [variables-template.md](variables-template.md) - 20 min

### Niveau avancé (je personnalise)
1. [personnalisation-prononciation.md](personnalisation-prononciation.md) - 30 min
2. [CONTRIBUTING.md](../CONTRIBUTING.md) - 45 min
3. [.github/copilot-instructions.md](../.github/copilot-instructions.md) - 1h

## 🗂️ Organisation des fichiers

```
Passerelle VHF/
│
├── README.md                    ← Commencez ici !
├── CHANGELOG.md                 ← Historique du projet
├── CONTRIBUTING.md              ← Pour développeurs
│
├── docs/                        ← Documentation utilisateur
│   ├── INDEX.md                 ← Ce fichier !
│   ├── INSTALLATION.md          ← Guide installation complet
│   ├── GUIDE_UTILISATEUR.md     ← Utilisation quotidienne
│   ├── FAQ.md                   ← Questions fréquentes
│   ├── voix-disponibles.md      ← Guide des voix
│   ├── variables-template.md    ← Personnaliser annonces
│   └── personnalisation-prononciation.md  ← Avancé
│
└── .github/
    └── copilot-instructions.md  ← Guide technique IA/dev
```

---

**🎯 Bonne lecture et bon déploiement !**  
La documentation est là pour vous guider à chaque étape. N'hésitez pas à la consulter régulièrement.

💡 **Astuce** : Créez des favoris vers les documents que vous consultez le plus souvent !
