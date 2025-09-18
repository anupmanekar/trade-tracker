import redis

# Connect to local Redis server
r = redis.Redis(host='localhost', port=6379, db=0)

# Set a test message
r.set('test_key', 'Hello, Redis!')

# Retrieve the test message
message = r.get('test_key')
print(f"Received from Redis: {message.decode('utf-8')}")