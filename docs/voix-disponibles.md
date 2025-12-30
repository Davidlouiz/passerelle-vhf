# Voix françaises disponibles

Le système utilise le moteur TTS **Piper** avec plusieurs voix françaises de qualité.

## Voix installées (6)

### Qualité Medium (meilleure qualité, fichiers plus volumineux)

| Voix | Type | Caractéristiques | Taille | Usage recommandé |
|------|------|------------------|--------|------------------|
| **Siwis** | Féminine | Claire, naturelle, bien articulée | 61 MB | **Recommandée** - Excellente pour les annonces météo |
| **Tom** | Masculine | Grave, posée, professionnelle | 61 MB | Alternative masculine claire |
| **UPMC** | Neutre | Voix synthétique standard | 15 MB | Usage général, légère |
| **MLS** | Féminine | Douce, agréable | 74 MB | Voix féminine alternative |

### Qualité Low (plus rapide, fichiers plus légers)

| Voix | Type | Caractéristiques | Taille | Usage recommandé |
|------|------|------------------|--------|------------------|
| **Gilles** | Masculine | Rapide, claire | 61 MB | Performances optimales |
| **Siwis Low** | Féminine | Version allégée de Siwis | 11 MB | **La plus légère** - idéale pour Raspberry Pi limité |

## Comparaison Medium vs Low

- **Medium** : Meilleure qualité audio, plus naturel, mais synthèse légèrement plus lente
- **Low** : Synthèse plus rapide, fichiers plus légers, qualité correcte pour des annonces

## Recommandation pour balises VHF

Pour des annonces vocales de vent sur VHF, nous recommandons :

1. **Siwis Medium** (par défaut) - Excellent compromis qualité/performance
2. **Siwis Low** - Si le Raspberry Pi est limité en ressources
3. **Tom Medium** - Pour une voix masculine

## Ajouter d'autres voix

Pour ajouter une nouvelle voix française depuis [Piper Voices](https://huggingface.co/rhasspy/piper-voices/tree/main/fr/fr_FR) :

```bash
cd /opt/vhf-balise/data/tts_models

# Télécharger le modèle (exemple avec la voix "mls_1840")
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/fr/fr_FR/mls_1840/low/fr_FR-mls_1840-low.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/fr/fr_FR/mls_1840/low/fr_FR-mls_1840-low.onnx.json

# Redémarrer le service
sudo systemctl restart vhf-balise-web
```

Puis mettre à jour `app/tts/piper_engine.py` pour ajouter la voix dans `known_voices`.
