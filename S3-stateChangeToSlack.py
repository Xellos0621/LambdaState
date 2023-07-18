import json
import logging
import os
from datetime import datetime

from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

# 환경변수로 불러오기
SLACK_CHANNEL = os.environ['SLACK_CHANNEL']
HOOK_URL = os.environ['HOOK_URL']
ACCOUNT = os.environ['ACCOUNT']
TZ = os.environ['TZ']

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    logger.info("Event: " + str(event))
    now = datetime.now()
    nowDate = str(now.year) + "-" + str(now.month) + "-" + str(now.day) + " " + str(now.hour) + ":" + str(
        now.minute) + ":" + str(now.second) + " KST"

    event_region = event['region']
    event_resource = event['source']
    use_userName = event['detail']['userIdentity']['userName']

    event_name = event['detail']['eventName']
    eventName = " "
    eventInstance = " "

    print("event_name : " + event_name)

    if event_name == "CreateBucket":
        eventName = "S3 버킷 생성"
        eventInstance = "*버킷이름*\n" + event['detail']['requestParameters']['bucketName']
    elif event_name == "PutBucketPublicAccessBlock":
        eventName = event_name
        eventInstance = "*버킷이름*\n" + event['detail']['requestParameters']['bucketName']
    elif event_name == "DeleteBucket":
        eventName = "S3 버킷 삭제"
        eventInstance = "*버킷이름*\n" + event['detail']['requestParameters']['bucketName']
    else:
        eventName = event_name

    # slack 으로 보낼 메세지 설정
    slack_message = {
        "channel": SLACK_CHANNEL,
        "attachments": [{
            "color": "#088A08",
            "blocks": [{
                "type": "section",
                "fields": [{
                    "type": "mrkdwn",
                    "text": "*계정*\n" + ACCOUNT
                },
                    {
                        "type": "mrkdwn",
                        "text": "*실행자*\n" + use_userName
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*리소스*\n" + event_resource
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*이벤트*\n" + eventName
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*리전*\n" + event_region
                    },
                    {
                        "type": "mrkdwn",
                        "text": eventInstance
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*발생시간*\n" + nowDate
                    }
                ]
            }]
        }],
        "blocks": [{
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": eventName + ' 이벤트가 발생되었습니다.'
            }
        }
        ]
    }

    # slack 으로 요청보내기
    req = Request(HOOK_URL, json.dumps(slack_message).encode('utf-8'))
    try:
        response = urlopen(req)
        response.read()
        logger.info("Message posted to %s", slack_message['channel'])
    except HTTPError as e:
        logger.error("Request failed: %d %s", e.code, e.reason)
    except URLError as e:
        logger.error("Server connection failed: %s", e.reason)
    else:
        print("try 끝")