# Guide utilisateur - Passerelle VHF

Bienvenue ! Ce guide vous explique comment utiliser au quotidien votre passerelle VHF pour diffuser automatiquement les mesures météo.

## 📱 Accéder à l'interface web

1. Ouvrez votre navigateur (Chrome, Firefox, Safari, Edge...)
2. Entrez l'adresse : `http://<ip-raspberry>:8000`
3. Connectez-vous avec vos identifiants

💡 **Conseil** : Créez un favori/marque-page dans votre navigateur pour y accéder rapidement !

## 🗺️ Vue d'ensemble de l'interface

L'interface est organisée en plusieurs sections accessibles via le menu latéral :

| Menu | Description |
|------|-------------|
| **📊 Tableau de bord** | Vue d'ensemble du système (statut, prochaines annonces) |
| **📡 Balises** | Gérer vos balises météo (créer, modifier, activer/désactiver) |
| **📋 Historique** | Consulter l'historique des émissions passées |
| **⚙️ Configuration** | Paramètres système, providers, utilisateurs |

## 📊 Tableau de bord

### Vue d'ensemble

Le tableau de bord affiche :
- ✅/❌ **Statut système** : Émissions autorisées ou bloquées
- 📡 **Balises actives** : Nombre de balises en fonctionnement
- 📝 **Dernières émissions** : Liste des 10 dernières annonces
- ⏰ **Prochaines annonces** : Ce qui va être diffusé prochainement

### Interpréter les statuts

| Statut | Signification | Action |
|--------|--------------|--------|
| 🟢 **SENT** (Envoyé) | Émission réussie | ✅ Rien à faire |
| 🔴 **FAILED** (Échoué) | Erreur lors de l'émission | ⚠️ Vérifier les logs |
| 🟡 **PENDING** (En attente) | Planifié mais pas encore émis | ⏳ Normal |
| ⚫ **ABORTED** (Annulé) | Annulé (mesure périmée ou erreur) | 💡 Vérifier configuration |

## 📡 Gestion des balises

### Créer une nouvelle balise

1. Allez dans **📡 Balises**
2. Cliquez sur **➕ Nouvelle balise**
3. Remplissez le formulaire :

#### Informations de base

- **Nom de la balise** : Un nom explicite (ex: "Balise Annecy", "Pioupiou Millau")
  
- **URL de la station** : Collez l'URL complète de la balise depuis :
  - FFVL : `https://www.balisemeteo.com/balise.php?idBalise=67`
  - Pioupiou : `https://www.openwindmap.org/pioupiou-385`
  
  💡 Le système détecte automatiquement le provider et l'ID !

#### Template d'annonce

Le template définit ce qui sera dit. Variables disponibles :

```
Balise de {station_name}, {wind_direction_name}, 
{wind_avg_kmh} kilomètres par heure, 
rafales à {wind_max_kmh}, 
il y a {measurement_age_minutes} minutes.
```

Résultat vocal :
> "Balise de Annecy, Nord-Est, 12 kilomètres par heure, rafales à 18, il y a 5 minutes."

📖 Voir [variables-template.md](variables-template.md) pour toutes les variables disponibles.

#### Choix de la voix

6 voix françaises disponibles :

| Voix | Type | Qualité | Recommandation |
|------|------|---------|----------------|
| **Siwis Medium** ⭐ | Féminine | Excellente | **Par défaut - recommandée** |
| **Siwis Low** | Féminine | Bonne | Pour Raspberry Pi limité |
| **Tom Medium** | Masculine | Excellente | Alternative masculine |
| **MLS Medium** | Féminine | Bonne | Voix douce |
| **Gilles Low** | Masculine | Bonne | Rapide et légère |
| **UPMC Medium** | Neutre | Correcte | Voix standard |

💡 **Testez avant de sauvegarder** : Cliquez sur **🎧 Écouter le rendu** pour pré-écouter !

#### Planification

- **Période de mesure** : Durée de validité des mesures (par défaut 3600 s = 1 heure)
  
