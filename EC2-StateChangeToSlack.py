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

    if event_detailType == "AWS API Call via CloudTrail":
        event_Type = event['detail']['userIdentity']['type']

        if event_Type != "AssumedRole":
            # event로 넘어온 json 받아오기
            event_name = event['detail']['eventName']
            use_userName = event['detail']['userIdentity']['userName']
            instanceName = ""

            print("event : " + event_name)
            if event_name == "CreateImage":
                instanceName = event['detail']['requestParameters']['instanceId']
            elif event_name == "DeregisterImage":
                instanceName = event['detail']['requestParameters']['imageId']
            elif event_name == "CreateVolume":
                instanceName = event['detail']['responseElements']['volumeId']
            elif event_name == "DeleteVolume":
                instanceName = event['detail']['requestParameters']['volumeId']
            elif event_name == "AttachVolume" or event_name == "DetachVolume":
                instanceName = "볼륨 : " + event['detail']['requestParameters']['volumeId'] + "\n인스턴스 : " + \
                               event['detail']['requestParameters']['instanceId']
            elif event_name == "UpdateAutoScalingGroup":
                instanceName = event['detail']['requestParameters']['autoScalingGroupName']
            elif event_name == "DeleteAutoScalingGroup":
                instanceName = event['detail']['requestParameters']['autoScalingGroupName']
            elif event_name == "CreateSecurityGroup":
                instanceName = "그룹명 : " + event['detail']['requestParameters']['groupName'] + "\n그룹ID : " + \
                               event['detail']['responseElements']['groupId']
            elif event_name == "DeleteSecurityGroup":
                instanceName = "보안그룹ID : " + event['detail']['requestParameters']['groupId']
            elif event_name == "AuthorizeSecurityGroupIngress":
                instanceName = event['detail']['requestParameters']['groupId']
            else:
                instanceName = event['detail']['requestParameters']['instancesSet']

            eventName = ""
            scalingMax = 0
            scalingMin = 0
            scalingDesire = 0
            scalingString = " "

            if event_name == "StartInstances":
                eventName = "인스턴스(EC2) *시작*"
            elif event_name == "StopInstances":
                eventName = "인스턴스(EC2) *중지*"
            elif event_name == "RebootInstances":
                eventName = "인스턴스(EC2) *재부팅*"
            elif event_name == "TerminateInstances":
                eventName = "인스턴스(EC2) *종료*"
            elif event_name == "RunInstances":
                eventName = "인스턴스(EC2) *생성*"
                instanceName = event['detail']['responseElements']['instancesSet']
            elif event_name == "CreateImage":
                eventName = "EC2 AMI 생성"
            elif event_name == "DeregisterImage":
                eventName = "EC2 AMI 삭제"
            elif event_name == "CreateVolume":
                eventName = "EC2 볼륨 생성"
            elif event_name == "DeleteVolume":
                eventName = "EC2 볼륨 삭제"
            elif event_name == "AttachVolume":
                eventName = "EC2 볼륨 연결"
            elif event_name == "DetachVolume":
                eventName = "EC2 볼륨 분리"
            elif event_name == "UpdateAutoScalingGroup":
                eventName = "EC2 AutoScaling"
                scalingMax = event['detail']['requestParameters']['maxSize']
                scalingMin = event['detail']['requestParameters']['minSize']
                scalingDesire = event['detail']['requestParameters']['desiredCapacity']
                scalingString = "최대 용량 : " + str(scalingMax) + " 최소 용량 : " + str(scalingMin) + "\n원하는 용량 : " + str(
                    scalingDesire)
            elif event_name == "DeleteAutoScalingGroup":
                eventName = "EC2 AutoScaling Delete"
            elif event_name == "CreateSecurityGroup":
                eventName = "보안그룹생성"
            elif event_name == "DeleteSecurityGroup":
                eventName = "보안그룹삭제"
            else:
                eventName = "EC2"

            insName = ""

            if event_name != "CreateImage" and event_name != "DeregisterImage" and event_name != "CreateVolume" and event_name != "DeleteVolume" and event_name != "AttachVolume" and event_name != "DetachVolume" and event_name != "UpdateAutoScalingGroup" and event_name != "DeleteAutoScalingGroup" and event_name != "CreateSecurityGroup" and event_name != "DeleteSecurityGroup" and event_name != "AuthorizeSecurityGroupIngress":
                size = len(instanceName['items'])
                number = 0

                for i in instanceName['items']:
                    number = number + 1
                    if number != size:
                        insName = insName + i['instanceId'] + "\n"
                    else:
                        insName = insName + i['instanceId']
            else:
                insName = instanceName

            # slack 으로 보낼 메세지 설정
            slack_message = {
                "channel": SLACK_CHANNEL,
                "attachments": [{
                    "color": "#FF8C00",
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
                                "text": "*인스턴스*\n" + insName
                            },
                            {
                                "type": "mrkdwn",
                                "text": "*발생시간*\n" + nowDate
                            },
                            {
                                "type": "mrkdwn",
                                "text": scalingString
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