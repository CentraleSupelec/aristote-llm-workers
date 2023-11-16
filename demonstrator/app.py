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
    "gpt-3.5-turbo-1106",
    "gpt-4-1106-preview",
]

TRANSCRIPT_PATHS = [
    "data/cs_videos_transcripts/transcript_ri.json",
    "data/cs_videos_transcripts/transcript_sociologie.json",
    "data/mit_videos_transcripts/transcript_clustering.txt",
]


def generate_html(chunks, metadata, quizzes, show_original_text=False, show_reformulation: bool = False):
    html = ""
    html += f"<h2>Title: {metadata['title']}</h2>\n"
    html += "<h3>Desctiption: </h3>\n"
    html += f"<p>{metadata['description']}</p>\n"
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
        html += f"<h4>Evaluation:</h4>\n"
        html += "<ul>\n"
        for key in quiz["evaluation"]:
            html += f"<li>{key}: {quiz['evaluation'][key]}</li>\n"
        html += "</ul>\n"
        html += f"<h4>Explanation:</h4>\n"
        html += f"<p>{explanation}</p>\n"
        html += "<p>------------------------------------------</p>\n"
    return html


def main(live_mode: bool, language_input: str, model: str, transcript_path: str, order: bool, show_original_text: bool = False, show_reformulation: bool = False):
    if live_mode:
        chunks, metadata, quizzes = generate_data_live(language_input, model, transcript_path, order)
    else:
        chunks, metadata, quizzes = get_generated_data(language_input, model, transcript_path, order)
    return generate_html(chunks, metadata, quizzes, show_original_text=show_original_text, show_reformulation=show_reformulation)


with gr.Blocks(css="demonstrator/style.css") as demo:
    gr.Markdown("# Quiz Generator")
    gr.Markdown("Generate quizzes with the best open source models:")

    with gr.Column():
        live_mode = gr.Checkbox(label="Live Mode")
        language_input = gr.Radio(choices=["en", "fr"], value="fr", label="Language")
        model = gr.Dropdown(
            choices=MODEL_NAMES,
            label="Model Choice",
            value="bofenghuang/vigostral-7b-instruct",
        )
        transcript_path = gr.Dropdown(
            choices=list(transcript_name2path.keys()),
            label="Transcript Choice",
            value="cs_ri",
        )
        order = gr.Checkbox(label="Order by Score")
        show_original_text = gr.Checkbox(label="Show Original Text")
        show_reformulated_text = gr.Checkbox(label="Show Reformulated Text")
        btn = gr.Button("Run")
        out = gr.HTML()
    btn.click(
        fn=main, inputs=[live_mode, language_input, model, transcript_path, order, show_original_text, show_reformulated_text], outputs=out
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
