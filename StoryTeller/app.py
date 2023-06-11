import datetime
import inspect
import json

import boto3
import jwt
import openai
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import (JWTManager, create_access_token, get_jwt,
                                get_jwt_identity, jwt_required)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
CORS(app)

app.config[
    "SQLALCHEMY_DATABASE_URI"
] = "postgresql://postgres:3141@localhost:5432/storytellerbd"
db = SQLAlchemy(app)

app.config["JWT_SECRET_KEY"] = "super-secret"
jwt = JWTManager(app)


class User(db.Model):
    email = db.Column(db.String(120), primary_key=True)
    name = db.Column(db.String(120))
    password_hash = db.Column(db.String(128))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


@app.route("/user", methods=["POST"])
def register_user():
    j = request.json

    if "email" not in j:
        return {"ok": False, "msg": "Missing `email`."}, 400
    if "username" not in j:
        return {"ok": False, "msg": "Missing `username`."}, 400
    if "password" not in j:
        return {"ok": False, "msg": "Missing `password`."}, 400

    email = j["email"]
    username = j["username"]
    password = j["password"]

    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table("storyteller_bot")

    response = table.get_item(Key={"user_email": email, "type": "user"})

    if "Item" in response:
        return {"ok": False, "msg": "Email is already registered"}, 409

    table.put_item(
        Item={
            "user_email": email,
            "type": "user",
            "username": username,
            "password": password,
        }
    )

    return login_regular(email, password)


def login_regular(email, password):
    # TODO: Extract to somewhere
    secret = "my_secret_key"

    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table("storyteller_bot")

    response = table.get_item(Key={"user_email": email, "type": "user"})

    if "Item" not in response:
        return {"ok": False, "msg": "User not registered"}, 404

    user = response["Item"]

    if password != user["password"]:
        return {"ok": False, "msg": "Wrong password"}, 401

    expiration_time = str(datetime.datetime.now() + datetime.timedelta(days=1))

    token = create_access_token(identity=email)

    return {
        "ok": True,
        "email": user["user_email"],
        "name": user["username"],
        "profile_picture": "https://picsum.photos/128/128",
        "token": token,
    }, 200


@app.route("/user/login", methods=["POST"])
def login_user():
    j = request.json

    if "type" not in j:
        return {"ok": False, "msg": "Missing `type`"}, 400

    t = j["type"]

    if t == "google":
        if "token" not in j:
            return {"ok": False, "msg": "Missing `token` in google authentication"}, 400

        token = j["token"]

        # idinfo = id_token.verify_oauth2_token(token, requests.Request())

        return {"ok": False, "msg": "Not implemented"}, 500

    if "email" not in j:
        return {"ok": False, "msg": "Missing `email`"}
    if "password" not in j:
        return {"ok": False, "msg": "Missing `password`"}

    email = j["email"]
    password = j["password"]

    return login_regular(email, password)


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
@jwt_required()
def create_queries():
    openai.api_key = "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"

    j = request.json
    if "story" not in j:
        return {"ok": False, "msg": "Missing `story`."}, 400

    story = j["story"]

    answer = prompts_for_story(story)
    ret = answer.split("\n")

    return {"ok": True, "queries": ret}

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
