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
    requests.post(
        "http://fastapi:8080/my_send_notice",
        json={
            "user_id": decoded_user_id,
            "password": password
        })
    logger.info('user_id: %s, index: %s' % (decoded_user_id, idx))
    consumer.commit_offsets()
