
import asyncio
import os
import sys

# Add parent directory to path so we can import app
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from sqlmodel import select
from app.database import get_session
from app.models import Complaint, Photo
from app.config import get_settings

async def sync_photos():
    print("Starting photo sync...")
    async for session in get_session():
        # Get all complaints
        stmt = select(Complaint)
        result = await session.exec(stmt)
        complaints = result.all()
        
        updated_count = 0
        
        for complaint in complaints:
            # Get photos for this complaint
            p_stmt = select(Photo).where(Photo.complaint_id == complaint.id).order_by(Photo.created_at)
            p_result = await session.exec(p_stmt)
            photos = p_result.all()
            
            # Extract URLs
            photo_urls = [p.file_url for p in photos if p.file_url]
            
            # Update if different
            if complaint.photo_urls != photo_urls:
                complaint.photo_urls = photo_urls
                session.add(complaint)
                updated_count += 1
                
        if updated_count > 0:
            await session.commit()
            print(f"Updated {updated_count} complaints with photo URLs.")
        else:
            print("No complaints needed syncing.")
            
        break # Only run once

if __name__ == "__main__":
    asyncio.run(sync_photos())
