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

    event_detailType = event['detail-type']
    event_region = event['region']
    event_resource = event['source']
    print("resource : " + event_resource)
    event_time = event['time']
    event_name = " "
    eventName = " "

    if event_detailType == "AWS API Call via CloudTrail" or event_detailType == "AWS Service Event via CloudTrail":
        event_name = event['detail']['eventName']

        event_Type = " "
        use_userName = " "
        backupName = " "

        if event_detailType == "AWS Service Event via CloudTrail":
            use_userName = " "
            backupName = "*백업볼트이름*\n" + event['detail']['serviceEventDetails']['backupVaultName']
        else:
            event_Type = event['detail']['userIdentity']['type']
            use_userName = event['detail']['userIdentity']['userName']

            if event_name == "StartRestoreJob":
                backupName = "*복구*"
            else:
                backupName = "*백업볼트이름*\n" + event['detail']['requestParameters']['backupVaultName']

        if event_Type != "AssumedRole":

            if event_name == "CreateBackupVault":
                eventName = "백업볼트생성"
            elif event_name == "BackupJobStarted":
                eventName = "백업 시작"
            elif event_name == "BackupJobCompleted":
                eventName = "백업 완료"
            else:
                eventName = event_name

            print("event_name : " + event_name)

            # slack 으로 보낼 메세지 설정
            slack_message = {
                "channel": SLACK_CHANNEL,
                "attachments": [{
                    "color": "#008000",
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
                                "text": "*이벤트*\n" + event_name
                            },
                            {
                                "type": "mrkdwn",
                                "text": "*리전*\n" + event_region
                            },
                            {
                                "type": "mrkdwn",
                                "text": backupName
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
        else:
            print("event_Type != AssumedRole else 끝")
    else:
        print("event_detailType == AWS API Call via CloudTrail else 끝")