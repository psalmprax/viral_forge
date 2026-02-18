from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from api.utils.database import SessionLocal
from api.utils.models import VideoJobDB
from api.routes.auth import get_current_user
from api.utils.user_models import UserDB
from services.video_engine.tasks import download_and_process_task

router = APIRouter(prefix="/video", tags=["Video Engine"])

class TransformationRequest(BaseModel):
    input_url: str
    niche: str = "Motivation"
    platform: str = "YouTube Shorts"


@router.post("/transform")
async def start_transformation(request: TransformationRequest, current_user: UserDB = Depends(get_current_user)):
    """
    Triggers a background Celery task to download, process, and upload a video.
    """
    db = SessionLocal()
    try:
        task = download_and_process_task.delay(request.input_url, request.niche, request.platform)
        
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
    """
    Aborts a running transformation job by revoking the Celery task.
    """
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
