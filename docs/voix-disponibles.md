# Voix françaises disponibles

Le système utilise le moteur TTS **Piper** qui produit une synthèse vocale très naturelle, parfaite pour les annonces météo sur VHF.

## 🎤 Comment choisir sa voix ?

Pour des annonces météo sur radio VHF, privilégiez :
- ✅ **Clarté** : Articulation nette pour une bonne intelligibilité même avec du bruit
- ✅ **Neutralité** : Pas trop rapide, ni trop lente
- ✅ **Naturel** : Éviter les voix trop synthétiques

**🏆 Notre recommandation : Siwis Medium** (voix par défaut)

## 📋 Voix installées (6 voix)

### 🥇 Voix recommandées pour la météo

| Voix | Genre | Qualité | Taille | Caractéristiques | 💬 Exemple d'annonce |
|------|-------|---------|--------|------------------|---------------------|
| **Siwis Medium** ⭐ | Féminine | Excellente | 61 MB | Claire, naturelle, bien articulée | "Balise d'Annecy, Nord-Este, douze kilomètres par heure" |
| **Tom Medium** | Masculine | Excellente | 61 MB | Grave, posée, professionnelle | Voix masculine, idéale si vous préférez |

### 🥈 Voix alternatives

### 🥈 Voix alternatives

| Voix | Genre | Qualité | Taille | Caractéristiques | Quand l'utiliser ? |
|------|-------|---------|--------|------------------|-------------------|
| **MLS Medium** | Féminine | Bonne | 74 MB | Douce, agréable | Si vous trouvez Siwis trop "sèche" |
| **UPMC Medium** | Neutre | Correcte | 15 MB | Voix synthétique standard | Raspberry Pi très limité en espace |
| **Gilles Low** | Masculine | Bonne | 61 MB | Rapide, claire | Performances optimales |
| **Siwis Low** | Féminine | Bonne | 11 MB | Version allégée de Siwis | **La plus légère** - Raspberry Pi limité en RAM |

## 🎯 Guide de sélection rapide

### Selon votre Raspberry Pi

| Modèle Raspberry Pi | Voix recommandée | Pourquoi ? |
|---------------------|------------------|-----------|
| **Pi 4 (4 Go+)** | Siwis Medium ou Tom Medium | Puissance suffisante pour la meilleure qualité |
| **Pi 4 (2 Go)** | Siwis Medium | Bon compromis |
| **Pi 3B+** | Siwis Low ou Gilles Low | Économie de RAM |
| **Pi 3B** | Siwis Low | Version légère recommandée |
| **Pi Zero** | ⚠️ Non recommandé | Trop lent pour la synthèse vocale |

### Selon vos préférences

- **👩 Vous préférez une voix féminine** → Siwis Medium
- **👨 Vous préférez une voix masculine** → Tom Medium
- **🏔️ Environnement bruyant (montagne, vent)** → Siwis ou Tom Medium (meilleure articulation)
- **⚡ Performance max / Raspberry Pi limité** → Siwis Low
- **💾 Espace disque limité** → UPMC Medium (15 MB seulement)

## 🎧 Tester les voix

### Via l'interface web (recommandé)

1. Allez dans **📡 Balises**
2. Créez ou modifiez une balise
3. Changez la voix dans le menu déroulant
4. Cliquez sur **🎧 Écouter le rendu**
5. Comparez plusieurs voix avant de valider

💡 **Conseil** : Testez avec votre texte d'annonce réel pour un résultat représentatif !

### Via l'API (pour utilisateurs avancés)

```bash
curl -X POST http://localhost:8000/api/tts/synthesize \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Balise d'Annecy, Nord-Este, douze kilomètres par heure",
    "voice_id": "fr_FR-siwis-medium"
  }'
```

## 📊 Comparaison détaillée Medium vs Low

| Critère | Medium | Low |
|---------|--------|-----|
| **Qualité audio** | ⭐⭐⭐⭐⭐ Excellente | ⭐⭐⭐⭐ Bonne |
| **Naturel** | Très naturel | Légèrement plus synthétique |
| **Taille fichier** | 60-75 MB | 11-15 MB |
| **Vitesse synthèse (Pi 4)** | ~3 secondes | ~2 secondes |
| **Vitesse synthèse (Pi 3)** | ~6 secondes | ~3 secondes |
| **RAM nécessaire** | ~200 MB | ~100 MB |
| **Usage recommandé** | Production | Raspberry Pi limité / Tests |

💡 **Note** : Les fichiers audio générés sont **mis en cache** ! Après la première synthèse, la lecture est instantanée.

