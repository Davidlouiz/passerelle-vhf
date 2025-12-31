# FAQ - Questions fréquentes

## 🚀 Installation et démarrage

### Q: De quel matériel ai-je besoin exactement ?

**R:** Matériel minimum :
- Raspberry Pi 3B+ ou 4 (2 Go RAM minimum)
- Carte microSD 16 Go
- Alimentation 5V 3A
- Radio VHF avec entrée PTT externe
- Câbles pour connecter GPIO → PTT (relais 5V ou transistor)
- Connexion Internet (Ethernet ou WiFi)

Budget total : ~70-100 € (hors radio VHF).

Voir [INSTALLATION.md](INSTALLATION.md) pour les détails complets.

### Q: Mon Raspberry Pi Zero fonctionne-t-il ?

**R:** Théoriquement oui, mais **non recommandé** :
- Le Pi Zero est très lent pour la synthèse vocale
- Risque de délais et timeouts
- Utilisez au minimum un Raspberry Pi 3B+

### Q: Puis-je installer sur un PC Linux au lieu d'un Raspberry Pi ?

**R:** Oui pour le développement et les tests, mais :
- ✅ Fonctionne parfaitement pour tester l'interface
- ⚠️ Le contrôle PTT GPIO ne fonctionnera pas (mode mock uniquement)
- ⚠️ Pas pratique en production (PC allumé 24/7)

Pour un usage réel, le Raspberry Pi est la meilleure option.

### Q: Combien de temps prend l'installation ?

**R:**
- Préparation carte SD : 10 min
- Installation logicielle : 10-15 min
- Configuration initiale : 10-20 min
- Câblage PTT : 15-30 min selon expérience

**Total : 45-75 minutes** pour une installation complète.

## 🔌 Câblage et matériel

### Q: Quel type de relais utiliser pour le PTT ?

**R:** Module relais 5V simple contact (2-3 €) :
- Marques courantes : SainSmart, Elegoo, HiLetgo
- Spécifications : 5V, 10A (largement suffisant)
- **Recommandé** : Module avec LED indicatrice

Alternative : Transistor NPN (2N2222, BC547) si vous êtes à l'aise avec l'électronique.

### Q: Sur quel GPIO brancher le PTT ?