- **Décalages horaires (offsets)** : Moments d'annonce dans la période
  - `0` = À l'heure pile (:00)
  - `1800` = À la demi-heure (:30)
  - `0, 900, 1800, 2700` = Toutes les 15 minutes (:00, :15, :30, :45)

**Exemple** : Avec période 3600s et offsets `0, 1800`
- 10:00 → annonce
- 10:30 → annonce
- 11:00 → annonce
- 11:30 → annonce
- ...

- **Intervalle minimum entre TX** : Temps minimum entre deux annonces (par défaut 600 s = 10 min)

#### Paramètres audio

- **Délai avant audio (lead)** : Silence après activation PTT (défaut 500 ms)
- **Délai après audio (tail)** : Silence avant désactivation PTT (défaut 500 ms)

💡 Ces délais permettent à la radio de s'activer complètement avant de parler.

#### Activation

- **☑️ Balise activée** : Cochez pour que la balise commence à émettre

4. **Sauvegardez** 🎉

### Modifier une balise existante

1. Dans **📡 Balises**, cliquez sur le nom de la balise
2. Modifiez les champs souhaités
3. **🎧 Testez à nouveau** si vous avez changé le template ou la voix
4. Sauvegardez

### Désactiver temporairement une balise

Plutôt que de supprimer une balise, vous pouvez la désactiver :

1. Cliquez sur la balise
2. Décochez **☑️ Balise activée**
3. Sauvegardez

La balise reste configurée mais n'émet plus. Vous pouvez la réactiver à tout moment.

### Supprimer une balise

⚠️ **Attention** : Cette action est irréversible !

1. Cliquez sur la balise
2. En bas de page : **🗑️ Supprimer cette balise**
3. Confirmez

## 📋 Historique des émissions

### Consulter l'historique

1. Allez dans **📋 Historique**
2. Vous voyez toutes les émissions (succès et échecs)

### Filtrer l'historique

- **Par balise** : Sélectionnez une balise dans le menu déroulant
- **Par statut** : SENT, FAILED, PENDING, ABORTED
- **Par date** : Les plus récentes en premier

### Comprendre une erreur

Si vous voyez une émission **FAILED** ou **ABORTED** :

1. Cliquez sur la ligne pour voir les détails
2. Regardez le champ **"Message d'erreur"**

**Erreurs courantes** :

| Message d'erreur | Cause probable | Solution |
|-----------------|----------------|----------|
| "Measurement expired" | Mesure trop ancienne | Vérifier connexion Internet, station météo en ligne ? |
| "PTT error" | Problème PTT/radio | Vérifier câblage GPIO, radio allumée ? |
| "Audio file not found" | Fichier audio manquant | Régénérer le cache audio |
| "Provider error" | Erreur récupération météo | Vérifier clé API, station existe toujours ? |

## ⚙️ Configuration

### Paramètres système

**⚙️ Configuration → Paramètres système**

#### Émissions autorisées (master_enabled)

**🔴 DÉSACTIVÉ** = Aucune émission radio (mode silence total)  
**🟢 ACTIVÉ** = Les annonces sont diffusées normalement

💡 **Utilisez ce bouton** pour couper rapidement toutes les émissions sans désactiver les balises une par une.

#### Configuration GPIO PTT

- **Pin GPIO** : Numéro du pin utilisé (défaut 17)
- **Niveau actif** : HIGH (haut) ou LOW (bas) selon votre relais

#### Périphérique audio

- **Nom du périphérique** : `default` pour la sortie par défaut
- Ou numéro de carte si vous utilisez une carte son USB (ex: `hw:1,0`)

💡 Pour lister les périphériques :
```bash
aplay -l
```

#### Pause entre annonces

Quand plusieurs annonces sont dues en même temps, combien de temps attendre entre chaque ?
- Défaut : 10 secondes
- Évite l'enchaînement trop rapide d'annonces

### Configuration des providers

**⚙️ Configuration → Providers**

#### FFVL

Si vous utilisez des balises FFVL, vous devez entrer votre clé API :

