# Introduction

Nous pouvons résumer l'objectif du projet Aristote avec cette phrase: **"augmenter les vidéos éducatives grâce à l'IA"**. Concrètement, l'idée est d'utiliser les LLMs pour transformer une simple vidéo en quelque chose de plus multimodal, plus interactif, et plus efficace pour l'enseignement, sans ajouter de la charge de travail sur les dos des professeurs.

Nous avons implémenté les fonctionnalités suivantes:
1. Transcription automatique des vidéos grâce à Whisper
2. Génération automatique de métadonnées (titre, description, *topics* etc.)
3. Génération automatique de QCMs
4. Fonctionnalité de rééexplication interactive
5. Création d'un PDF de slides à partir de la vidéo
6. Une interface Web de démo

Le projet utilise la bibliothèque [LangChain](https://www.langchain.com/) comme framework pour toutes les fonctionnalités liées aux LLMs. La plupart des fonctionnalités ci-dessus sont donc implémentées en tant que chaînes LangChain plutôt que des simples scripts Python. 

Le notebook `app/main.ipynb` permet de mettre la plupart de ces fonctionallités en mouvement. Cela se passe en 3 étapes:
1. Premièrement, il faut générer les transcripts, convertir l'audio en texte, afin de pouvoir les utiliser dans les LLMs. Pour cela, il faut utiliser la classe `Transcript` (définie dans `src/transcribe/transcript.py`), en particulier la méthode `from_path` - un exemple d'utilisation est dans `app/demos/week1.ipynb`:
```python
from src.transcribe import Transcript
Transcript.use_API(True) # If set to False, will use a locally installed version of Whisper - quite slower, but free !
statquest_transcript = Transcript.from_path(video_path)
```
> Cette étape est à faire manuellement, ce n'est pas implémenté dans `main.ipynb`

2. Passer le transcript par une de nos chaînes `LangChain`. La plupart de ces chaînes font usage de la technique "Split-Transform-Combine" (voir les slides ou ci-dessous) pour gérer des textes de longueur arbitraire. Chacune de ces chaînes prend du texte en entrée (le transcript de la vidéo), et y applique diverses manipulations, transformations, et fait des appels au LLM.
3. On sauvegarde tous les résultats sous forme de JSON, pour pouvoir les utiliser dans le site de démo (on peut utiliser le script `app/load_to_front.py`)

# Structure du projet
- `src/LLM_engine`: fonctionnalités communes à toutes les chaînes
	- `LoadJSONChain.py`: l'idée de cette classe est de "nettoyer" une réponse JSON obtenue à partir d'un LLM, afin de pouvoir la charger en tant qu'objet Python (les LLMs renvoient souvent du JSON légèrement incorrect, ou avec du texte en plus).
	- `custom_splitters.py`: implémente une classe permettant de découper du texte en blocs à peu près égaux en nombre de tokens, mais sans jamais couper une phrase au milieu.
	- `split_transform_combine.py`: la classe de base implémentant la technique "Split-Transform-Combine" (voir [ci-dessous](#elements-techniques)). C'est une classe abstraite, les sous-classes doivent implémenter les fonctions `_split`, `_transform` et `_combine_` (et optionellement `_validate` et `_correct`)
	- `prompts.py`: tous les prompts utilisés par les chaînes de ce module
	- `StatisticalCombiner.py`: non utilisé
	- `LLM_engine/ingest_reduce`: Implémente la chaîne de "summarisation hybride" (voir [ci-dessous](#elements-techniques)).
- `src/meta_gen`: Différentes chaînes utilisant la technique "STC" pour la génération de métadonnées autour de la vidéo. Chaque sous-module implémente une `xxx_chain`, qui permet de traiter un petit bout de texte, ainsi qu'une `xxx_STC_chain`, qui permet d'appeler la `xxx_chain` plusieurs fois en parallèle afin de traiter des textes plus long (voir l'explication de la technique STC pour plus de détails)
	- `title_gen`: Génération d'un titre pour la vidéo à partir de son transcript
	- `description_gen`: Génération d'une description pour la vidéo à partir de son transcript
	- `topics`: Génération de *topics* pour la vidéo à partir de son transcript, comme "Expansion de l'univers", "Géopolitique européenne" etc.
	- `tags_gen`: Génération de *tags* pour la vidéo à partir de son transcript. Contrairement à un *topic*, qui est généré librement par le LLM, pour un *tag* on lui demande de les sélectionner à partir d'une liste prédéfinie.
- `src/mcq_gen`: Toutes les chaînes liées à la création de QCMs: génération de questions, des réponses à ces questions, explications etc.
- `src/video2pdf`: Création de PDFs contenant transcript et slides côte-à-côte
- `src/from_topics`: Techniques alternatives pour la génération de métadonnées, à partir des *topics* plutôt qu'à partir du transcript lui-même

# Elements techniques
## Split-Transform-Combine
Un des problèmes récurrents pendant la réalisation de ce projet a été celui de la "fenêtre de contexte", ou de "longueur de prompt": les LLMs, même en mode chat*, ne peuvent pas accepter des prompts de longueur arbitraire. Pour GPT-3 par exemple c'est 4000 tokens environ.

> * En discutant avec ChatGPT, on ne se rend pas compte de cette limitation, les conversations peuvent être bien plus longues que 4000 tokens. Il faut bien comprendre la distinction ici entre le *LLM* GPT-3, et *l'application* ChatGPT. Le LLM, auquel on peut accéder via l'API ou le playground, et utilisé par ChatGPT en arrière-plan, est limité aux 4000 tokens - l'application est en fait constamment en train de summariser les messages plus vieux dans la conversation avant de passer chaque nouveau message au LLM, donnant *l'illusion* d'une fenêtre de contexte bien plus grande.

Or, un transcript d'une vidéo de 3h se compte en dizaines de milliers de tokens. Nous avons donc imaginé une technique générique, que nous utilisont dans la plupart de nos fonctionnalités: *Split-Transform-Combine*.

Il faut d'abord créer une chaîne LangChain implémentant la fonctionnalité que l'on veut, sans se préoccuper de ces problèmes de tokens. Ces chaînes sont implémentées dans les fichiers `description_chain.py`, `title_chain.py`, `mcq_chain.py` etc. Cette chaîne remplit le rôle de *Transform*.

L'idée est alors d'utiliser cette chaîne de nombreuses fois en parallèle sur des morceaux du long texte, et de recombiner tous leurs outputs par la suite: *Split* et *Combine*. 
La partie *Split* est assez simple: on découpe simplement le texte en blocs d'environ la même longueur, le plus proche possible de la taille maximale (on fait cependant attention à ne pas couper une phrase en plein milieu, voir `src/LLM_engine/custom_splitters.py`). 
Pour *Combine*, cela dépend de la chaîne *Transform*, souvent une chaîne LangChain aussi, avec un prompt comme, par exemple "Voici les titres des chapitres d'une vidéo éducative: <RESULTATS DES CHAINES *TRANSFORM*>. Quel serait un bon titre pour la vidéo complète ?"

## Summarisation hybride
Avant d'essayer STC, nous avons essayé de passer par la création d'un résumé du texte, un résumé suffisamment efficace pour que le texte puisse rentrer dans la fenêtre de contexte (~10 000 -> 4000 tokens).

Il existe deux techniques principales pour la summarisation: **Map reduce** et **Refine**. Chacune a ses avantages et inconvénients, mais globalement map_reduce fonctionne bien pour extraire les grandes lignes alors que refine fonctionne mieux pour extraire les points spécifiques mais importants d'un texte.

Ainsi, nous avons voulu implémenter une technique "hybride", combinant ces deux techniques de manière paramétrable, pour pouvoir summariser plus ou moins, en gardant plus ou moins de détail. Au final, nous ne nous sommes pas servi de cette technique: elle donne de bien moins bons résultats que STC, et demande beaucoup de *bidouillage* à la main pour trouver les bons paramètres pour chaque texte donné en entrée.

Plus de détails sont dans le document `doc/Ingestion.md`
