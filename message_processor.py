import redis
import time

def main():
    # Connect to Redis (default localhost:6379)
    r = redis.Redis(host='localhost', port=6379, db=0)
    queue_name = 'buy_alerts'  # Change this to your queue name

    print("Listening for messages... (Ctrl+C to stop)")
    try:
        while True:
            # BLPOP blocks until a message is available
            message = r.blpop(queue_name)
            if message:
                # log current time and message
                # message is a tuple: (queue_name, message_data)
                print(f"Received message at {time.strftime('%Y-%m-%d %H:%M:%S')}: {message[1].decode('utf-8')}")
    except KeyboardInterrupt:
        print("\nStopped listening.")

if __name__ == "__main__":
    main()