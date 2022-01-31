import os
import requests
from pykafka import KafkaClient
import logging.config
import yaml

with open('consumer_log.yaml', 'r') as stream:
    config = yaml.load(stream, Loader=yaml.FullLoader)
logging.config.dictConfig(config)
logger = logging.getLogger('consumer')

password = os.getenv('FASTAPI_PASSWORD')
client = KafkaClient(hosts="10.1.0.111:9092")

consumer = client.topics["topic-notice"].get_simple_consumer(
    consumer_group="mygroup",
    reset_offset_on_start=False)

for idx, message in enumerate(consumer):
    logger.debug('received %s' % (message))
    decoded_user_id = int.from_bytes(message.value, byteorder='big')
    logger.info('the consumer has successfully received user_id: %s' % (decoded_user_id))
    # send_notice(decoded_user_id)
    response_post = requests.post(
        "http://fastapi:8080/send_user_id",
        json={
            "user_id": decoded_user_id,
            "password": password
        })

    logger.info('send result user_id: %s, index: %s, status_code: %s, text: %s' % (decoded_user_id, idx, response_post.status_code, response_post.text))
    if response_post.ok:
        consumer.commit_offsets()
    else:
        logger.fatal('cannot send result user_id: %s, index: %s, status_code: %s, text: %s' % (decoded_user_id, idx, response_post.status_code, response_post.text))
