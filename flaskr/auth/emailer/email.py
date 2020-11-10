import boto3
from flask import current_app


def send_email(app, recipients, sender=None, subject='', text='', html=''):
    ses = boto3.client(
        'ses',
        region_name=app.config['SES_REGION_NAME'],
        aws_access_key_id=app.config['AWS_ACCESS_KEY_ID'],
        aws_secret_access_key=app.config['AWS_SECRET_ACCESS_KEY']
    )
    if not sender:
        sender = app.config['SES_EMAIL_SOURCE']

    result = ses.send_email(
            Source=sender,
            Destination={'ToAddresses': recipients},
            Message={
                'Subject': {'Data': subject},
                'Body': {
                    'Text': {'Data': text},
                    'Html': {'Data': html}
                }
            }
        )
    if result['ResponseMetadata']['HTTPStatusCode'] != 200:
        current_app.logger.error("Error sending confirmation email to: %s " % recipients)
