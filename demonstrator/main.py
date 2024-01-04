import gradio as gr

from .generate_quizzes_live import generate_data_live
from .get_generated_quizzes import get_generated_data, transcript_name2path


def update(name):
    return f"Welcome to Gradio, {name}!"


MODEL_NAMES = [
    "bofenghuang/vigogne-2-7b-instruct",
    "bofenghuang/vigogne-2-13b-instruct",
    "bofenghuang/vigostral-7b-instruct",
    "HuggingFaceH4/zephyr-7b-beta",
    "teknium/OpenHermes-2.5-Mistral-7B",
    "gpt-3.5-turbo-1106",
    "gpt-4-1106-preview",
]


def generate_html(
    chunks,
    metadata,
    quizzes,
    show_original_text=False,
    show_reformulation: bool = False,
):
    html = ""
    html += f"<h2>Title: {metadata['title']}</h2>\n"
    html += "<h3>Desctiption: </h3>\n"
    html += f"<p>{metadata['description']}</p>\n"
    html += "<p>============================================</p>\n"
    html += f"<p>Number of chunks:{len(chunks)}</p>\n"
    html += f"<p>Number of quizzes:{len(quizzes)}</p>\n"
    html += "<p>============================================</p>\n"
    for i, quiz in enumerate(quizzes):
        if show_original_text and i < len(chunks):
            html += "<h3>Original Transcript:</h3>\n"
            html += f"<p>{chunks[i]['chunk']}</p>\n"
        if show_reformulation:
            html += "<h3>Reformulated Transcript:</h3>\n"
            html += f"<p>{quiz['quiz']['quiz_origin_text']}</p>\n"
        question = quiz["quiz"]["question"]
        answer = quiz["quiz"]["answer"]
        fake_answer_1 = quiz["quiz"]["fake_answer_1"]
        fake_answer_2 = quiz["quiz"]["fake_answer_2"]
        fake_answer_3 = quiz["quiz"]["fake_answer_3"]
        explanation = quiz["quiz"]["explanation"]
        html += f"<h3>Question {i+1}: {question}</h3>\n"
        html += "<ul>\n"
        for choice in [answer, fake_answer_1, fake_answer_2, fake_answer_3]:
            html += f"<li>{choice}</li>\n"
        html += "</ul>\n"
        html += "<h4>Evaluation:</h4>\n"
        html += "<ul>\n"
        for key in quiz["evaluation"]:
            html += f"<li>{key}: {quiz['evaluation'][key]}</li>\n"
        html += "</ul>\n"
        html += "<h4>Explanation:</h4>\n"
        html += f"<p>{explanation}</p>\n"
        html += "<p>------------------------------------------</p>\n"
    return html


def main(
    live_mode_: bool,
    language_input_: str,
    model_: str,
    transcript_path_: str,
    order_: bool,
    show_original_text_: bool,
    show_reformulation_: bool,
    is_related_: bool,
    is_self_contained_: bool,
    is_question_: bool,
    language_is_clear_: bool,
    answers_are_all_different_: bool,
    fake_answers_are_not_obvious_: bool,
    answers_are_related_: bool,
    quiz_about_concept_: bool,
):
    filters = {
        "is_related": is_related_,
        "is_self_contained": is_self_contained_,
        "is_question": is_question_,
        "language_is_clear": language_is_clear_,
        "answers_are_all_different": answers_are_all_different_,
        "fake_answers_are_not_obvious": fake_answers_are_not_obvious_,
        "answers_are_related": answers_are_related_,
        "quiz_about_concept": quiz_about_concept_,
    }
    if live_mode_:
        chunks, metadata, quizzes = generate_data_live(
            language_input_, model_, transcript_path_, order_
        )
    else:
        chunks, metadata, quizzes = get_generated_data(
            language_input_, model_, transcript_path_, order_, filters
        )
    return generate_html(
        chunks,
        metadata,
        quizzes,
        show_original_text=show_original_text_,
        show_reformulation=show_reformulation_,
    )


with gr.Blocks(css="demonstrator/style.css") as demo:
    gr.Markdown("# Quiz Generator")
    gr.Markdown("Generate quizzes with the best open source models:")

    with gr.Column():
        live_mode = gr.Checkbox(label="Live Mode")
        language_input = gr.Radio(choices=["en", "fr"], value="fr", label="Language")
        model = gr.Dropdown(
            choices=MODEL_NAMES,
            label="Model Choice",
            value="teknium/OpenHermes-2.5-Mistral-7B",
        )
        transcript_path = gr.Dropdown(
            choices=list(transcript_name2path.keys()),
            label="Transcript Choice",
            value="cs_ri",
        )
        order = gr.Checkbox(label="Order by Score")
        show_original_text = gr.Checkbox(label="Show Original Text")
        show_reformulated_text = gr.Checkbox(label="Show Reformulated Text")
        with gr.Row():
            is_related = gr.Checkbox(label="Is Related")
            is_self_contained = gr.Checkbox(label="Is Self Contained")
            is_question = gr.Checkbox(label="Is Question")
            language_is_clear = gr.Checkbox(label="Language is Clear")
            answers_are_all_different = gr.Checkbox(label="Answers are all different")
            fake_answers_are_not_obvious = gr.Checkbox(
                label="Fake Answers are not Obvious"
            )
            answers_are_related = gr.Checkbox(label="Answers are Related")
            quiz_about_concept = gr.Checkbox(label="Quiz about Concept")
        btn = gr.Button("Run")
        out = gr.HTML()
    btn.click(
        fn=main,
        inputs=[
            live_mode,
            language_input,
            model,
            transcript_path,
            order,
            show_original_text,
            show_reformulated_text,
            is_related,
            is_self_contained,
            is_question,
            language_is_clear,
            answers_are_all_different,
            fake_answers_are_not_obvious,
            answers_are_related,
            quiz_about_concept,
        ],
        outputs=out,
    )

if __name__ == "__main__":
    DEMONSTRATOR_HOST = "0.0.0.0"
    DEMONSTRATOR_PORT = 8080
    try:
        demo.launch(server_name=DEMONSTRATOR_HOST, server_port=DEMONSTRATOR_PORT)
    except KeyboardInterrupt:
        demo.close()
        gr.close_all()
    except Exception as e:
        demo.close()
        gr.close_all()
        raise e
