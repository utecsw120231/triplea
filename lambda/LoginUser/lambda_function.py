import json
import boto3
import jwt
import datetime

from google.oauth2 import id_token
from google.auth.transport import requests


def lambda_handler(event, context):
    j = json.loads(event["body"])

    t = j["type"]

    secret = "my_secret_key"

    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table("storyteller_bot")

    if t == "google":
        token = j["token"]

        idinfo = id_token.verify_oauth2_token(token, requests.Request())

        return {
            "statusCode": 500,
            "body": json.dumps({"ok": False, "msg": "Not implemented"}),
        }

    email = j["email"]
    password = j["password"]

    response = table.get_item(Key={"user_email": email, "type": "user"})

    if "Item" not in response:
        return {
            "statusCode": 404,
            "body": json.dumps({"ok": False, "msg": "User not registered"}),
        }

    user = response["Item"]
    if password != user["password"]:
        return {
            "statusCode": 401,
            "body": json.dumps({"ok": False, "msg": "Wrong password"}),
        }

    expiration_time = str(datetime.datetime.now() + datetime.timedelta(days=1))

    token = jwt.encode(
        {"email": email, "expires_on": expiration_time}, secret, algorithm="HS256"
    )
    return {
        "statusCode": 200,
        # "multiValueHeaders": {
        #     "Set-Cookie": [
        #         jwt.encode(
        #             {"email": email, "expires_on": expiration_time},
        #             secret,
        #             algorithm="HS256",
        #         )
        #     ]
        # },
        #
        "body": json.dumps(
            {
                "ok": True,
                "email": user["user_email"],
                "name": user["username"],
                "profile_picture": "https://picsum.photos/128/128",
                "token": token,
            }
        ),
    }
