from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from api.utils.database import SessionLocal
from api.utils.models import VideoJobDB
from api.routes.auth import get_current_user
from api.utils.user_models import UserDB
from services.video_engine.tasks import download_and_process_task
import logging

router = APIRouter(prefix="/video", tags=["Video Engine"])

class TransformationRequest(BaseModel):
    input_url: str
    niche: str = "Motivation"
    platform: str = "YouTube Shorts"
    style: Optional[str] = "Default"


@router.post("/transform")
async def start_transformation(request: TransformationRequest, current_user: UserDB = Depends(get_current_user)):
    """
    Triggers a background Celery task to download, process, and upload a video.
    """
    db = SessionLocal()
    try:
        task = download_and_process_task.delay(
            source_url=request.input_url,
            niche=request.niche,
            platform=request.platform,
            style=request.style
        )
        
        # Create Job Entry in Database
        new_job = VideoJobDB(
            id=task.id,
            title=f"Viral Transform - {request.niche}",
            status="Queued",
            progress=0,
            input_url=request.input_url,
            user_id=current_user.id
        )
        db.add(new_job)
        db.commit()
        
        return {
            "message": "Transformation started in background", 
            "task_id": task.id,
            "status": "Queued"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@router.get("/jobs")
async def list_jobs(current_user: UserDB = Depends(get_current_user)):
    """
    Lists all video processing jobs from the database for the current user.
    """
    db = SessionLocal()
    try:
        # User isolation: Only see their own jobs unless admin
        query = db.query(VideoJobDB)
        if current_user.role != "admin":
            query = query.filter(VideoJobDB.user_id == current_user.id)
            
        jobs = query.order_by(VideoJobDB.created_at.desc()).all()
        return jobs
    finally:
        db.close()
@router.post("/jobs/{job_id}/abort")
async def abort_job(job_id: str, current_user: UserDB = Depends(get_current_user)):
    # ... (rest of the abort_job code)
    from api.utils.celery import celery_app
    db = SessionLocal()
    try:
        job = db.query(VideoJobDB).filter(VideoJobDB.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # User isolation
        if current_user.role != "admin" and job.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to abort this job")

        # Revoke Celery Task
        celery_app.control.revoke(job_id, terminate=True)
        
        # Update Database
        job.status = "Aborted"
        db.commit()

        # Notify Dashboard via WebSocket
        from api.routes.ws import notify_job_update_sync
        notify_job_update_sync({
            "id": job_id,
            "status": "Aborted",
            "progress": job.progress,
            "output_path": job.output_path
        })

        return {"status": "Aborted", "message": f"Job {job_id} revocation signal transmitted."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

class TestDriveRequest(BaseModel):
    niche: str
    style: Optional[str] = "Default"

@router.post("/test-drive")
async def test_drive(request: TestDriveRequest, current_user: UserDB = Depends(get_current_user)):
    """
    Identifies the top viral candidate for a niche and triggers a preview-only transformation.
    """
    from services.discovery.service import base_discovery_service
    from api.utils.models import ContentCandidateDB
    
    db = SessionLocal()
    try:
        # 1. Find top candidate with strict guardrails
        # - Must have a thumbnail
        # - Must have a niche
        # - Order by viral score
        candidate = db.query(ContentCandidateDB).filter(
            ContentCandidateDB.niche == request.niche,
            ContentCandidateDB.thumbnail_url.isnot(None),
            ContentCandidateDB.thumbnail_url != ""
        ).order_by(ContentCandidateDB.viral_score.desc()).first()
        
        if not candidate:
            # Try a quick scan if none found
            logging.info(f"[TestDrive] No valid candidates with thumbnails found for {request.niche}. Triggering scan...")
            trends = await base_discovery_service.find_trending_content(request.niche, horizon="30d")
            if trends:
                candidate = db.query(ContentCandidateDB).filter(
                    ContentCandidateDB.niche == request.niche,
                    ContentCandidateDB.thumbnail_url.isnot(None),
                    ContentCandidateDB.thumbnail_url != ""
                ).order_by(ContentCandidateDB.viral_score.desc()).first()
        
        if not candidate:
            raise HTTPException(
                status_code=404, 
                detail=f"No high-quality video candidates with thumbnails found for {request.niche}. Please try again in a few minutes after the scanners update."
            )

        # 2. Trigger Preview Task
        task = download_and_process_task.delay(
            source_url=candidate.url,
            niche=request.niche,
            platform="YouTube Shorts", # Default format for test drive
            preview_only=True,
            style=request.style
        )

        # 3. Create Job Entry
        new_job = VideoJobDB(
            id=task.id,
            title=f"Test Drive - {request.niche}",
            status="Queued",
            progress=0,
            input_url=candidate.url,
            user_id=current_user.id
        )
        db.add(new_job)
        db.commit()

        return {
            "message": "Test Drive started",
            "task_id": task.id,
            "candidate": {
                "id": candidate.id,
                "title": candidate.title,
                "url": candidate.url
            }
        }
    except Exception as e:
        import traceback
        logging.error(f"[TestDrive] Error: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
