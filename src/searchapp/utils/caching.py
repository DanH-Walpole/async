import redis
import json
import time
import logging
from faker import Faker

logger = logging.getLogger(__name__)

class RedisHelper:

    def __init__(self, host='localhost', port=6379, db=0):
        # Initialize Redis connection
        self.redis_client = redis.StrictRedis(
            host=host,
            port=port,
            db=db,
            decode_responses=True  # Ensures values are returned as strings
        )
    
    def connectionStatus(self):
        # Check if the connection is successful
        try:
            return self.redis_client.ping()
        except redis.ConnectionError:
            return False
    
    def store(self, key: str, value: str):
        # Store the result in Redis with the key
        self.redis_client.set(key, value)

    def lookup(self, key: str) -> str:
        # Look up the key in Redis
        start_time = time.time()
        result = self.redis_client.get(key)
        time_taken_ms = (time.time() - start_time) * 1000
        # show the time taken to retrieve the key in milliseconds
        logger.info(f"Time taken to retrieve key in ms: {time_taken_ms}")
        return result
    
    def exists(self, key: str) -> bool:
        # Check if the key exists in Redis
        return self.redis_client.exists(key)
    
    def get_size(self) -> int:
        # Get the number of keys in the Redis database
        return self.redis_client.dbsize()

    def delete(self, key: str):
        # Optionally implement a delete method if you want to invalidate cache
        self.redis_client.delete(key)

    def flush(self):
        # Clears all keys in the Redis database (use with caution)
        logger.info("Flushing Redis database...")
        self.redis_client.flushdb()

    def populate_dummy_data(self, num_entries: int):
        # Use Faker to generate dummy data
        fake = Faker()

        for i in range(num_entries):
            # Generate a unique key and a random value
            key = f"user:{i}"
            value = {
                "name": fake.name(),
                "email": fake.email(),
                "address": fake.address(),
                "phone_number": fake.phone_number(),
            }
            # Store the value as a JSON string
            self.store(key, json.dumps(value))
        
        logger.info(f"Inserted {num_entries} key-value pairs into Redis.")