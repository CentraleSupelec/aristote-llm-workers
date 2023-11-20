# Zero shot quiz generation

**Author:** Antonio Loison <[antonio.loison@illuin.tech](mailto:antonio.loison@illuin.tech)>

**Creation date:** Wed, 25 Oct 2023 18:08:49

<!-- Delete this line -->
Here are some template sections that you can fill or delete as you wish. For each section, you have the corresponding explanation.

**Table of contents:**

- [Objectives](#objectives)
- [Bibliography](#bibliography)
- [Studied methods](#studied-methods)
  - [First experiment](#first-experiment)
  - [Second experiment](#second-experiment)
- [Results](#results)
  - [Quiz generation pipeline](#quiz-generation-pipeline)
    - [Résultats obtenus sur des transcripts de cours en Recherche d’Informations et Clustering](#résultats-obtenus-sur-des-transcripts-de-cours-en-recherche-dinformations-et-clustering)
  - [Filtering](#filtering)
    - [Analyse des 5 premiers quizzes obtenus après filtrage](#analyse-des-5-premiers-quizzes-obtenus-après-filtrage)
- [Slides](#slides)
- [Steps to reproduce experiments](#steps-to-reproduce-experiments)
  - [Generate GPT-4 Quizzes](#generate-gpt-4-quizzes)
  - [Generate GPT-3.5-turbo Quizzes](#generate-gpt-35-turbo-quizzes)
  - [Generate Vigostral Quizzes](#generate-vigostral-quizzes)
  - [Generate English Quizzes with Zephyr](#generate-english-quizzes-with-zephyr)
- [Conclusion/TLDR](#conclusiontldr)

## Objectives

The objective of this experiment is to generate a quiz from a text in few-shot or zero-shot settings.

<!-- Can be used to answer the section "Objectifs scientifiques et techniques" and "Incertitudes" of the CIR -->

## Bibliography

<!-- Delete this line -->
State some references that are related to the experiment. Summarize the main known results.
<!-- Can be used to answer the section "Etat de l'art" of the CIR -->

## Studied methods

<!-- Can be used to answer the section "Contribution scientifique, technique ou technologique"; "Description de la démarche suivie et des travaux réalisés" of the CIR -->
### First experiment

Compare ChatGPT, GPT-4 and Vigostral to generate a quiz in a zero-shot setting.

**Pipeline**

Generate the quizzes:
- Split the transcript in N chunks of size 1000 tokens
- Ask the model to reformulate each chunk.
- Generate a quiz from the reformulation of each chunk.

### Second experiment

Use a simple open-source model with a more complex pipeline to generate the summaries.

**Pipeline**

Generate the metadata of the course:
- Split the transcript in N chunks of size 1000 tokens
- Ask the model to describe each chunk.
- Ask the model to summarize each described chunk
- Output the summary of the summaries and the title of the course

Generate the quizzes:
- Split the transcript in N chunks of size 1000 tokens and chunks of size 2000 to have local and more global contexts.
- Ask the model to describe each chunk.
- Generate a quiz from the description of each chunk.
- Evaluate the quiz with yes/no questions given the title and the description and choose the quizzes depending on different criteria:
  - Question is related to the course 
  - Question is self contained 
  - Question is a question 
  - Language is clear 
  - Are there non undefined symbols in the question? 
  - Answers are all different 
  - Fake answers are not obvious

## Results

### Quiz generation pipeline

Evaluation qualitative par rapport à 5 critères qualitatifs:

- Pertinence des questions
- Fluidité et cohérence de la langue
- Respect du format attendu
- Questions nécessitent des connaissances mal explicitées 
- Difficulté/Pertinence des mauvaises réponses

3 modèles: Vigostral, Zéphyr 7B et GPT-4

2 transcripts: 1 français sur de la recherche d’information et 1 anglais sur du clustering

#### Résultats obtenus sur des transcripts de cours en Recherche d’Informations et Clustering

Modèles | Pertinence des questions | Fluidité et cohérence de la langue | Respect du format attendu | Questions nécessitent des connaissances mal explicitées | Difficulté/Pertinence des mauvaises réponses
---------|-------------------------|-----------------------------------|----------------------|-----------------------------|---------------------------------------------------------
Vigostral | Souvent Bon (~70%) | Très bon | Encourageant, ne finit pas des réponses parfois | Parfois | Mauvais: les fausses sont trop proches parfois
Zephyr 7b | en français | Inégal: dépend du transcript et de la compréhension du transcript par le modèle, questions trop compliquées (~40%) | Bon, à tendance à trop parler et on perd le sens de la question/réponse | Bon, répète trop la question | Parfois | Mauvaise: fausses réponses trop proches de la vraie réponse ou complètement évidente
Zéphyr 7b en anglais | Souvent bonne (~80%) | Très bon | Bon, répète trop la question | Pas trop mais le cours a moins de notations mathématiques | Acceptable: quelques mauvaises réponses sont trop évidentes
GPT-4 | Bonne: dépend du transcript et pas de GPT4 (~90%) | Très bon | Bon: génération en trop | Parfois: Il faudrait faire un effort de prompting pour mieux préciser les notations | Acceptable

**Conclusion:** Par rapport à GPT4, les meilleurs modèles OS français ont tendance à proposer des questions/réponses d’une qualité inégale. Il est essentiel de les filtrer pour sélectionner les plus pertinentes!

### Filtering

Evaluation par rapport à 7 critères pour ranker les quizzes selon leur qualité:

- La question doit être:
  - Pertinente par rapport au cours
  - Auto-porteuse
  - Formattée telle une question
  - Claire et cohérente sémantiquement
  - (Mathématiques):  Ne doit pas contenir de symboles non définis préalablement
- Les multiples réponses proposées doivent être:
  - Toutes différentes
  - Les réponses fausses sont non triviales

Grâce à cette liste de critères, on utilise les LLMs pour auto-évaluer chaque question/réponses pour filtrer les questions moins pertinentes.

#### Analyse des 5 premiers quizzes obtenus après filtrage

Modèles | Pertinence des questions | Fluidité et cohérence de la langue | Respect du format attendu | Questions nécessitent des connaissances mal explicitées  | Difficulté/Pertinence des mauvaises réponses
---------|-------------------------|-----------------------------------|----------------------|-----------------------------|---------------------------------------------------------
Vigostral | Remontée biaisée de questions plus longues, les meilleures questions ne sont pas bien remontées | Toujours bon | Même qualité que la moyenne | Mieux: Sélection de questions compréhensibles sans le transcript  | Pas mieux que la plupart des quiz
Zephyr 7b | en français | ~80% de questions pertinentes sur les 5 1ères | Toujours bon, mais réponses toujours trop longues | Toujours bon | Pas besoin de connaissances préalables | Pas mieux que la plupart des quiz
Zephyr 7b | en anglais | ~80% de questions pertinentes sur les 5 1ères | Toujours bon | Toujours bon | Toujours bon | Le reranking final ne fait pas ressortir les questions qui respectent le mieux ce critère, mais l’évaluation sur ce critère est pertinente
GPT-4 | Même pertinence | Toujours bon | Toujours bon | Le reranking final ne fait pas ressortir les questions qui respectent le mieux ce critère, mais l’évaluation sur ce critère est pertinente | Le reranking final ne fait pas ressortir les questions qui respectent le mieux ce critère, mais l’évaluation sur ce critère est pertinente

Les modèles open-source ne sont pas très adaptés à l’évaluation des quizzes et la méthode ranking peu être affinée. Avec GPT-4, l’étape de filtrage permet de réduire le nombre de questions non pertinentes.

## Slides

<!-- Delete this line -->
Link to reference slides where you might keep the update of the project results.

## Steps to reproduce experiments

### Generate GPT-4 Quizzes

```bash
cd experiments/2023-10-25_zero-shot-quiz-generation
python generate_quiz_openai.py --model_name gpt-3.5-turbo --transcript_path ../../data/cs_videos_transcripts/transcript_rl.json --output_path results/gpt_3_5_ri_quiz.md
```

### Generate GPT-3.5-turbo Quizzes

```bash
cd experiments/2023-10-25_zero-shot-quiz-generation
python generate_quiz_openai.py --model_name gpt-3.5-turbo --transcript_path ../../data/cs_videos_transcripts/transcript_rl.json --output_path results/gpt_3_5_ri_quiz.md
```

### Generate Vigostral Quizzes

Launch the vLLM server with skypilot:

```bash
sky launch -c zero-shot-a100 --gpus A100:1 experiments/2023-10-25_zero-shot-quiz-generation/configs/skypilot/{MODEL_NAME_CONFIG}
```

Connect API in machine to local machine:
    
```bash
gcloud compute ssh {VM_NAME} --ssh-flag "-L 8000:localhost:8000"
```

Then make requests to the API:

```bash
python experiments/2023-10-25_zero-shot-quiz-generation/vigostral/generate_quizes.py --transcript_path data/cs_videos_transcripts/transcript_ri.json --output_path experiments/2023-10-25_zero-shot-quiz-generation/results/vigostral_ri_quiz.md
```

### Generate English Quizzes with Zephyr

```bash
quizgen generate-metadata configs/metadata_generation.yml
```

```bash
quizgen generate-quiz configs/quiz_generation.yml
```

## Conclusion/TLDR

Les modèles open-source Vigostral et Zéphyr 7B ne sont pas suffisamment bons en français pour générer des quizzes toujours pertinents. Il faut filtrer les quizzes générés pour ne garder que les meilleurs. Les modèles open-source ne sont pas très adaptés à l’évaluation des quizzes et la méthode ranking peu être affinée. GPT-4 agit comme un meilleur filtre.
