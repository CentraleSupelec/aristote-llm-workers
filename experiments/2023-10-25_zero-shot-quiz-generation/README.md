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
  - [First experiment](#first-experiment-1)
    - [Feedback on the experiment](#feedback-on-the-experiment)
  - [Second experiment](#second-experiment-1)
    - [Qualitative analysis](#qualitative-analysis-1)
    - [Next steps](#next-steps)
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

### First experiment

#### Feedback on the experiment

##### Feedback on the pipeline

Generation is very slow now. The use of vLLM + request batching is really good. It accelerates the rquests a lot.

##### Qualitative analysis

The quizzes are not always very relevant. The quizzes use specific details of the transcript with no context. A post-hoc method is needed to filter the scripts that are not relevant.

### Second experiment

#### Qualitative analysis

Title and description generation can be improved. Sometimes the description is a bit too long.

The evaluation is not very relevant for now. I am not sure that it realy understands the evaluation task.

#### Next steps

- Make title/description generation more robust
- Use an evaluation model? --> Maybe generate quizzes in English to take profit of better evaluation models
- Try ChatGPT, GPT-4 and Zephyr Beta on the second pipeline --> Vigostral is quite limited compared to ChatGPT and GPT-4

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

<!-- Delete this line -->
Conclude on the experiment and the results. State the answer to the hypothesis.
