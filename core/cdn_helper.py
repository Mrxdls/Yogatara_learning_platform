import requests
import uuid
import os
import time
import hmac
import hashlib
import base64
import logging
from urllib.parse import urlparse

from django.conf import settings

# Configure logging for Celery
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)



class BunnyService:
    # ============ CONFIG (from environment variables) ============
    BUNNY_STORAGE_ZONE = settings.BUNNY_STORAGE_ZONE
    BUNNY_STORAGE_API_KEY = settings.BUNNY_STORAGE_API_KEY
    BUNNY_STORAGE_ENDPOINT = settings.BUNNY_STORAGE_ENDPOINT
    CDN_BASE_URL = settings.CDN_BASE_URL

    BUNNY_STREAM_LIBRARY_ID = settings.BUNNY_STREAM_LIBRARY_ID
    BUNNY_STREAM_API_KEY = settings.BUNNY_STREAM_API_KEY
    BUNNY_STREAM_TOKEN_SECRET = settings.BUNNY_STREAM_TOKEN_SECRET

    # ============ INTERNAL HELPERS ============

    @classmethod
    def _upload_to_storage(cls, file_or_path, remote_path):
        """Upload a file to Bunny Storage. Debugs config on error."""
        url = f"{cls.BUNNY_STORAGE_ENDPOINT}/{cls.BUNNY_STORAGE_ZONE}/{remote_path}"
        headers = {
            "AccessKey": cls.BUNNY_STORAGE_API_KEY,
            "Content-Type": "application/octet-stream"
        }
        if isinstance(file_or_path, (str, bytes, os.PathLike)):
            with open(file_or_path, "rb") as f:
                resp = requests.put(url, data=f, headers=headers)
        else:
            file_or_path.seek(0)
            resp = requests.put(url, data=file_or_path, headers=headers)
        if resp.status_code not in [200, 201]:
            raise Exception(f"Bunny upload failed: {resp.status_code} {resp.text}")
        return f"{cls.CDN_BASE_URL}/{remote_path}"

    @staticmethod
    def _generate_safe_filename(original_name):
        #repalce spaces with underscores and remove special characters
        name, ext = os.path.splitext(original_name)
        safe_name = "".join(c if c.isalnum() or c in (' ', '.', '_') else '_' for c in name)
        safe_name = safe_name.replace(" ", "_")
        return f"{safe_name}{ext}"
    
    

    @staticmethod
    def _extract_storage_path_from_cdn_url(cdn_url):
        """Extract storage path from CDN URL for deletion.
        
        Example:
        Input: https://mridul-testing.b-cdn.net/uploads/avatars/user_123_file.jpg
        Output: uploads/avatars/user_123_file.jpg
        """
        parsed = urlparse(cdn_url)
        storage_path = parsed.path.lstrip("/")  # remove leading /
        print(f"[Bunny DEBUG] CDN URL: {cdn_url}")
        print(f"[Bunny DEBUG] Parsed path: {parsed.path}")
        print(f"[Bunny DEBUG] Storage path (stripped): {storage_path}")
        return storage_path

    # ============ IMAGES & DOCUMENTS ============

    @classmethod
    def upload_image(cls, file_path, original_name, user_id=None):
        if user_id:
            ext = os.path.splitext(original_name)[1]
            filename = f"user_{user_id}_{uuid.uuid4().hex}{ext}"
        else:
            filename = cls._generate_safe_filename(original_name)

        remote_path = f"uploads/images/{filename}"

        from core.cdn_helper import upload_to_storage_task
        return upload_to_storage_task.delay(file_path, remote_path)

    

    @classmethod
    def upload_document(cls, local_file_path, original_name):
        filename = cls._generate_safe_filename(original_name)
        remote_path = f"uploads/documents/{filename}"
        from core.cdn_helper import upload_to_storage_task
        return upload_to_storage_task.delay(local_file_path, remote_path)

    @classmethod
    def delete_file_by_cdn_url(cls, cdn_url):
        """Delete file from Bunny Storage via CDN URL."""
        storage_path = cls._extract_storage_path_from_cdn_url(cdn_url)
        url = f"{cls.BUNNY_STORAGE_ENDPOINT}/{cls.BUNNY_STORAGE_ZONE}/{storage_path}"
        headers = {
            "AccessKey": cls.BUNNY_STORAGE_API_KEY
        }
        resp = requests.delete(url, headers=headers)
        if resp.status_code not in [200, 204]:
            raise Exception(f"Failed to delete file: {resp.status_code} {resp.text}")
        return True

    # ============ VIDEO (BUNNY STREAM) ============

    @classmethod
    def upload_video(cls, title, local_file_path):
        # Step 1: Create video
        create_url = f"https://video.bunnycdn.com/library/{cls.BUNNY_STREAM_LIBRARY_ID}/videos"
        headers = {
            "AccessKey": cls.BUNNY_STREAM_API_KEY,
            "Content-Type": "application/json"
        }
        resp = requests.post(create_url, json={"title": title}, headers=headers)
        if resp.status_code != 200:
            raise Exception(f"Failed to create video: {resp.text}")
        video_id = resp.json()["guid"]
        # Step 2: Upload binary
        upload_url = f"https://video.bunnycdn.com/library/{cls.BUNNY_STREAM_LIBRARY_ID}/videos/{video_id}"
        headers = {
            "AccessKey": cls.BUNNY_STREAM_API_KEY,
            "Content-Type": "application/octet-stream"
        }
        with open(local_file_path, "rb") as f:
            resp = requests.put(upload_url, data=f, headers=headers)
        if resp.status_code != 200:
            raise Exception(f"Failed to upload video file: {resp.text}")
        return video_id

    @classmethod
    def delete_video(cls, video_id):
        url = f"https://video.bunnycdn.com/library/{cls.BUNNY_STREAM_LIBRARY_ID}/videos/{video_id}"
        headers = {
            "AccessKey": cls.BUNNY_STREAM_API_KEY
        }
        resp = requests.delete(url, headers=headers)
        if resp.status_code != 200:
            raise Exception(f"Failed to delete video: {resp.text}")
        return True

    # ============ STREAM LINK ============

    @classmethod
    def get_streaming_link(cls, video_id, expires_in_seconds=300):
        expires = int(time.time()) + expires_in_seconds
        path = f"/embed/{cls.BUNNY_STREAM_LIBRARY_ID}/{video_id}"
        security_string = f"{path}{expires}"
        signature = base64.urlsafe_b64encode(
            hmac.new(
                cls.BUNNY_STREAM_TOKEN_SECRET.encode(),
                security_string.encode(),
                hashlib.sha256
            ).digest()
        ).decode().rstrip("=")
        stream_url = f"https://iframe.mediadelivery.net{path}?token={signature}&expires={expires}"
        return stream_url

    # ============ VIDEO LIST & DETAILS ============

    @classmethod
    def list_videos(cls, page=1, per_page=100):
        url = f"https://video.bunnycdn.com/library/{cls.BUNNY_STREAM_LIBRARY_ID}/videos?page={page}&itemsPerPage={per_page}"
        headers = {
            "AccessKey": cls.BUNNY_STREAM_API_KEY
        }
        resp = requests.get(url, headers=headers)
        if resp.status_code != 200:
            raise Exception(f"Failed to list videos: {resp.text}")
        return resp.json()

    @classmethod
    def get_video_details(cls, video_id):
        url = f"https://video.bunnycdn.com/library/{cls.BUNNY_STREAM_LIBRARY_ID}/videos/{video_id}"
        headers = {
            "AccessKey": cls.BUNNY_STREAM_API_KEY
        }
        resp = requests.get(url, headers=headers)
        if resp.status_code != 200:
            raise Exception(f"Failed to get video details: {resp.text}")
        data = resp.json()
        return data


# ========== Celery Standalone Tasks ==========
from Learning_hub.celery import app

@app.task(name="bunny_upload_to_storage")
def upload_to_storage_task(file_or_path, remote_path):
    return BunnyService._upload_to_storage(file_or_path, remote_path)


