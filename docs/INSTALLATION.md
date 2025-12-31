# Guide d'installation détaillé - Passerelle VHF

Ce guide vous accompagne pas-à-pas pour installer votre passerelle VHF sur un Raspberry Pi.

## 📦 Matériel nécessaire

### Liste de courses

| Élément | Spécifications | Prix indicatif | Où acheter |
|---------|---------------|----------------|------------|
| **Raspberry Pi** | Pi 3B+ ou Pi 4 (2 Go RAM min, 4 Go recommandés) | 40-60 € | Kubii, Amazon, RS Components |
| **Carte microSD** | 16 Go minimum, Classe 10 | 10-15 € | Tout revendeur informatique |
| **Alimentation** | 5V 3A USB-C (Pi 4) ou micro-USB (Pi 3) | 10 € | Avec le Raspberry Pi |
| **Boîtier** | Optionnel mais recommandé | 5-10 € | Avec le Raspberry Pi |
| **Câbles de connexion** | Câbles Dupont femelle-femelle pour GPIO | 5 € | Amazon, AliExpress |
| **Radio VHF** | Compatible PTT externe (voir ci-dessous) | Variable | Selon votre équipement |

💰 **Budget total** : 70-100 € (hors radio VHF)

### Radios VHF compatibles

Le système peut contrôler quasiment toute radio VHF disposant d'une entrée PTT externe. Exemples :

- **Yaesu FT-60R** : Prise micro externe avec PTT (câble CT-44)
- **Baofeng UV-5R** : Connecteur Kenwood (câble PTT standard)
- **Icom IC-V80** : Connecteur micro/PTT 2,5mm + 3,5mm
- **Motorola GP340** : Connecteur audio externe

💡 **Important** : Vérifiez que votre radio possède bien un connecteur PTT accessible (souvent sur prise micro externe).

## 🔌 Câblage du PTT

### Schéma de principe

Le système contrôle la radio en "court-circuitant" le signal PTT via un relais ou transistor. Voici le schéma le plus simple :

```
Raspberry Pi GPIO 17 ──┐
                       │
                    [Transistor]
                       │
Radio PTT ─────────────┴───── Masse radio
```

### Option 1 : Module relais (recommandé pour débutants)

**Matériel** : Module relais 5V (2-3 €)

**Câblage** :
```
Raspberry Pi                Module Relais              Radio
┌──────────┐               ┌───────────┐             ┌──────┐
│ Pin 11   ├───────────────┤ IN        │             │ PTT  │
│ (GPIO17) │               │           │             │      │
│          │               │  NO ──────┼─────────────┤      │
│ Pin 2    ├───────────────┤ VCC       │             │      │
│ (5V)     │               │           │             │      │
│          │               │  COM ─────┼─────────────┤ GND  │
│ Pin 6    ├───────────────┤ GND       │             │      │
│ (GND)    │               └───────────┘             └──────┘
└──────────┘
```

**Avantages** : Isolation galvanique, facile à câbler, robuste  
**Inconvénients** : Légèrement plus cher, prend un peu de place

### Option 2 : Transistor NPN (pour utilisateurs avancés)

**Matériel** : Transistor 2N2222 ou BC547 + résistance 1kΩ

**Schéma** :
```
GPIO17 ────[1kΩ]───── Base (B)
                        │
                      [NPN]
                        │
PTT radio ───────────── Collecteur (C)
                        │
GND Pi ────────────────  Émetteur (E) ── GND Radio
```

### Identification des broches GPIO Raspberry Pi

```
      3.3V  (1)  (2)  5V ← Alimentation relais
     GPIO2  (3)  (4)  5V
     GPIO3  (5)  (6)  GND ← Masse commune
     GPIO4  (7)  (8)  GPIO14
       GND  (9) (10)  GPIO15
    GPIO17 (11) (12)  GPIO18 ← Pin par défaut PTT
   GPIO27  (13) (14)  GND
    GPIO22 (15) (16)  GPIO23
      3.3V (17) (18)  GPIO24
  ...
```

