import boto3
import json
import openai
import inspect


def prompts_for_story(story):
    behaviour = """
    Follow my instructions as precisely as possible.
    You are given an story and you will give a list of prompts so that DALL-E can be used to generate images for the story.
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


def lambda_handler(event, context):
    j = json.loads(event["body"])
    story = j["story"]

    openai.api_key = "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"

    answer = prompts_for_story(story)
    ret = answer.split("\n")

    ja = json.dumps({"ok": True, "queries": ret})

    return {"ok": True, "statusCode": 200, "body": ja}