**R:** Par défaut **GPIO 17** (broche physique #11), mais vous pouvez utiliser :
- N'importe quel GPIO libre (0-27)
- Évitez les GPIO avec fonctions spéciales (I2C, SPI, UART)
- Configurez le numéro dans l'interface web

💡 **Conseil** : Restez sur GPIO 17 si vous débutez, c'est testé et documenté.

### Q: Ma radio VHF est-elle compatible ?

**R:** Si votre radio a une **prise micro externe avec PTT**, oui !

**Compatible** :
- ✅ Yaesu FT-60R, VX-6R, VX-7R
- ✅ Baofeng UV-5R, UV-82
- ✅ Icom IC-V80, IC-V85
- ✅ Motorola GP340, GP380
- ✅ La plupart des radios portables VHF/UHF

**Comment vérifier** : Cherchez "PTT cable" ou "speaker mic connector" pour votre modèle.

### Q: Comment identifier les fils PTT et masse sur ma radio ?

**R:** 
1. Cherchez le schéma de votre connecteur (Google : "radio_model PTT pinout")
2. Utilisez un multimètre en mode continuité
3. Testez avec le micro d'origine : quel fil s'active quand vous appuyez sur PTT ?

**Exemple Baofeng UV-5R** (connecteur Kenwood) :
- Pointe = Audio
- Anneau 1 = Masse
- Anneau 2 = PTT
- Base = Micro

### Q: Puis-je utiliser plusieurs radios en même temps ?

**R:** Non, un Raspberry Pi = un PTT = une radio à la fois.

Pour plusieurs fréquences simultanées :
- Installer plusieurs Raspberry Pi
- OU basculer manuellement de radio (pas pratique)
- OU utiliser un relais multivoies (configuration avancée)

## 🌐 Connexion et réseau

### Q: Dois-je ouvrir des ports sur ma box Internet ?

**R:** **Non**, sauf si vous voulez accéder à distance :
- En local (réseau domestique) : Rien à faire, ça marche directement
- Depuis Internet : Il faut un VPN (recommandé) ou redirection de port (déconseillé pour la sécurité)

### Q: Comment accéder à l'interface depuis mon téléphone ?

**R:** Sur le même réseau WiFi :
1. Trouvez l'IP du Raspberry : `hostname -I`
2. Sur votre téléphone, ouvrez le navigateur
3. Allez sur `http://192.168.1.XX:8000`

💡 Créez un favori/marque-page pour y accéder facilement !

### Q: Le Raspberry Pi doit-il être connecté en permanence à Internet ?

**R:** **Oui** pour récupérer les mesures météo.

- Internet nécessaire toutes les 1-5 minutes (très peu de bande passante)
- Si coupure Internet : Les annonces s'arrêtent automatiquement (fail-safe)
- Quand Internet revient : Les annonces reprennent

## 🎤 Voix et annonces

### Q: Quelle voix choisir pour des annonces météo ?

**R:** **Siwis Medium** (voix par défaut) est la meilleure :
- Féminine, claire, bien articulée
- Parfaite intelligibilité sur VHF
- Bon compromis qualité/performance

Alternatives :
- **Tom Medium** : Voix masculine si vous préférez
- **Siwis Low** : Si votre Raspberry Pi rame (plus légère)

### Q: Les voix sont-elles téléchargées automatiquement ?

**R:** Oui ! Le script `install.sh` télécharge automatiquement les 6 voix françaises (environ 500 Mo).

Elles sont stockées dans `/opt/vhf-balise/data/tts_models/`.

### Q: Puis-je ajouter d'autres voix ?

**R:** Oui, des dizaines de voix françaises sont disponibles :
1. Consultez [Piper Voices](https://huggingface.co/rhasspy/piper-voices/tree/main/fr/fr_FR)
2. Téléchargez les fichiers `.onnx` et `.onnx.json`
3. Placez-les dans `/opt/vhf-balise/data/tts_models/`
4. Redémarrez le service web

Voir [voix-disponibles.md](voix-disponibles.md) pour les détails.

### Q: Comment personnaliser les annonces ?

**R:** Via les **templates** dans la configuration de chaque balise.

Variables disponibles :
- `{station_name}` - Nom de la balise
- `{wind_avg_kmh}` - Vent moyen
- `{wind_max_kmh}` - Rafales
- `{wind_direction_name}` - Direction (Nord, Sud-Est, etc.)
- `{measurement_age_minutes}` - Ancienneté de la mesure

Exemple personnalisé :
```
Attention parapentistes, {station_name}, vent {wind_direction_name} 
à {wind_avg_kmh} kilomètres heure, rafales {wind_max_kmh}.
```

Voir [variables-template.md](variables-template.md) pour toutes les variables.

### Q: Pourquoi "Este" au lieu de "Est" dans les directions ?

**R:** Optimisation phonétique pour le TTS français :
- "Este" se prononce mieux dans "Nord-Este"
- "Oueste" est plus clair que "Ouest"

Ces optimisations améliorent l'intelligibilité sur la radio. Vous pouvez les modifier dans `app/services/template.py` si vous préférez.

## 📡 Sources de données météo

### Q: Quelle est la différence entre FFVL et Pioupiou ?

**R:**

| Critère | FFVL | Pioupiou (OpenWindMap) |
|---------|------|------------------------|
| **Clé API** | Requise (gratuite) | Aucune (public) |
| **Nombre de stations** | ~500 en France | ~1000 en France |
| **Données** | Vent, température, humidité, etc. | Vent principalement |
| **Fiabilité** | Excellente | Très bonne |
| **Communauté** | Vol libre (parapente, delta) | Multisports |

💡 Vous pouvez utiliser **les deux** sur la même installation !

### Q: Comment obtenir une clé API FFVL ?

**R:**
1. Contactez la FFVL via le site [ffvl.fr](https://federation.ffvl.fr/)
2. Expliquez votre usage (balise météo vocale automatisée)
3. La clé est généralement fournie gratuitement sous 48-72h
4. Entrez-la dans ⚙️ Configuration → Providers

### Q: À quelle fréquence les mesures sont-elles mises à jour ?

**R:**
- Le système interroge les providers toutes les **1 minute**
- Les stations météo envoient généralement des mesures toutes les **1-5 minutes**
- Le système vérifie que les mesures ne sont pas périmées (par défaut max 1 heure)

### Q: Que se passe-t-il si une station météo tombe en panne ?

**R:** Sécurité fail-safe :
1. Le système détecte qu'aucune mesure récente n'est disponible
2. Les annonces pour cette balise sont **automatiquement bloquées**
3. Le statut passe à "ABORTED" avec message d'erreur
4. Quand la station revient, les annonces reprennent automatiquement

**Aucune annonce périmée n'est jamais diffusée.**

## ⚙️ Fonctionnement et paramétrage

### Q: Comment fonctionne la planification des annonces ?

**R:** Système d'offsets dans une période :

**Exemple concret** :
- Période de mesure : 3600 s (1 heure)
- Offsets : `0, 1800` (0 s et 1800 s = 30 minutes)

Résultat :
```
10:00 → Annonce (offset 0)
10:30 → Annonce (offset 1800)
11:00 → Annonce (offset 0)
11:30 → Annonce (offset 1800)
...
```

Pour annoncer **toutes les 15 minutes** : `0, 900, 1800, 2700`

### Q: Puis-je avoir des annonces à heures exactes uniquement ?

**R:** Oui !
- Période : 3600 (1 heure)
- Offsets : `0` (uniquement)

Résultat : Annonces à 10:00, 11:00, 12:00, etc.

### Q: Pourquoi y a-t-il un "intervalle minimum entre TX" ?

**R:** Sécurité pour éviter :
- Le spam radio si plusieurs balises émettent en même temps
- L'occupation excessive de la fréquence
- Les problèmes si une mesure arrive en retard

Par défaut 10 minutes = temps raisonnable entre deux annonces.

### Q: Que se passe-t-il si plusieurs balises doivent émettre en même temps ?

**R:** Le système gère intelligemment :
1. Détecte les collisions
2. Mélange l'ordre aléatoirement
3. Émet les annonces **séquentiellement** avec une pause (10 s par défaut)

**Exemple** : 3 balises à 10:00
- 10:00:00 → Balise A
- 10:00:20 → Balise C (ordre aléatoire)
- 10:00:40 → Balise B

### Q: Comment désactiver temporairement toutes les annonces ?

**R:** Deux méthodes :

**Méthode rapide** (tout le système) :
1. ⚙️ Configuration → Paramètres système
2. 🔴 Désactiver "Émissions autorisées"

**Méthode sélective** (balise par balise) :
1. 📡 Balises → Cliquer sur la balise
2. ☐ Décocher "Balise activée"

## 🐛 Problèmes courants

### Q: "Impossible d'accéder à l'interface web"

**R:** Vérifications par ordre :

1. **Le Raspberry Pi est-il allumé ?**
   - Vérifiez les LEDs
   
2. **Est-il sur le même réseau ?**
   ```bash
   ping vhf-balise.local
   # ou
   ping 192.168.1.XX
   ```

3. **Le service web fonctionne-t-il ?**
   ```bash
   sudo systemctl status vhf-balise-web
   ```

4. **Redémarrer les services**
   ```bash
   sudo systemctl restart vhf-balise-web
   ```

### Q: "Les annonces ne partent pas"

**R:** Checklist de dépannage :

1. ✅ **"Émissions autorisées" est activé ?**
   - ⚙️ Configuration → Paramètres système

2. ✅ **La balise est activée ?**
   - 📡 Balises → Vérifier ☑️ "Balise activée"

3. ✅ **Les mesures météo arrivent ?**
   - 📊 Tableau de bord → Vérifier "Dernières mesures"
   - Consulter l'historique pour voir les erreurs

4. ✅ **Le PTT fonctionne ?**
   - Vérifier le câblage
   - Consulter les logs : `sudo journalctl -u vhf-balise-runner -f`

### Q: "J'entends le relais cliquer mais pas d'audio sur la radio"

**R:** Problème de câblage audio :

1. **Tester le son localement**
   ```bash
   speaker-test -t wav -c 2
   ```

2. **Vérifier le volume** (ne doit pas être à 0% !)
   ```bash
   alsamixer
   ```

3. **Vérifier le bon périphérique audio**
   - ⚙️ Configuration → Paramètres système → Périphérique audio
   - Lister les périphériques : `aplay -L`

4. **Câble audio bien branché ?**
   - Sortie jack 3.5mm du Raspberry Pi → Entrée micro de la radio
   - Ou carte son USB → Entrée micro de la radio

### Q: "Erreur 'Measurement expired' dans l'historique"

**R:** La mesure météo est trop ancienne :

**Causes possibles** :
- La station météo est hors ligne
- Connexion Internet du Raspberry Pi coupée
- La période de validité est trop courte

**Solutions** :
1. Vérifier que la station fonctionne (consulter le site web)
2. Vérifier la connexion Internet : `ping google.com`
3. Augmenter la période si nécessaire (⚙️ Balise → Période de mesure)

### Q: "Le système redémarre tout seul"

**R:** Problème d'alimentation :

- **Cause #1** : Alimentation sous-dimensionnée (< 3A)
- **Cause #2** : Câble USB défectueux
- **Cause #3** : Trop de périphériques USB

**Solution** : Utiliser l'alimentation officielle Raspberry Pi (5V 3A).

### Q: "La base de données est verrouillée (database locked)"

**R:** Deux processus tentent d'écrire en même temps :

```bash
# Vérifier les processus
ps aux | grep python

# Redémarrer proprement
sudo systemctl restart vhf-balise-web
sudo systemctl restart vhf-balise-runner
```

Si le problème persiste, rebooter :
```bash
sudo reboot
```

## 🔒 Sécurité et légal

### Q: Est-ce légal d'utiliser ce système ?

**R:** **Ça dépend de votre pays et de votre licence radio !**

**En France** :
- ✅ Légal si vous avez une autorisation d'émission VHF aéronautique
- ✅ Fréquences vol libre : 143.9875 MHz, 143.9625 MHz, etc.
- ⚠️ Respectez les temps d'émission max et les pauses
- ⚠️ Identifiez votre station (indicatif)

**Vérifiez auprès de** :
- Votre fédération (FFVL pour le vol libre en France)
- L'ANFR (Agence Nationale des Fréquences)

**En cas de doute, ne pas émettre !**

### Q: Quelqu'un peut-il pirater mon système ?

**R:** Plusieurs niveaux de sécurité :

1. **Mot de passe obligatoire** pour accéder à l'interface
2. **Pas d'exposition Internet** (sauf si vous configurez un VPN)
3. **Logs complets** de toutes les émissions
4. **Fail-safe** : En cas de problème, le système bloque les émissions

**Recommandations** :
- ✅ Changez le mot de passe admin par défaut
- ✅ N'exposez PAS le port 8000 directement sur Internet
- ✅ Utilisez un VPN (Wireguard, OpenVPN) pour l'accès distant
- ✅ Mettez à jour régulièrement le système

### Q: Que se passe-t-il si un bug provoque des émissions parasites ?

**R:** **Architecture fail-safe** à plusieurs niveaux :

1. ✅ Aucune émission sans journalisation préalable en DB
2. ✅ Aucune émission de mesure périmée (jamais !)
3. ✅ Timeout PTT : 30 secondes max (watchdog)
4. ✅ Bouton d'urgence "Émissions autorisées" (désactive tout)
5. ✅ En cas d'erreur → BLOCAGE, pas d'émission

**C'est le principe "fail-closed"** : En cas de doute, on ne transmet pas.

## 💾 Sauvegarde et maintenance

### Q: Comment sauvegarder ma configuration ?

**R:** La configuration est dans la base de données SQLite :

```bash
# Sauvegarde manuelle
sudo cp /opt/vhf-balise/data/vhf-balise.db \
        /opt/vhf-balise/data/backup-$(date +%Y%m%d).db

# Télécharger sur votre PC
scp pi@vhf-balise.local:/opt/vhf-balise/data/vhf-balise.db \
    ./ma-config-vhf.db
```

**Sauvegardez régulièrement** (au moins une fois par mois).

### Q: Le cache audio prend-il beaucoup de place ?

**R:** Chaque fichier audio fait ~50-200 Ko.

- 100 annonces différentes ≈ 5-20 Mo
- Nettoyage automatique : Pas encore implémenté
- Nettoyage manuel : Vous pouvez supprimer `/opt/vhf-balise/data/audio_cache/*` sans risque (ils seront régénérés)

### Q: Dois-je mettre à jour le système régulièrement ?

**R:** Recommandé tous les 2-3 mois :

```bash
cd /opt/vhf-balise
sudo git pull
sudo systemctl restart vhf-balise-web vhf-balise-runner
```

**Avant la mise à jour** :
```bash
# Sauvegarder la config !
sudo cp data/vhf-balise.db data/vhf-balise.db.backup
```

## 🛠️ Optimisations et astuces

### Q: Comment réduire la latence entre mesure et annonce ?

**R:** Plusieurs paramètres jouent :

1. **Polling provider** : Le système interroge toutes les 60 secondes (fixe)
2. **Synthèse vocale** : ~2-5 secondes (dépend du Raspberry Pi)
3. **Cache TTS** : Réutilise les audios identiques (instantané)

**Astuce** : Le cache TTS accélère énormément les annonces répétées !

### Q: Puis-je utiliser une carte son USB pour meilleure qualité audio ?

**R:** Oui !

1. Branchez la carte son USB
2. Trouvez son identifiant : `aplay -l`
   ```
   card 1: Device [USB Audio Device]
   ```
3. Dans l'interface : ⚙️ Configuration → Paramètres système
4. Périphérique audio : `hw:1,0` (remplacer 1 par le numéro de votre carte)

**Avantage** : Meilleure qualité audio que la sortie jack du Raspberry Pi.

### Q: Comment tester sans émettre sur la vraie fréquence ?

**R:** Plusieurs options :

1. **Désactiver "Émissions autorisées"** + utiliser 🎧 "Écouter le rendu"
2. **Radio sur une fréquence test** (ex: PMR446 ou fréquence libre)
3. **Brancher un récepteur à la place** (pour vérifier le PTT)
4. **Mode développement** sur PC (sans GPIO, mais interface complète)

## 📚 Ressources supplémentaires

### Q: Où trouver de l'aide supplémentaire ?

**R:** Documentation complète :
- 📖 [README.md](../README.md) - Vue d'ensemble
- 🔧 [INSTALLATION.md](INSTALLATION.md) - Installation détaillée
- 👤 [GUIDE_UTILISATEUR.md](GUIDE_UTILISATEUR.md) - Utilisation quotidienne
- 🎤 [voix-disponibles.md](voix-disponibles.md) - Voix françaises
- 📝 [variables-template.md](variables-template.md) - Templates d'annonces
- 💻 [CONTRIBUTING.md](../CONTRIBUTING.md) - Pour développeurs

**Support** :
- Issues GitHub : Signalez bugs et suggestions
- Communauté : Forums vol libre, groupes Telegram/Discord

---

**❓ Votre question n'est pas ici ?** Créez une [issue GitHub](https://github.com/votre-utilisateur/passerelle-vhf/issues) ou consultez les logs pour diagnostiquer :
```bash
sudo journalctl -u vhf-balise-runner -f
```
