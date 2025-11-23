import os
os.environ["BACKEND_URL"] = "http://localhost:8000"
os.environ["BACKEND_SERVICE_TOKEN"] = "76bd085a412b5b70fa05e2c8c3f4b92f944425c7dfd355a9943aa0c52550d813"
from PIL import Image
import io
# generate small red JPEG
img = Image.new("RGB", (100,100), (255,0,0))
b = io.BytesIO()
img.save(b, format="JPEG")
img_bytes = b.getvalue()
# import client after env set
import client
# first create a complaint to attach photo to using submit_complaint
resp = client.submit_complaint({"telegram_user_id":"cli-photo","hostel":"John","room_number":"A101","category":"plumbing","description":"for photo test","severity":"low"})
print('submit response', resp)
complaint_id = resp.get('complaint_id')
print('complaint id:', complaint_id)
upload = client.upload_photo(complaint_id, img_bytes, 'test.jpg', mime_type='image/jpeg')
print('upload response:', upload)
