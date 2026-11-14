import json
import time
from collections import deque

import redis
from kafka import KafkaProducer

class HybridStreamBroker:
    """
    Uses real Redis & Apache Kafka if running on localhost;
    automatically falls back to in-memory structures for local Option B mode.
    """
    def __init__(self):
        self.redis_client = None
        self.kafka_producer = None
        self.local_cache = {}
        self.local_stream = deque(maxlen=5000)

        # Try connecting to Redis
        try:
            r = redis.Redis(host='127.0.0.1', port=6379, decode_responses=True, socket_connect_timeout=1)
            r.ping()
            self.redis_client = r
            print("[Broker] Connected to live Redis server on port 6379!")
        except Exception:
            print("[Broker] Redis not running -> Using ultra-fast in-memory cache mode.")

        # Try connecting to Apache Kafka
        try:
            self.kafka_producer = KafkaProducer(
                bootstrap_servers=['127.0.0.1:9092'],
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                request_timeout_ms=1500
            )
            print("[Broker] Connected to live Apache Kafka broker on port 9092!")
        except Exception:
            print("[Broker] Kafka not running -> Using local stream deque buffer mode.")

    def cache_rider_state(self, rider_code: str, state_dict: dict):
        state_dict["timestamp"] = time.time()
        if self.redis_client:
            self.redis_client.hset("fleet:live_riders", rider_code, json.dumps(state_dict))
        else:
            self.local_cache[rider_code] = state_dict

    def get_all_riders(self) -> list:
        if self.redis_client:
            raw = self.redis_client.hgetall("fleet:live_riders")
            return [json.loads(val) for val in raw.values()]
        return list(self.local_cache.values())

    def publish_event(self, topic: str, payload: dict):
        if self.kafka_producer:
            self.kafka_producer.send(topic, payload)
        self.local_stream.append(payload)

    def drain_batch(self, batch_size: int = 15) -> list:
        if len(self.local_stream) >= batch_size:
            batch = list(self.local_stream)
            self.local_stream.clear()
            return batch
        return []