💡 **Pin par défaut** : GPIO 17 (broche physique #11)  
Vous pouvez changer ce numéro dans l'interface web (Paramètres système).

## 💻 Installation logicielle

### Étape 1 : Préparer la carte SD

1. **Télécharger Raspberry Pi OS** :
   - Allez sur [raspberrypi.com/software](https://www.raspberrypi.com/software/)
   - Téléchargez **Raspberry Pi Imager**

2. **Flasher la carte SD** :
   - Lancez Raspberry Pi Imager
   - Choisissez "Raspberry Pi OS (64-bit)" ou "Lite" si pas besoin d'interface graphique
   - Sélectionnez votre carte SD
   - **⚙️ Paramètres avancés** (icône roue dentée) :
     - ✅ Activer SSH
     - ✅ Configurer le WiFi (SSID et mot de passe)
     - ✅ Définir nom d'hôte : `vhf-balise`
     - ✅ Définir utilisateur et mot de passe
   - Cliquez sur "Écrire"

3. **Premier démarrage** :
   - Insérez la carte SD dans le Raspberry Pi
   - Branchez l'alimentation
   - Attendez 1-2 minutes le démarrage

### Étape 2 : Connexion SSH

Depuis votre ordinateur (Linux/Mac/Windows PowerShell) :

```bash
# Se connecter au Raspberry Pi
ssh pi@vhf-balise.local
# ou
ssh pi@<adresse-ip>

# Mot de passe : celui défini dans Raspberry Pi Imager
```

💡 **Trouver l'IP** : Si `.local` ne fonctionne pas, trouvez l'IP via votre box Internet ou avec :
```bash
# Sur le Raspberry Pi directement (clavier/écran)
hostname -I
```

### Étape 3 : Mise à jour du système

```bash
# Mettre à jour les paquets système
sudo apt update
sudo apt upgrade -y

# Installer les dépendances système
sudo apt install -y git python3-pip python3-venv sqlite3 alsa-utils
```

⏱️ **Durée** : 5-10 minutes selon connexion Internet

### Étape 4 : Téléchargement et installation

```bash
# Télécharger le code
sudo git clone https://github.com/votre-utilisateur/passerelle-vhf.git /opt/vhf-balise

# Aller dans le dossier
cd /opt/vhf-balise

# Rendre le script d'installation exécutable
sudo chmod +x install.sh

# Lancer l'installation
sudo ./install.sh
```

Le script va :
1. ✅ Créer un utilisateur système `vhf-balise`
2. ✅ Installer toutes les dépendances Python
3. ✅ Télécharger les 6 voix françaises (500 Mo, peut prendre 10 min)
4. ✅ Créer la base de données
5. ✅ Configurer les services systemd
6. ✅ Démarrer automatiquement le système

⏱️ **Durée totale** : 10-15 minutes

### Étape 5 : Vérification de l'installation

```bash
# Vérifier que les services sont actifs
sudo systemctl status vhf-balise-web
sudo systemctl status vhf-balise-runner
```

Vous devriez voir :
```
● vhf-balise-web.service - Passerelle VHF - Interface Web
   Loaded: loaded (/etc/systemd/system/vhf-balise-web.service; enabled)
   Active: active (running) since ... ← Doit être vert
```

❌ **Si le service est "failed"** :
```bash
# Voir les erreurs
sudo journalctl -u vhf-balise-web -n 50

# Redémarrer
sudo systemctl restart vhf-balise-web
```

## 🌐 Configuration initiale via l'interface web

### Accéder à l'interface

1. **Trouver l'adresse IP** du Raspberry Pi :
   ```bash
   hostname -I
   # Exemple : 192.168.1.50
   ```

2. **Ouvrir dans un navigateur** :
   ```
   http://192.168.1.50:8000
   ```

3. **Connexion par défaut** :
   - 👤 Utilisateur : `admin`
   - 🔑 Mot de passe : `admin`

### Premier paramétrage

#### 1️⃣ Changer le mot de passe (obligatoire)

Le système vous force à changer le mot de passe par défaut :
- Choisissez un mot de passe fort (min 8 caractères)
- Notez-le dans un endroit sûr !

#### 2️⃣ Configurer le GPIO PTT

Allez dans **⚙️ Configuration → Paramètres système** :

- **Pin GPIO PTT** : `17` (ou le numéro que vous avez câblé)
- **Niveau actif** : `HIGH` (haut) pour la plupart des relais
- **Périphérique audio** : `default` (ou numéro de carte si vous avez une carte son USB)

💡 **Test du PTT** : Le système teste automatiquement le GPIO au démarrage. Consultez les logs :
```bash
sudo journalctl -u vhf-balise-runner -n 20
```

#### 3️⃣ Configurer votre source météo

**Pour les balises FFVL** :

1. Obtenir une clé API auprès de la FFVL
2. Dans l'interface : **⚙️ Configuration → Providers**
3. Entrez votre clé FFVL
4. Sauvegardez

**Pour Pioupiou (OpenWindMap)** :

Rien à configurer ! Le service est public.

#### 4️⃣ Créer votre première balise

1. Allez dans **📡 Balises**
2. Cliquez sur **➕ Nouvelle balise**
3. Remplissez :
   - **Nom** : ex. "Balise Annecy"
   - **URL de la station** : Collez l'URL depuis balisemeteo.com ou openwindmap.org
   - **Template** : Utilisez le template par défaut ou personnalisez
   - **Voix** : Choisissez parmi les 6 voix (recommandé : Siwis Medium)
   - **Période de mesure** : 3600 secondes (1 heure)
   - **Offsets** : `0, 1800` (annonces à :00 et :30)
4. **🎧 Testez l'audio** avant de sauvegarder
5. **✅ Activez la balise** une fois satisfait

#### 5️⃣ Activer les émissions

1. Allez dans **⚙️ Configuration → Paramètres système**
2. ✅ Cochez **"Émissions autorisées"** (master_enabled)
3. Sauvegardez

🎉 **C'est parti !** Le système va maintenant :
- Récupérer les mesures météo toutes les minutes
- Générer les annonces vocales
- Émettre aux horaires programmés

## ✅ Vérifications post-installation

### Test 1 : L'interface web répond

```bash
curl http://localhost:8000
# Doit retourner du HTML
```

### Test 2 : La base de données existe

```bash
ls -lh /opt/vhf-balise/data/vhf-balise.db
# Doit afficher le fichier (quelques Ko)
```

### Test 3 : Les voix sont téléchargées

```bash
ls -lh /opt/vhf-balise/data/tts_models/
# Doit lister 12 fichiers (6 .onnx + 6 .onnx.json)
```

### Test 4 : Le GPIO fonctionne (avec relais branché)

```bash
# Tester manuellement le GPIO
sudo python3 << EOF
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.OUT)
GPIO.output(17, GPIO.HIGH)  # Vous devriez entendre le relais cliquer
import time
time.sleep(2)
GPIO.output(17, GPIO.LOW)
GPIO.cleanup()
EOF
```

## 🆘 Dépannage

### Problème : "Impossible d'accéder à l'interface web"

**Vérifications** :
```bash
# Le service web est-il actif ?
sudo systemctl status vhf-balise-web

# Le port 8000 écoute-t-il ?
sudo netstat -tlnp | grep 8000

# Y a-t-il des erreurs ?
sudo journalctl -u vhf-balise-web -n 50
```

**Solution** : Redémarrer le service
```bash
sudo systemctl restart vhf-balise-web
```

### Problème : "Pas de son audio"

```bash
# Lister les cartes son
aplay -l

# Tester la sortie audio
speaker-test -t wav -c 2

# Vérifier le volume (doit être > 0%)
alsamixer
```

### Problème : "Le PTT ne s'active pas"

1. Vérifier le câblage (multimètre)
2. Tester manuellement le GPIO (script ci-dessus)
3. Vérifier le bon numéro de pin dans l'interface web
4. Consulter les logs :
   ```bash
   sudo journalctl -u vhf-balise-runner -f
   ```

### Problème : "Les mesures météo ne se chargent pas"

```bash
# Vérifier la connexion Internet
ping -c 3 google.com

# Tester l'API Pioupiou
curl http://api.pioupiou.fr/v1/live/385
```

## 🔄 Mises à jour futures

Pour mettre à jour le système vers une nouvelle version :

```bash
cd /opt/vhf-balise

# Sauvegarder la base de données (prudence !)
sudo cp data/vhf-balise.db data/vhf-balise.db.backup

# Récupérer les mises à jour
sudo git pull

# Redémarrer les services
sudo systemctl restart vhf-balise-web
sudo systemctl restart vhf-balise-runner
```

## 📚 Prochaines étapes

✅ Installation terminée !

Consultez maintenant :
- **[GUIDE_UTILISATEUR.md](GUIDE_UTILISATEUR.md)** - Utilisation quotidienne de l'interface
- **[voix-disponibles.md](voix-disponibles.md)** - Choisir et personnaliser les voix
- **[variables-template.md](variables-template.md)** - Personnaliser vos annonces
- **[FAQ.md](FAQ.md)** - Solutions aux problèmes courants

**🚀 Bon vol et bonnes annonces météo !**
