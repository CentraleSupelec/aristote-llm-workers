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


def generate_html(metadata, quizzes):
    html = ""
    html += f"<h2>Title: {metadata['title']}</h2>\n"
    html += "<h3>Desctiption: </h3>\n"
    html += f"{metadata['description']}\n"
    html += "============================================\n"
    for quiz in quizzes:
        question = quiz["quiz"]["question"]
        answer = quiz["quiz"]["answer"]
        fake_answer_1 = quiz["quiz"]["fake_answer_1"]
        fake_answer_2 = quiz["quiz"]["fake_answer_2"]
        fake_answer_3 = quiz["quiz"]["fake_answer_3"]
        html += f"<h3>Question: {question}</h3>\n"
        html += "<ul>\n"
        for choice in [answer, fake_answer_1, fake_answer_2, fake_answer_3]:
            html += f"<li>{choice}</li>\n"
        html += "</ul>\n"
        html += "------------------------------------------\n"
    return html


def main(live_mode: str, language_input: str, model: str, transcript_path: str):
    if live_mode:
        metadata, quizzes = generate_data_live(language_input, model, transcript_path)
    else:
        metadata, quizzes = get_generated_data(language_input, model, transcript_path)
    return generate_html(metadata, quizzes)


with gr.Blocks() as demo:
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
        out = gr.HTML()
    btn = gr.Button("Run")
    btn.click(
        fn=main, inputs=[live_mode, language_input, model, transcript_path], outputs=out
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
