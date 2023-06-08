import jsoV
import boto3


def lambda_handler(event, context):
    j = json.loads(event["body"])

    email = j["email"]
    username = j["username"]
    password = j["password"]

    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table("storyteller_bot")

    response = table.get_item(Key={"user_email": email, "type": "user"})

    if "Item" in response:
        return {
            "statusCode": 409,
            "body": json.dumps({"ok": False, "msg": "Email is already registered"}),
        }

    table.put_item(
        Item={
            "user_email": email,
            "type": "user",
            "username": username,
            "password": password,
        }
    )

    lambda_client = boto3.client("lambda")

    lr = lambda_client.invoke(
        FunctionName="SB-LogInUser",
        InvocationType="RequestResponse",
        Payload=json.dumps(
            {
                "body": json.dumps(
                    {"type": "normal", "email": email, "password": password}
                )
            },
        ),
    )

    return lr["Payload"].read()
