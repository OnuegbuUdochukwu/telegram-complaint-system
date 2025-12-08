
import os
import asyncio
from dotenv import load_dotenv
load_dotenv()

from client import submit_complaint

print(f"BACKEND_URL: {os.getenv('BACKEND_URL')}")

async def test_submission():
    payload = {
        "telegram_user_id": "123456789",
        "hostel": "John",
        "wing": "B",
        "room_number": "B301",
        "category": "carpentry",
        "description": "Chair not cherring",
        "severity": "medium"
    }
    try:
        print("Attempting submission...")
        response = await submit_complaint(payload)
        print(f"Submission successful: {response}")
    except Exception as e:
        print(f"Submission failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_submission())
