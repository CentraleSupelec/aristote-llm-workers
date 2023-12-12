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
  - [Study of Prometheus/JudgeLM as a quiz evaluator](#study-of-prometheusjudgelm-as-a-quiz-evaluator)
    - [Judge LM](#judge-lm)
    - [Prometheus](#prometheus)
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

### Study of Prometheus/JudgeLM as a quiz evaluator

#### Judge LM

On the [Demo page](http://218.91.113.230:9004/):

Question:

```txt
You're a teaching assistant helping a teacher create a knowledge test for his students.
Here is a description of the course.
Title: Advanced Clustering Techniques in Machine Learning: Optimization, Algorithms, and Applications
Description: This course focuses on clustering in machine learning, covering optimization problems, objective functions, and constraints in clustering. It explores hierarchical clustering and k-means clustering algorithms, discussing their advantages and limitations. The course also addresses challenges in selecting the appropriate number of clusters and scaling attributes for better clustering results. Students will learn to apply clustering algorithms to real-world datasets and experiment with parameters for informed decision-making.
Generate a quiz related to the following course.
```

Reference answer:

```txt
Question: What is the time complexity of one iteration of the k-centroids clustering algorithm?
Answers:
- The time complexity of one iteration is O(k * n * d), where k is the number of centroids, n is the number of examples, and d is the dimensionality of the features.
- The time complexity of one iteration is O(n^2)
- The time complexity of one iteration is O(k * n)
- The time complexity of one iteration is O(k * n * d * log d)
```

Answer:

```txt
Question: What type of license allows for free access and use of the educational content in this course transcript?
Answers:
- The educational content in this course transcript is provided under a Creative Commons license.
- The educational content in this course transcript is protected by a proprietary license.
- The educational content in this course transcript is available under a public domain license.
- The educational content in this course transcript is distributed under a copyrighted license.
```

Evaluation:

```txt
Assistant 1’s response is not relevant to the course description provided. The assistant seems to be generating a quiz about the time complexity of one iteration of the k-centroids clustering algorithm, which is not related to the course titled “Advanced Clustering Techniques in Machine Learning: Optimization, Algorithms, and Applications”. Therefore, the assistant’s response is not helpful or accurate in this context.

Assistant 2’s response is also not relevant to the course description. The assistant seems to be generating a quiz about the type of license that allows for free access and use of the educational content in this course transcript. This is also not related to the course. However, the assistant’s response is more detailed than Assistant 1’s, providing multiple possible answers. Therefore, the assistant’s response is slightly more helpful than Assistant 1’s, but still not accurate or relevant.
```

#### Prometheus

Prompt:

```txt
###Task Description:
An instruction (might include an Input inside it), a response to evaluate, a reference answer that gets a score of 5, and a score rubric representing a evaluation criteria are given.
1. Write a detailed feedback that assess the quality of the response strictly based on the given score rubric, not evaluating in general.
2. After writing a feedback, write a score that is an integer between 1 and 5. You should refer to the score rubric.
3. The output format should look as follows: \"Feedback: (write a feedback for criteria) [RESULT] (an integer number between 1 and 5)\"
4. Please do not generate any other opening, closing, and explanations.

###The instruction to evaluate:
You're a teaching assistant helping a teacher create a knowledge test for his students.
Generate a quiz related to the following course.
Title: Advanced Clustering Techniques in Machine Learning: Optimization, Algorithms, and Applications
Description: This course focuses on clustering in machine learning, covering optimization problems, objective functions, and constraints in clustering. It explores hierarchical clustering and k-means clustering algorithms, discussing their advantages and limitations. The course also addresses challenges in selecting the appropriate number of clusters and scaling attributes for better clustering results. Students will learn to apply clustering algorithms to real-world datasets and experiment with parameters for informed decision-making.

###Response to evaluate:
Question: What type of license allows for free access and use of the educational content in this course transcript?
Answers:
- The educational content in this course transcript is provided under a Creative Commons license.
- The educational content in this course transcript is protected by a proprietary license.
- The educational content in this course transcript is available under a public domain license.
- The educational content in this course transcript is distributed under a copyrighted license.

###Reference Answer (Score 5):
Question: What is the time complexity of one iteration of the k-centroids clustering algorithm?
Answers:
- The time complexity of one iteration is O(k * n * d), where k is the number of centroids, n is the number of examples, and d is the dimensionality of the features.
- The time complexity of one iteration is O(n^2)
- The time complexity of one iteration is O(k * n)
- The time complexity of one iteration is O(k * n * d * log d)

###Score Rubrics:
[Are the question and answers related to the topics of the course? Are the question and answers about theoretical concepts and not about examples? Is the true answer not obvious? Are the answers all different? Are there any undefined terms? ]
Score 1: The question or answers are not related to the topics covered in the course.
Score 2: The question or answers are related but are not about theoretical concepts.
Score 3: The question and answers are related to the topics of the course but it has undefined terms.
Score 4: The question and answers are related to the topics of the course but it has an obvious response or answers are too close between each other.
Score 5: The question and answers are related to the topics of the course. The quiz is written in proper English. The question and answers are about theoretical concepts. The answers are all different. There are no undefined terms. The true answer is not obvious.

###Feedback: 
```

Feedback:

```txt
'The question and answers are related to the topics of the course. The question is about a theoretical concept, and the answers are all different. However, the true answer is not difficult to find, and the question could be improved by making the answer less obvious. There are no undefined terms. Overall, the quiz is well-written, but it could be improved by making the question more challenging. [RESULT] 4'
```

Both are really bad evaluators on this task. They fail on a simple example.

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
