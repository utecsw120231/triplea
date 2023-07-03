import base64
import datetime
import hashlib
import inspect
import os
import pathlib
import tempfile
import zipfile
from io import BytesIO

import boto3
import botocore
import flask
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
from psycopg.rows import dict_row
from werkzeug.security import check_password_hash, generate_password_hash

from db import get_db, init_app

app = Flask(__name__)
CORS(app, expose_headers=["Content-Type"])

app.config["JWT_ACCESS_TOKEN_EXPIRES"] = datetime.timedelta(hours=2)
app.config.from_prefixed_env(loads=lambda x: x)

jwt = JWTManager(app)


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
    table_name = app.config['DYNAMODB_USERS_TABLE']
    table = dynamodb.Table(table_name)

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
    table_name = app.config['DYNAMODB_USERS_TABLE']
    table = dynamodb.Table(table_name)

    response = table.get_item(Key={"user_email": email, "type": "user"})

    if "Item" not in response:
        return {"ok": False, "msg": "User not registered"}, 404

    user = response["Item"]

    if password != user["password"]:
        return {"ok": False, "msg": "Wrong password"}, 401

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
        return {"ok": False, "msg": "Missing `email`"}, 400
    if "password" not in j:
        return {"ok": False, "msg": "Missing `password`"}, 400

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

        bucket_name = app.config['S3_IMAGES_BUCKET']
        s3.upload_fileobj(BytesIO(image), bucket_name, image_hash)

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
    j = request.json
    if "story" not in j:
        return {"ok": False, "msg": "Missing `story`."}, 400

    story = j["story"]

    answer = prompts_for_story(story)
    ret = answer.split("\n")

    return {"ok": True, "queries": ret}


def image_from_s3(image_hash):
    s3 = boto3.client("s3")
    image = BytesIO()
    s3.download_fileobj("sb-user-images", image_hash, image)

    image.seek(0)

    return image


@app.route("/image/<image_hash>", methods=["GET"])
@jwt_required()
def get_image(image_hash):
    try:
        image = image_from_s3(image_hash)
    except botocore.exceptions.ClientError:
        return {"ok": False, "msg": "No such image."}, 404

    return flask.send_file(image, mimetype="image/png")


def image_hash_to_url(image_hash):
    return flask.url_for("get_image", image_hash=image_hash)


@app.route("/image/create", methods=["POST"])
@jwt_required()
def generate_images():
    j = request.json

    if "query" not in j:
        return {"ok": False, "msg": "Missing `query`."}, 400

    if "story_id" not in j:
        return {"ok": False, "msg": "Missing `story_id`."}, 400
    if type(j["story_id"]) != int:
        return {"ok": False, "msg": "`story_id` must be an integer"}, 400

    query = j["query"]
    story_id = j["story_id"]
    for_real = j.get("for_real", False)
    n_images = j.get("n_images", 1)

    user_email = get_jwt_identity()

    with get_db().cursor() as cur:
        cur.execute(
            """
            SELECT * FROM story
            WHERE story_id = %s
            AND user_email = %s
            """,
            (story_id, user_email),
        )
        if cur.fetchone() is None:
            return {
                "ok": False,
                "msg": "Given `story_id` does not exist associated to this user.",
            }, 400

    if not for_real:
        images = ["https://picsum.photos/256/256" for _ in range(n_images)]
    else:
        image_hashes = get_dalle_images(query, n_images)
        images = [image_hash_to_url(i_h) for i_h in image_hashes]

        user_email = get_jwt_identity()

        with get_db().cursor() as cur:
            for i_hash in image_hashes:
                cur.execute(
                    """
                    INSERT INTO image VALUES (%s, %s, %s)
                    """,
                    (i_hash, query, story_id),
                )

            get_db().commit()

    return {"ok": True, "images": images}


@app.route("/image", methods=["GET"])
@jwt_required()
def get_images():
    user_email = get_jwt_identity()
    with get_db().cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT story_id, hash, query FROM image JOIN story USING (story_id) WHERE user_email = %s
            """,
            (user_email,),
        )

        ret = dict()
        for row in cur:
            story_id = row["story_id"]
            ret.setdefault(story_id, list())
            ret[story_id].append((row["query"], image_hash_to_url(row["hash"])))

    return ret, 200


@app.route("/story/<int:s_id>", methods=["GET"])
@jwt_required()
def get_story_route(s_id):
    return get_story(s_id, get_jwt_identity(), "images" in request.args)


def get_story(s_id, user_email, with_images):
    with get_db().cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
        SELECT story_id, title, created_at FROM story
        WHERE user_email = %s
        AND story_id = %s
        """,
            (user_email, s_id),
        )

        s = cur.fetchone()

        if s is None:
            return {"ok": False, "msg": "User does not own such `story_id`."}, 404

        title = s["title"]
        created_at = s["created_at"]

        ret = {
            "ok": True,
            "story_id": s_id,
            "title": title,
            "created_at": created_at,
        }

        if not with_images:
            return ret, 200

        cur.execute(
            """
            SELECT hash, query FROM image WHERE story_id = %s
            """,
            (s_id,),
        )

        images = [
            {"url": image_hash_to_url(row["hash"]), "query": row["query"]}
            for row in cur
        ]
        ret["images"] = images

        return ret, 200


@app.route("/story/<int:s_id>/zip", methods=["GET"])
@jwt_required()
def get_story_image_zip(s_id):
    user_email = get_jwt_identity()

    with get_db().cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
        SELECT story_id, title, created_at FROM story
        WHERE user_email = %s
        AND story_id = %s
        """,
            (user_email, s_id),
        )

        s = cur.fetchone()

        if s is None:
            return {"ok": False, "msg": "User does not own such `story_id`."}, 404

        title = s["title"]

        cur.execute(
            """
            SELECT hash FROM image WHERE story_id = %s
            """,
            (s_id,),
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir = pathlib.Path(temp_dir)
            images_directory = temp_dir / "images"
            os.makedirs(images_directory)

            for h in (r["hash"] for r in cur):
                with open(images_directory / f"{h}.png", "wb") as h_fp:
                    image = image_from_s3(h)
                    h_fp.write(image.read())

            zip_filename = temp_dir / f"{s_id}-{title}.zip"
            with zipfile.ZipFile(zip_filename, mode="w") as archive:
                for file_path in images_directory.iterdir():
                    archive.write(file_path, arcname=file_path.name)

            return (
                flask.send_file(
                    zip_filename,
                    mimetype="application/zip",
                    as_attachment=True,
                ),
                200,
            )


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
        RETURNING story_id
        """,
            (user_email, title),
        )
        story_id = cur.fetchone()[0]
        get_db().commit()

    return {"ok": True, "story_id": story_id}, 200


@app.route("/style", methods=["GET", "POST"])
@jwt_required()
def styles():
    user_email = get_jwt_identity()

    if request.method == "GET":
        with get_db().cursor() as cur:
            cur.execute(
                """
            SELECT style FROM style
            WHERE user_email = %s
            """,
                (user_email,),
            )

            styles = [t[0] for t in cur.fetchall()]
            return {"ok": True, "styles": styles}, 200

    j = request.json

    if "style" not in j:
        return {"ok": False, "msg": "Missing `style`."}
    style = j["style"]

    with get_db().cursor() as cur:
        cur.execute(
            """
        INSERT INTO style
        VALUES (%s, %s)
        """,
            (user_email, style),
        )
        get_db().commit()

    return {"ok": True}, 200


init_app(app)

if __name__ == "__main__":
    app.run(debug=True, port=8080)