# Zero shot quiz generation

**Author:** Antonio Loison <[antonio.loison@illuin.tech](mailto:antonio.loison@illuin.tech)>

**Creation date:** Wed, 25 Oct 2023 18:08:49

<!-- Delete this line -->
Here are some template sections that you can fill or delete as you wish. For each section, you have the corresponding explanation.

**Table of contents:**

- [Objectives](#objectives)
- [Bibliography](#bibliography)
- [Studied methods](#studied-methods)
- [Results](#results)
- [Link to slides](#link-to-slides)
- [Steps to reproduce experiments](#steps-to-reproduce-experiments)
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
Try using GPT-4 to generate a quiz in a zero-shot setting.

## Results

<!-- Delete this line -->
Detail the results that were obtained for each method and how they can prove or disprove the hypothesis. Comment and compare the results.
<!-- Can be used to answer the section "Contribution scientifique, technique ou technologique"; "Description de la démarche suivie et des travaux réalisés" of the CIR -->

## Link to slides

<!-- Delete this line -->
Link to reference slides where you might keep the update of the project results.

## Steps to reproduce experiments

Generate GPT-4 Quizzes:

```bash
cd experiments/2023-10-25_zero-shot-quiz-generation
python generate_quiz_openai.py --model_name gpt-3.5-turbo --transcript_path ../../data/cs_videos_transcripts/transcript_rl.json --output_path results/gpt_3_5_ri_quiz.md
```

Generate GPT-3.5-turbo Quizzes:

```bash
cd experiments/2023-10-25_zero-shot-quiz-generation
python generate_quiz_openai.py --model_name gpt-3.5-turbo --transcript_path ../../data/cs_videos_transcripts/transcript_rl.json --output_path results/gpt_3_5_ri_quiz.md
```

## Conclusion/TLDR

<!-- Delete this line -->
Conclude on the experiment and the results. State the answer to the hypothesis.