## 🔧 Identifier les voix dans le code

Les voix sont identifiées par leur ID :

| Nom affiché | ID interne (voice_id) |
|-------------|----------------------|
| Siwis Medium | `fr_FR-siwis-medium` |
| Siwis Low | `fr_FR-siwis-low` |
| Tom Medium | `fr_FR-tom-medium` |
| MLS Medium | `fr_FR-mls-medium` |
| Gilles Low | `fr_FR-gilles-low` |
| UPMC Medium | `fr_FR-upmc-medium` |

## ➕ Ajouter d'autres voix françaises

## ➕ Ajouter d'autres voix françaises

Des dizaines de voix supplémentaires sont disponibles gratuitement sur [Piper Voices - Français](https://huggingface.co/rhasspy/piper-voices/tree/main/fr/fr_FR).

### Installation manuelle (méthode simple)

1. **Trouvez une voix** sur le site Hugging Face
   - Exemple : `mls_1840` (voix féminine alternative)

2. **Téléchargez les fichiers** :
   ```bash
   cd /opt/vhf-balise/data/tts_models
   
   # Télécharger le modèle .onnx
   sudo wget https://huggingface.co/rhasspy/piper-voices/resolve/main/fr/fr_FR/mls_1840/low/fr_FR-mls_1840-low.onnx
   
   # Télécharger le fichier de configuration .json
   sudo wget https://huggingface.co/rhasspy/piper-voices/resolve/main/fr/fr_FR/mls_1840/low/fr_FR-mls_1840-low.onnx.json
   ```

3. **Redémarrer le service web** :
   ```bash
   sudo systemctl restart vhf-balise-web
   ```

4. **Vérifier dans l'interface** :
   - La nouvelle voix apparaît dans le menu déroulant !

### Voix supplémentaires recommandées

| Nom | Type | Qualité | Particularité |
|-----|------|---------|---------------|
| `mls_1840` | Féminine | Medium/Low | Voix douce, posée |
| `upmc-pierre` | Masculine | Medium | Voix masculine alternative |
| `siwis-claire` | Féminine | Medium | Variante de Siwis |

💡 **Conseil** : Privilégiez les versions "low" si vous avez un Raspberry Pi 3B ou antérieur.

## 🐛 Dépannage

### "La voix est hachée ou saccadée"

**Causes possibles** :
- Raspberry Pi surchargé
- Modèle trop lourd pour votre Pi
- Problème de carte son

**Solutions** :
1. Passer à une voix "Low" (plus légère)
2. Fermer les processus inutiles
3. Vérifier l'utilisation CPU : `top`

### "La voix ne se télécharge pas"

**Vérifications** :
```bash
# Connexion Internet ?
ping google.com

# Espace disque suffisant ?
df -h /opt/vhf-balise

# Droits d'accès ?
ls -lh /opt/vhf-balise/data/tts_models/
```

### "La voix n'apparaît pas dans le menu"

Après ajout manuel d'une voix :

1. Vérifier que les 2 fichiers sont présents (.onnx + .onnx.json)
2. Redémarrer le service : `sudo systemctl restart vhf-balise-web`
3. Vider le cache du navigateur (Ctrl+F5)

## 📚 Ressources

- **Catalogue complet** : [Piper Voices sur Hugging Face](https://huggingface.co/rhasspy/piper-voices/tree/main/fr)
- **Documentation Piper** : [GitHub Piper TTS](https://github.com/rhasspy/piper)
- **Exemples audio** : Consultez les samples sur le site Piper

## 💡 Astuces

### Cache audio = Performances optimales

Une fois qu'une annonce a été générée, le fichier audio est **mis en cache**.

**Exemple** :
- 1ère fois : "Balise d'Annecy, 12 km/h" → Synthèse 3-5 secondes
- 2ème fois (même texte) → Lecture instantanée du cache

**Avantage** : Après quelques jours, la plupart des annonces sont en cache !

### Nettoyer le cache (si besoin d'espace disque)

```bash
# Voir la taille du cache
du -sh /opt/vhf-balise/data/audio_cache

# Nettoyer (les fichiers seront régénérés au besoin)
sudo rm -rf /opt/vhf-balise/data/audio_cache/*
```

### Personnaliser la prononciation

Si certains mots sont mal prononcés, vous pouvez :
- Modifier l'orthographe dans le template (ex: "Este" au lieu de "Est")
- Voir [personnalisation-prononciation.md](personnalisation-prononciation.md) pour plus de détails

---

**🎤 Bon choix de voix !**  
Pour toute question, consultez la [FAQ](FAQ.md).
