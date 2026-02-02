from Learning_hub.celery import app
from celery import shared_task
from django.contrib.auth import get_user_model
from core.cdn_helper import BunnyService
import os
import logging
import uuid
# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


@shared_task(bind=True, autoretry_for=(Exception,), retry_kwargs={"max_retries": 3, "countdown": 10})
def upload_avatar_task(self, user_id: int, local_path: str, remote_path: str):
    try:
        # Import here to avoid AppRegistryNotReady error
        User = get_user_model()

        user = User.objects.get(id=user_id)
        profile = user.profile

        # Delete existing avatar if it exists
        if profile.avatar_url:
            try:
                print(f"[Avatar] Deleting old avatar: {profile.avatar_url}")
                delete_file_by_cdn_url_task.delay(profile.avatar_url)
            except Exception as e:
                print(f"[Avatar] Error deleting old avatar: {e}")

        # Upload new avatar
        image_url = BunnyService._upload_to_storage(local_path, remote_path)

        # Save URL
        profile.avatar_url = image_url
        profile.save(update_fields=["avatar_url"])

        # Cleanup temp file
        if os.path.exists(local_path):
            os.remove(local_path)

        logger.info(f"[Avatar Upload] Task completed successfully")
        return image_url
    except Exception as e:
        logger.error(f"[Avatar Upload] Task failed: {str(e)}", exc_info=True)
        raise

@app.task(name="bunny_delete_file_by_cdn_url")
def delete_file_by_cdn_url_task(cdn_url):
    """Delete file from Bunny CDN by CDN URL."""
    logger.info(f"[File Delete] Starting file deletion")
    logger.info(f"[File Delete] CDN URL: {cdn_url}")
    
    try:
        result = BunnyService.delete_file_by_cdn_url(cdn_url)
        logger.info(f"[File Delete] Deletion successful")
        return result
    except Exception as e:

        logger.error(f"[File Delete] Task failed: {str(e)}", exc_info=True)
        raise

@app.task(name="upload_video_task")
def upload_video_task(local_path: str, title: str, lecture_id:uuid.UUID):
    """Upload video to Bunny CDN."""
    logger.info(f"[Video Upload] Starting video upload")
    logger.info(f"[Video Upload] Local Path: {local_path}")
    logger.info(f"[Video Upload] Title: {title}")
    
    try:
        video_url = BunnyService.upload_video(title=title, local_file_path=local_path)

        # Cleanup temp file
        if os.path.exists(local_path):
            os.remove(local_path)

        logger.info(f"[Video Upload] Upload successful")

        if lecture_id:
            from apps.courses.models import Lecture
            lecture = Lecture.objects.get(id=lecture_id)
            lecture.content_url = video_url
            lecture.save(update_fields=['content_url'])
        return video_url
    except Exception as e:
        logger.error(f"[Video Upload] Task failed: {str(e)}", exc_info=True)
        raise

@app.task(name="bunny_delete_video_by_cdn_url")
def delete_video_task(video_url):
    """Delete video from Bunny CDN by CDN URL."""
    logger.info(f"[Video Delete] Starting video deletion")
    logger.info(f"[Video Delete] CDN URL: {video_url}")
    
    try:
        result = BunnyService.delete_video(video_url)
        logger.info(f"[Video Delete] Deletion successful")
        return result
    except Exception as e:
        logger.error(f"[Video Delete] Task failed: {str(e)}", exc_info=True)
        raise