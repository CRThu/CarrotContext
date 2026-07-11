from fastapi import APIRouter, Depends

from app.auth.router import get_current_user
from app.lock.models import LockRequest, LockResponse, LockStatus
from app.lock.service import acquire_lock, get_lock_status, release_lock

router = APIRouter()


@router.post("", response_model=LockResponse)
async def acquire_lock_api(
    lock: LockRequest,
    current_user: dict = Depends(get_current_user),
):
    result = acquire_lock(
        lock.knowledge_id, lock.file_path, current_user["username"]
    )
    if not result["success"]:
        return LockResponse(
            success=False,
            locked_by=result["locked_by"],
            locked_at=result["locked_at"],
            message=f"文件已被 {result['locked_by']} 锁定",
        )
    return LockResponse(
        success=True,
        locked_by=current_user["username"],
        locked_at=result["locked_at"],
        message="锁定成功",
    )


@router.delete("", response_model=LockResponse)
async def release_lock_api(
    lock: LockRequest,
    current_user: dict = Depends(get_current_user),
):
    success = release_lock(
        lock.knowledge_id, lock.file_path, current_user["username"]
    )
    if not success:
        return LockResponse(
            success=False,
            message="释放锁失败，可能已被释放或无权释放",
        )
    return LockResponse(success=True, message="释放成功")


@router.get("/status", response_model=LockStatus)
async def get_lock_status_api(
    knowledge_id: str,
    file_path: str,
    current_user: dict = Depends(get_current_user),
):
    lock_data = get_lock_status(knowledge_id, file_path)
    if not lock_data:
        return LockStatus(
            knowledge_id=knowledge_id,
            file_path=file_path,
            locked=False,
        )
    return LockStatus(
        knowledge_id=knowledge_id,
        file_path=file_path,
        locked=True,
        locked_by=lock_data.get("username"),
        locked_at=lock_data.get("locked_at"),
    )
