# Fanga Intelligent File Classifier

Pipeline intelligente qui classifie, renomme et organise automatiquement des fichiers hétérogènes pour FANGA, une plateforme de mobilité électrique deux-roues en Côte d'Ivoire.

## Architecture

```
fanga_inbox/  -->  Extractor  -->  Classifier (GPT-4o)  -->  Renamer  -->  Organizer  -->  fanga_organised/
                  (métadonnées +   (catégorie +              (nom             (copie/         (trié par
                   contenu)         confiance)                normalisé)       déplacement     catégorie)
                                                                              + notes)
                                                                                          --> rapport_traitement.json
```

**Modules :**

| Module | Responsabilité |
|--------|----------------|
| `src/extractor.py` | Extraction des métadonnées et du contenu lisible de tout type de fichier (PDF, DOCX, XLSX, CSV, images) |
| `src/classifier.py` | Envoi du contenu à GPT-4o et récupération d'une classification structurée (catégorie, confiance, description) |
| `src/renamer.py` | Génération de noms de fichiers normalisés : `YYYY-MM-DD_{catégorie}_{description}.{ext}` |
| `src/organizer.py` | Création de l'arborescence de sortie, copie/déplacement des fichiers, rédaction des notes d'ambiguïté |
| `src/reporter.py` | Génération du rapport de traitement JSON avec statistiques |
| `src/pipeline.py` | Orchestrateur principal qui coordonne tous les modules |
| `src/utils.py` | Constantes partagées, configuration du logging, fonctions utilitaires |

## Choix techniques

- **GPT-4o** : modèle unifié texte + vision, pas besoin d'une API vision séparée. Gère la classification de documents textuels et d'images dans un seul modèle.
- **pdfplumber** plutôt que PyPDF2 : meilleure qualité d'extraction de texte, notamment pour les documents structurés avec des tableaux.
- **Copie par défaut** plutôt que déplacement : opération non-destructive. Les fichiers originaux sont préservés. Utiliser le flag `--move` pour le mode destructif.
- **Un seul appel LLM par fichier** avec sortie JSON structurée : économique en tokens, simple à parser, pas de chaînes multi-étapes.
- **Seuil de confiance** (défaut : 0.70) : les fichiers en dessous de ce seuil sont placés dans `A_verifier/` avec une note compagnon expliquant pourquoi. Cela permet aux humains de revoir les classifications incertaines.

## Stratégie de classification

La classification utilise une approche structurée de prompt engineering :

1. **Rôle système** : le LLM agit comme assistant de classification documentaire pour FANGA, avec le contexte complet sur l'entreprise (motos électriques, Côte d'Ivoire).
2. **Définitions des catégories** : chacune des 8 catégories est accompagnée de descriptions explicites de ce qui y appartient, réduisant l'ambiguïté.
3. **Sortie JSON structurée** : le LLM retourne `category`, `confidence`, `description` et `reasoning` sous forme d'objet JSON. L'utilisation de `response_format: json_object` garantit un JSON valide.
4. **Calibration de la confiance** : le prompt demande explicitement une certitude réelle plutôt que de toujours retourner 0.99.
5. **Support vision** : les fichiers image sont envoyés en base64 avec le même prompt de classification, exploitant les capacités multimodales de GPT-4o.
6. **Fallback** : si le LLM retourne une catégorie invalide ou que le parsing échoue, le fichier est mappé vers "Autre" avec une confiance de 0.0.

## Installation et exécution

```bash
# Cloner le dépôt
git clone https://github.com/username/fanga-file-classifier.git
cd fanga-file-classifier

# Installer les dépendances
pip install -r requirements.txt

# Configurer la clé API
cp .env.example .env
# Éditer .env et ajouter votre OPENAI_API_KEY

# Générer les fichiers mock
python generate_mocks.py

# Lancer la pipeline
python main.py

# Lancer avec des options
python main.py --threshold 0.8 --check-duplicates --dry-run
```

**Arguments CLI :**

