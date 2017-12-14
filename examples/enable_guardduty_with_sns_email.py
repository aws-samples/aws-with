import boto3
import json

##########################################################################

# Change the email address where you want GuardDuty alerts sent to
# Then run with: aws_with -R '*' python enable_guardduty_with_sns_email.py

SOC_EMAIL_ADDRESS="PUT_YOUR_EMAIL_ADDRESS_HERE"

##########################################################################


gd=boto3.client("guardduty")
sns=boto3.client("sns")
cwe=boto3.client("events")

# enable GuardDuty
gd.create_detector(Enable=True)

# create SNS topic and subscription
topic = sns.create_topic(Name="email-guardduty-alerts")["TopicArn"]
subscription=sns.subscribe(TopicArn=topic, Protocol="email", Endpoint=SOC_EMAIL_ADDRESS)

# Add CloudWatch Events Rule to trigger email
rule=cwe.put_rule(Name="guardduty-alerts", EventPattern='{"source":["aws.guardduty"]}')["RuleArn"]
target=[{"Id":"1","Arn":topic}]
cwe.put_targets(Rule="guardduty-alerts", Targets=target)

# Grant CloudWatch Events permission to publish to the topic
policy = {
  "Version": "2012-10-17",
  "Id": "__default_policy_ID",
  "Statement": [
    {
      "Sid": "__default_statement_ID",
      "Effect": "Allow",
      "Principal": {
        "AWS": "*"
      },
      "Action": [
        "SNS:GetTopicAttributes",
        "SNS:SetTopicAttributes",
        "SNS:AddPermission",
        "SNS:RemovePermission",
        "SNS:DeleteTopic",
        "SNS:Subscribe",
        "SNS:ListSubscriptionsByTopic",
        "SNS:Publish",
        "SNS:Receive"
      ],
      "Resource": topic,
      "Condition": {
        "StringEquals": {
          "AWS:SourceOwner": topic.split(":")[4]
        }
      }
    },
    {
      "Sid": "AWSEvents_guardduty-alerts_1",
      "Effect": "Allow",
      "Principal": {
        "Service": "events.amazonaws.com"
      },
      "Action": "sns:Publish",
      "Resource": topic
    }
  ]
}

policy=json.dumps(policy)
sns.set_topic_attributes(TopicArn=topic, AttributeName="Policy", AttributeValue=policy)
