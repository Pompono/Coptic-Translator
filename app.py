from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from translator import CopticTranslator

app = FastAPI(title="Coptic-English Translator API")

translator = CopticTranslator()


class TranslationRequest(BaseModel):
    text: str
    direction: str


@app.post("/translate")
def translate(request: TranslationRequest):
    if request.direction == "coptic_to_english":
        translation = translator.coptic_to_english(request.text)
    elif request.direction == "english_to_coptic":
        translation = translator.english_to_coptic(request.text)
    else:
        return {
            "error": "direction must be coptic_to_english or english_to_coptic"
        }

    return {
        "input": request.text,
        "direction": request.direction,
        "translation": translation
    }


app.mount("/", StaticFiles(directory="static", html=True), name="static")