1. Obtenez une clé auprès de la FFVL (gratuite)
2. Entrez-la dans le champ **"Clé API FFVL"**
3. Sauvegardez

#### OpenWindMap / Pioupiou

Aucune configuration nécessaire ! Le service est public et gratuit.

### Gérer les utilisateurs

**⚙️ Configuration → Administration → Utilisateurs**

#### Changer votre mot de passe

1. Menu utilisateur (en haut à droite) → **Changer mot de passe**
2. Entrez l'ancien puis le nouveau (2 fois)
3. Sauvegardez

#### Créer un nouvel utilisateur (admin uniquement)

1. Allez dans **Administration → Utilisateurs**
2. **➕ Nouvel utilisateur**
3. Définissez nom d'utilisateur et mot de passe temporaire
4. ☑️ "Doit changer le mot de passe" : l'utilisateur devra choisir son propre mot de passe à la première connexion

## 🔧 Maintenance courante

### Surveiller le système

**Quotidien** :
- Vérifier le tableau de bord
- Surveiller les statuts des dernières émissions

**Hebdomadaire** :
- Consulter l'historique pour détecter des anomalies
- Vérifier que les mesures météo se mettent à jour

**Mensuel** :
- Vérifier l'espace disque : `df -h /opt/vhf-balise`
- Nettoyer l'historique si nécessaire (très vieilles entrées)

### Redémarrer le système

Si quelque chose ne fonctionne pas bien :

```bash
# Via SSH
sudo systemctl restart vhf-balise-web
sudo systemctl restart vhf-balise-runner
```

Ou redémarrez complètement le Raspberry Pi :
```bash
sudo reboot
```

### Sauvegarder la configuration

Votre configuration est dans la base de données. Pour la sauvegarder :

```bash
# Créer une sauvegarde
sudo cp /opt/vhf-balise/data/vhf-balise.db /opt/vhf-balise/data/vhf-balise.db.backup-$(date +%Y%m%d)

# Ou télécharger via SCP depuis votre ordinateur
scp pi@vhf-balise.local:/opt/vhf-balise/data/vhf-balise.db ./sauvegarde-vhf.db
```

### Restaurer une sauvegarde

```bash
# Arrêter les services
sudo systemctl stop vhf-balise-web vhf-balise-runner

# Restaurer
sudo cp /opt/vhf-balise/data/vhf-balise.db.backup /opt/vhf-balise/data/vhf-balise.db

# Redémarrer
sudo systemctl start vhf-balise-web vhf-balise-runner
```

## 🎓 Cas d'usage avancés

### Plusieurs balises sur différentes fréquences

Vous gérez plusieurs sites ? Configurez plusieurs balises :
- Balise 1 : Annecy (FFVL ID 67) → Radio 1 sur 143.9625 MHz
- Balise 2 : Millau (Pioupiou 385) → Radio 2 sur 143.8875 MHz

**Important** : Un seul Raspberry Pi = Une seule radio à la fois !  
Pour émettre sur plusieurs fréquences, il faut :
- Soit basculer manuellement de radio
- Soit installer plusieurs Raspberry Pi

### Annonces multi-langues

Actuellement, seul le français est supporté. Pour d'autres langues, il faudrait :
- Ajouter des modèles Piper dans d'autres langues
- Adapter les templates

### Mode maintenance (sans radio)

Pour tester le système sans radio branchée :

1. **⚙️ Configuration → Paramètres système**
2. **🔴 Désactiver "Émissions autorisées"**
3. Vous pouvez quand même :
   - Créer et configurer des balises
   - Tester les annonces avec **🎧 Écouter le rendu**
   - Consulter l'historique

## ❓ Besoin d'aide ?

- 📖 **[FAQ](FAQ.md)** - Questions fréquentes
- 🔧 **[INSTALLATION.md](INSTALLATION.md)** - Problèmes matériels/installation
- 🎤 **[voix-disponibles.md](voix-disponibles.md)** - Personnaliser les voix
- 📝 **[variables-template.md](variables-template.md)** - Personnaliser les annonces

**Bonne utilisation ! 🚀**
