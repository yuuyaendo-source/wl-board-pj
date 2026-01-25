import json
import boto3
import time
import os

# SQSキューのURLを設定
SQS_QUEUE_URL = os.environ['SQS_QUEUE_URL'] 

sqs = boto3.client('sqs')

def poll_sqs_queue():
    print("Polling SQS queue...")
    try:
        response = sqs.receive_message(
            QueueUrl=SQS_QUEUE_URL,
            MaxNumberOfMessages=1,
            WaitTimeSeconds=20
        )

        messages = response.get('Messages', [])
        if not messages:
            print("No new messages.")
            return

        for message in messages:
            body = json.loads(message['Body'])
            
            # Verkadaのペイロードから`notification_type`と`person_label`を抽出
            webhook_data = json.loads(body['body'])
            event_data = webhook_data['data']
            event_type = event_data['notification_type']

            if event_type == 'person':
                person_label = event_data['person_label']
                
                if person_label:
                    print(f"--- Registered person detected: {person_label} ---")
                    # 例: "〇〇さん、いらっしゃいませ！"と挨拶させる
                    # vtuber_greet_known_person(person_label)
                else:
                    print("--- Unknown person detected ---")
                    # 例: "いらっしゃいませ！"と一般的な挨拶をさせる
                    # vtuber_greet_unknown_person()
            else:
                print(f"--- Other event detected: {event_type} ---")

            # メッセージをキューから削除
            sqs.delete_message(
                QueueUrl=SQS_QUEUE_URL,
                ReceiptHandle=message['ReceiptHandle']
            )

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == '__main__':
    while True:
        poll_sqs_queue()