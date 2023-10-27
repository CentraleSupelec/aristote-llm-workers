import torch
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from transformers import AutoModelForCausalLM, AutoTokenizer
from typing import Any, Dict

MODEL_NAME = ""
UVICORN_HOST = "0.0.0.0"
UVICORN_PORT = 8000

app = FastAPI()
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    device_map="auto",
    torch_dtype=torch.bfloat16,
)
model.eval()
print("Using the following device: ", model.device)


class TextInput(BaseModel):
    text: str
    parameters: Dict[str, Any]


class GenerationOutput(BaseModel):
    generation: str


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/generate")
async def generate(text_input: TextInput) -> GenerationOutput:
    tokenized_text = tokenizer(
        text_input.text,
        return_tensors="pt",
    )
    # generation_config = text_input.parameters
    outputs = model.generate(
        **tokenized_text.to(model.device),
        **text_input.parameters,
    ).squeeze(0)
    input_length = tokenized_text["input_ids"].shape[1]
    completion = tokenizer.decode(outputs[input_length:], skip_special_tokens=True)
    return GenerationOutput(generation=completion)


if __name__ == "__main__":
    uvicorn.run(app, host=UVICORN_HOST, port=UVICORN_PORT)
