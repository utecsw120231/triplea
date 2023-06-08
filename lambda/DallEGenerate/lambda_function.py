import json
import boto3
import openai


def get_dalle_images(query, n=1, size="256x256"):
    response = openai.Image.create(prompt=query, n=n, size="256x256")
    ret = [r["url"] for r in response["data"]]

    return ret


def lambda_handler(event, context):
    openai.api_key = "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"

    j = json.loads(event["body"])

    query = j["query"]
    for_real = j.get("for_real", False)
    n_images = j.get("n_images", 1)

    if not for_real:
        images = ["https://picsum.photos/256/256" for _ in range(n_images)]
    else:
        images = get_dalle_images(query, n_images)

    ret = {"ok": True, "images": images}

    return {"statusCode": 200, "body": json.dumps(ret)}
