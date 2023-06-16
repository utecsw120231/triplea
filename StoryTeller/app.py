import base64
import datetime
import hashlib
import inspect
from io import BytesIO

from db import get_db, init_app

import boto3
import flask
import jwt
import openai
from flask import Flask, request
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    get_jwt,
    get_jwt_identity,
    jwt_required,
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
CORS(app)

app.config[
    "SQLALCHEMY_DATABASE_URI"
] = "postgresql://postgres:3141@localhost:5432/storytellerbd"
db = SQLAlchemy(app)

app.config["JWT_SECRET_KEY"] = "super-secret"

app.config[
    "DB_HOST"
] = "storyteller-bot-instance-1.cwtcnyqx5tws.us-east-1.rds.amazonaws.com"
app.config["DB_USER"] = "postgres"
app.config["DB_PASS"] = "REDACTED"

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
    response = openai.Image.create(
        prompt=query, n=n, size="256x256", response_format="b64_json"
    )

    s3 = boto3.client("s3")

    ret = []
    for image_b64 in (d["b64_json"] for d in response["data"]):
        image = base64.b64decode(image_b64)
        image_hash = hashlib.sha256(image).hexdigest()

        s3.upload_fileobj(BytesIO(image), "sb-user-images", image_hash)

        ret.append(image_hash)

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


@app.route("/image/create", methods=["POST"])
@jwt_required()
def generate_images():
    openai.api_key = "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"

    j = request.json

    if "query" not in j:
        return {"ok": False, "msg": "Missing `query`."}, 400

    if "story_id" not in j:
        return {"ok": False, "msg": "Missing `story_id`."}, 400

    query = j["query"]
    story_id = j["story_id"]
    for_real = j.get("for_real", False)
    n_images = j.get("n_images", 1)

    if not for_real:
        images = ["https://picsum.photos/256/256" for _ in range(n_images)]
    else:
        image_hashes = get_dalle_images(query, n_images)
        images = [
            flask.url_for("get_image", image_hash=image_hash)
            for image_hash in image_hashes
        ]

        user_email = get_jwt_identity()

        dynamodb = boto3.resource("dynamodb")
        table = dynamodb.Table("storyteller_bot")
        for i_hash in image_hashes:
            table.put_item(
                Item={
                    "user_email": user_email,
                    "type": "image",
                    "story_id": story_id,
                    "image_hash": i_hash,
                }
            )

    return {"ok": True, "images": images}


@app.route("/image/<image_hash>", methods=["GET"])
@jwt_required()
def get_image(image_hash):
    s3 = boto3.client("s3")

    image = BytesIO()
    s3.download_fileobj("sb-user-images", image_hash, image)

    image.seek(0)
    return flask.send_file(image, mimetype="image/png")


@app.route("/story", methods=["GET", "POST"])
@jwt_required()
def stories():
    user_email = get_jwt_identity()

    if request.method == "GET":
        with get_db().cursor() as cur:
            cur.execute(
                """
            SELECT story_id, title, created_at FROM story
            WHERE user_email = %s
            """,
                (user_email,),
            )

            return {"ok": True, "stories": cur.fetchall()}, 200

    j = request.json

    if "title" not in j:
        return {"ok": False, "msg": "Missing `title`."}
    title = j["title"]

    with get_db().cursor() as cur:
        cur.execute(
            """
        INSERT INTO story
        VALUES (DEFAULT, %s, %s)
        """,
            (user_email, title),
        )
        get_db().commit()

    return {"ok": True}, 200


if __name__ == "__main__":
    init_app(app)
    app.run(debug=True, port=8080)
