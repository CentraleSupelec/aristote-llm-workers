# GPT4 English Filtering

**Author:** Antonio Loison <[antonio.loison@illuin.tech](mailto:antonio.loison@illuin.tech)>

**Creation date:** Tue, 21 Nov 2023 12:05:16

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

Hypothesis:

1. We can generate good quizzes when generating a lot of quizzes.
2. GPT4 can be a good filter for English quizzes.
3. Reranking of the quizzes after filtering can improve the quality of the quizzes.

## Bibliography

<!-- Delete this line -->
State some references that are related to the experiment. Summarize the main known results.
<!-- Can be used to answer the section "Etat de l'art" of the CIR -->

## Studied methods

Pipeline:

- Generate several quizzes with Zephir 7B beta.
- Filter the quizzes with GPT4.

Do this on 5 transcripts:
- [ ] Machine Learning Course: MIT Clustering
- [ ] Law School Course: Harvard transcript
- [ ] [High School Biology](https://www.youtube.com/watch?v=qviLDKDJNKM&list=PL7B2654D8D1A53104&index=3)
- [ ] High School Literature: [Part 1](https://www.youtube.com/watch?v=I4kz-C7GryY&list=PLWkIOn7DGRlJzepuPNXU6CrHEjatOLg5S&index=2) and [Part 2](https://www.youtube.com/watch?v=9J4hoAatGRQ&list=PLWkIOn7DGRlJzepuPNXU6CrHEjatOLg5S&index=3)
- [ ] [MIT Thermodynamics](https://www.youtube.com/watch?v=JYuMimF6bu0)

For hypothesis 1, check if there are good quizzes among all the generated quizzes and which transcript difficulty --> Metric: number of good quizzes / number of quizzes.
For hypothesis 2, check if evaluation is coherent. --> Metric: accuracy of evaluation for several criteria.

## Results

<!-- Delete this line -->
Detail the results that were obtained for each method and how they can prove or disprove the hypothesis. Comment and compare the results.
<!-- Can be used to answer the section "Contribution scientifique, technique ou technologique"; "Description de la démarche suivie et des travaux réalisés" of the CIR -->

## Link to slides

<!-- Delete this line -->
Link to reference slides where you might keep the update of the project results.

## Steps to reproduce experiments

<!-- Delete this line -->
```bash
quizgen generate-metadata experiments/2023-11-21_gpt4-english-filtering/configs/zephyr_en_metadata_gen.yml
quizgen generate-quizzes experiments/2023-11-21_gpt4-english-filtering/configs/zephyr_en_quiz_gen.yml
quizgen evaluate experiments/2023-11-21_gpt4-english-filtering/configs/gpt4_en_eval.yml
```

**Example:**

You need to launch this command:

```bash
reproduce-experiments --input data/ --output results/ 
```

## Conclusion/TLDR

<!-- Delete this line -->
Conclude on the experiment and the results. State the answer to the hypothesis.