| Argument | Défaut | Description |
|----------|--------|-------------|
| `--input` | `./fanga_inbox` | Chemin vers le dossier source |
| `--output` | `./fanga_organised` | Chemin vers le dossier de sortie |
| `--move` | `False` | Déplacer les fichiers au lieu de les copier |
| `--threshold` | `0.70` | Seuil de confiance |
| `--dry-run` | `False` | Mode aperçu, aucune opération sur les fichiers |
| `--check-duplicates` | `False` | Activer la détection de doublons par hash MD5 |

## Améliorations envisagées

- **Système de file de messages** (Redis/RabbitMQ) pour le traitement à haut volume avec des pools de workers.
- **Traitement asynchrone** avec asyncio pour des appels LLM en parallèle sur plusieurs fichiers.
- **Modèle fine-tuné** entraîné sur des classifications validées par des humains pour réduire les coûts API à grande échelle.
- **Interface web human-in-the-loop** pour la revue des fichiers dans `A_verifier/`, avec les corrections réinjectées dans les données d'entraînement.
- **Déclencheurs webhook/S3** pour le traitement automatique à l'arrivée de nouveaux fichiers.
- **Stockage en base de données** (PostgreSQL) pour l'historique des classifications et les analytics, au lieu d'un fichier JSON unique.
- **Couche de cache** (Redis) indexée sur le hash du fichier pour éviter de re-classifier des fichiers identiques.

## Réponse à la question finale

> FANGA prévoit de traiter automatiquement des milliers de fichiers par jour provenant de dizaines d'agences partenaires en Côte d'Ivoire, avec des noms de fichiers parfois incohérents et des formats variés. Comment feriez-vous évoluer votre solution pour répondre à ce volume, garantir la fiabilité de la classification et intégrer une boucle de correction humaine lorsque le modèle se trompe ?

### 1. Scalabilité (Volume)

- Remplacer le scan du filesystem par une file de messages (Redis Queue, Celery, ou RabbitMQ). Chaque nouveau fichier déclenche une tâche.
- Traiter les fichiers de manière asynchrone avec des pools de workers. Plusieurs workers classifient en parallèle.
- Utiliser l'API Batch d'OpenAI pour les fichiers non urgents.
- Implémenter un cache (Redis) indexé sur le hash du fichier pour éviter de re-classifier des fichiers identiques.
- Stocker les résultats dans une base de données (PostgreSQL) au lieu d'un fichier JSON unique.

### 2. Fiabilité (Qualité de classification)

- Constituer un dataset labellisé à partir des classifications validées par des humains.
- Fine-tuner un modèle plus petit et moins coûteux (GPT-4o-mini ou un modèle open-source comme Mistral) sur ce dataset.
- Implémenter un système à deux passes : modèle rapide pour la classification initiale, modèle complet pour les fichiers à faible confiance.
- Ajouter une pré-classification par règles pour les cas évidents (ex: fichiers `.csv` = `Exports_donnees`) afin de réduire la dépendance au LLM.
- Monitorer la précision avec des métriques automatisées et des alertes.

### 3. Boucle de correction humaine

- Construire une interface web de revue où les opérateurs voient les fichiers dans `A_verifier/`, confirment ou corrigent la classification.
- Chaque correction humaine est loguée et réinjectée dans le dataset d'entraînement.
- Implémenter une boucle d'apprentissage actif : le système priorise la revue des fichiers où le modèle est le moins confiant.
- Ré-entraînement ou raffinement du prompt hebdomadaire basé sur les corrections accumulées.
- Dashboard montrant les tendances de précision par catégorie, par agence, dans le temps.

### 4. Multi-agences / contraintes terrain

- Chaque agence dispose d'un endpoint ou dossier d'upload unique avec des métadonnées d'agence.
- Normaliser les conventions de nommage par agence (certaines utilisent des formats différents).
- Implémenter des profils de classification par agence si certaines produisent systématiquement certains types de fichiers.
- Ajouter une logique de retry et de dégradation gracieuse pour les pannes réseau/API dans les zones à connectivité instable.
