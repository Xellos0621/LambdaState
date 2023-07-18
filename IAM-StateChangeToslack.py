import json
import logging
import os
from datetime import datetime

from urllib.request import Request, urlopen

# 환경변수로 불러오기
SLACK_CHANNEL = os.environ['SLACK_CHANNEL']
HOOK_URL = os.environ['HOOK_URL']
ACCOUNT = os.environ['ACCOUNT']
TZ = os.environ['TZ']

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def listToString(str_list):
    result = ""
    for s in str_list:
        result += s + " "
    return result.strip()


def lambda_handler(event, context):
    logger.info("Event: " + str(event))
    now = datetime.now()
    nowDate = str(now.year) + "-" + str(now.month) + "-" + str(now.day) + "  " + str(now.hour) + ":" + str(
        now.minute) + ":" + str(now.second) + " KST"

    event_Name = event['detail']['eventName']
    event_Type = event['detail']['userIdentity']['type']
    event_Time = event['detail']['eventTime']
    print("event_Name : " + event_Name)
    print("event_Type : " + event_Type)

    if event_Name != "GenerateServiceLastAccessedDetails" and event_Type != "AssumedRole" and event_Name != "CreateLoginProfile" and event_Name != "DeleteLoginProfile":
        event_source = event['source']
        use_userName = event['detail']['userIdentity']['userName']

        if event_Name == "CreatePolicyVersion" or event_Name == "CreatePolicy" or event_Name == "ChangePassword" or event_Name == "DeletePolicy" or event_Name == "AttachRolePolicy" or event_Name == "CreateServiceLinkedRole" or event_Name == "DetachRolePolicy":
            add_userName = " "
        else:
            add_userName = "*변경된 계정*\n" + event['detail']['requestParameters']['userName']

        add_userPolicy = " "
        eventName = " "

        if event_Name == "AttachUserPolicy":
            eventName = "권한 추가"
            split_policy = event['detail']['requestParameters']['policyArn'].split(':')
            matching = [s for s in split_policy if "policy" in s]
            print(matching)
            add_userPolicy = "*추가된 권한*\n" + listToString(matching)
        elif event_Name == "DetachUserPolicy":
            eventName = "권한 삭제"
            split_policy = event['detail']['requestParameters']['policyArn'].split(':')
            matching = [s for s in split_policy if "policy" in s]
            print(matching)
            add_userPolicy = "*삭제된 권한*\n" + listToString(matching)
        elif event_Name == "DeleteUser":
            eventName = "계정 삭제"
            add_userPolicy = "*이벤트*\n계정 삭제"
        elif event_Name == "CreateUser":
            eventName = "계정 생성"
            add_userPolicy = "*이벤트*\n계정 생성"
        elif event_Name == "CreateAccessKey":
            eventName = "엑세스키 생성"
            add_userPolicy = "*이벤트*\n엑세스키 생성"
        elif event_Name == "ChangePassword":
            eventName = "비밀번호 변경"
            add_userPolicy = "*이벤트*\n비밀번호 변경"
        elif event_Name == "CreatePolicyVersion":
            split_policy = event['detail']['requestParameters']['policyArn'].split(':')
            matching = [s for s in split_policy if "policy" in s]
            print(matching)
            add_userPolicy = "*변경된 정책*\n" + listToString(matching)
            add_userName = "*정책 버전 변경*\n" + listToString(matching)
        elif event_Name == "CreatePolicy":
            eventName = "정책 생성"
            print("add_userPolicy : " + add_userPolicy)
            add_userName = "*생성된 정책*\n" + event['detail']['requestParameters']['policyName']
        elif event_Name == "DeletePolicy":
            split_policy = event['detail']['requestParameters']['policyArn'].split(':')
            matching = [s for s in split_policy if "policy" in s]
            print(matching)
            eventName = "정책 삭제"
            add_userName = "*삭제된 정책*\n" + listToString(matching)
        else:
            eventName = event_Name

        if eventName != "TagUser":
            # slack 으로 보낼 메세지 설정
            slack_message = {
                "channel": SLACK_CHANNEL,
                "attachments": [{
                    "color": "#eb4034",
                    "blocks": [{
                        "type": "section",
                        "fields": [{
                            "type": "mrkdwn",
                            "text": "*실행자*\n" + use_userName
                        },
                            {
                                "type": "mrkdwn",
                                "text": "*리소스*\n" + event_source
                            },
                            {
                                "type": "mrkdwn",
                                "text": add_userName
                            },
                            {
                                "type": "mrkdwn",
                                "text": add_userPolicy
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
                        "text": ACCOUNT + ' 에서 ' + eventName + ' 이벤트가 발생되었습니다.'
                    }
                }
                ]
            }
            print(slack_message)
            # slack 으로 요청보내기
            req = Request(HOOK_URL, json.dumps(slack_message).encode('utf-8'))
            response = urlopen(req)
            response.read()
        else:
            print("eventName != TagUser 끝")

    else:
        print(
            "event_Name != GenerateServiceLastAccessedDetails and event_Type != AssumedRole and event_Name != CreateLoginProfile and event_Name != DeleteLoginProfile 끝")