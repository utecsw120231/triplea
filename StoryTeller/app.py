import inspect
import json

import openai
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

from flask import Flask, jsonify, request

app = Flask(__name__)
CORS(app)

app.config[
    "SQLALCHEMY_DATABASE_URI"
] = "postgresql://postgres:3141@localhost:5432/storytellerbd"
db = SQLAlchemy(app)


class User(db.Model):
    email = db.Column(db.String(120), primary_key=True)
    name = db.Column(db.String(120))
    password_hash = db.Column(db.String(128))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


def get_dalle_images(query, n=1, size="256x256"):
    response = openai.Image.create(prompt=query, n=n, size="256x256")
    ret = [r["url"] for r in response["data"]]
    return ret


def prompts_for_story(story):
    behaviour = """
    Follow my instructions as precisely as possible.
    You are given a story and you will give a list of prompts so that DALL-E can be used to generate images for the story.
    Use full descriptions of the subjects instead of referring to them with their names.
    You must return the resulting prompts for DALL-E in an enumerated list, one query per line. Like this:
    1. Query1
    2. Query2
    """
    behaviour = inspect.cleandoc(behaviour)
    completion = openai.ChatCompletion()
    chat_log = [{"role": "system", "content": behaviour}]

    def askgpt(question, chat_log):
        chat_log.append({"role": "user", "content": question})
        response = completion.create(model="gpt-3.5-turbo", messages=chat_log)
        answer = response.choices[0]["message"]["content"]
        chat_log.append({"role": "assistant", "content": answer})
        return answer, chat_log

    answer, _ = askgpt(story, chat_log)
    return answer


@app.route("/story/prompts", methods=["POST"])
def create_queries():
    openai.api_key = "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"

    """
    j = json.loads(event["body"])
    story = j["story"]

    """
    story = request.json.get("story")

    answer = prompts_for_story(story)
    ret = answer.split("\n")
    return jsonify({"ok": True, "queries": ret})


@app.route("/generate_images", methods=["POST"])
def generate_images():
    openai.api_key = "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"
    query = request.json.get("query", "")
    for_real = request.json.get("for_real", False)
    n_images = request.json.get("n_images", 1)
    if not for_real:
        images = ["https://picsum.photos/256/256" for _ in range(n_images)]
    else:
        images = get_dalle_images(query, n_images)
    return jsonify({"ok": True, "images": images})


if __name__ == "__main__":
    app.run(debug=True, port=8080)
