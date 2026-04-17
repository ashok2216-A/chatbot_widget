import requests
import concurrent.futures
import time
import argparse
import sys

def parse_args():
    parser = argparse.ArgumentParser(description="Stress Test the Live RAG Chatbot Endpoint.")
    parser.add_argument("--url", default="https://portfolio-backend-93ck.onrender.com/chat", help="Target API URL")
    parser.add_argument("--users", type=int, default=5, help="Number of concurrent users")
    parser.add_argument("--iterations", type=int, default=1, help="Number of requests per user")
    parser.add_argument("--message", default="tell me about your python skills", help="Query to send")
    parser.add_argument("--origin", default="https://ashok2216-a.github.io", help="Origin header for CORS spoofing")
    return parser.parse_args()

import random

# A pool of common questions recruiters or visitors might ask
REAL_WORLD_QUERIES = [
    "Tell me about your Python experience",
    "What kind of projects have you built?",
    "Do you know React or frontend technologies?",
    "Where did you go to school?",
    "What is your email or contact info?",
    "Give me a summary of your skills"
]

def simulate_user(user_id, target_url, origin, iterations):
    session_times = []
    success_count = 0
    failure_count = 0
    
    headers = {
        "Origin": origin,
        "Content-Type": "application/json"
    }
    
    # Simulate staggered arrivals (Users don't all click your link at the exact same millisecond)
    arrival_delay = random.uniform(0.1, 5.0)
    time.sleep(arrival_delay)
    
    for i in range(iterations):
        # Pick a random question
        query = random.choice(REAL_WORLD_QUERIES)
        
        payload = {
            "message": query,
            "session_id": f"organic_visitor_{user_id}_{int(time.time())}"
        }
        
        start_time = time.time()
        try:
            response = requests.post(target_url, json=payload, headers=headers, timeout=20)
            latency = time.time() - start_time
            if response.status_code == 200:
                success_count += 1
                if i == 0:
                    print(f"✅ [User {user_id}] Connected & Answered '{query[:20]}...' in {latency:.2f}s")
            else:
                print(f"❌ [User {user_id}] Failed with Status {response.status_code}: {response.text}")
                failure_count += 1
        except Exception as e:
            latency = time.time() - start_time
            print(f"⚠️ [User {user_id}] Connection Error (Timeout/Throttled): {str(e)}")
            failure_count += 1
            
        session_times.append(latency)
        
        # Simulate the user reading the answer and typing another question (3 to 8 seconds delay)
        if i < iterations - 1:
            typing_delay = random.uniform(3.0, 8.0)
            time.sleep(typing_delay)
            
    return {
        "user_id": user_id,
        "avg_latency": sum(session_times) / len(session_times) if session_times else 0,
        "success_count": success_count,
        "failure_count": failure_count
    }

def main():
    args = parse_args()
    print(f"Starting Stress Test against: {args.url}")
    print(f"Concurrent Users: {args.users}")
    print(f"Requests per User: {args.iterations}")
    print("-" * 50)
    
    start_time = time.time()
    
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.users) as executor:
        futures = [
            executor.submit(simulate_user, i, args.url, args.origin, args.iterations)
            for i in range(args.users)
        ]
        
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())
            
    total_time = time.time() - start_time
    
    total_success = sum(r["success_count"] for r in results)
    total_failure = sum(r["failure_count"] for r in results)
    avg_latency = sum(r["avg_latency"] for r in results) / len(results) if results else 0
    
    print("-" * 50)
    print("** Stress Test Results **")
    print(f"Total Time Elapsed : {total_time:.2f} seconds")
    print(f"Total Successes    : {total_success}")
    print(f"Total Failures     : {total_failure}")
    print(f"Global Avg Latency : {avg_latency:.2f} seconds per query")
    print("-" * 50)

if __name__ == "__main__":
    main()
