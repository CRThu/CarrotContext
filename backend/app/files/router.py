from fastapi import APIRouter, Body, Depends, HTTPException, UploadFile, status
from fastapi.responses import Response

from app.auth.router import get_current_user
from app.knowledge.models import FileContent, FileMoveRequest, TreeNode
from app.knowledge.permissions import require_access
from app.files.service import (
    create_directory,
    get_binary_content,
    get_file_content,
    get_file_tree,
    is_binary_file,
    move_file,
    update_file_content,
    upload_file,
)

router = APIRouter()

# Maximum upload size: 10MB
MAX_UPLOAD_SIZE = 10 * 1024 * 1024


@router.get("/{knowledge_id}/tree", response_model=list[TreeNode])
async def get_tree_api(
    knowledge_id: str,
    path: str = "",
    current_user: dict = Depends(require_access("read")),
):
    return get_file_tree(knowledge_id, path)


@router.get("/{knowledge_id}/files/{file_path:path}/raw")
async def get_raw_file_api(
    knowledge_id: str,
    file_path: str,
    current_user: dict = Depends(require_access("read")),
):
    """Download a binary file"""
    content = get_binary_content(knowledge_id, file_path)
    if content is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文件不存在",
        )

    # Determine content type from extension
    ext = file_path.rsplit(".", 1)[-1].lower() if "." in file_path else ""
    content_types = {
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "gif": "image/gif",
        "svg": "image/svg+xml",
        "pdf": "application/pdf",
        "zip": "application/zip",
        "json": "application/json",
        "txt": "text/plain",
        "md": "text/markdown",
    }
    content_type = content_types.get(ext, "application/octet-stream")

    return Response(
        content=content,
        media_type=content_type,
        headers={"Content-Disposition": f'attachment; filename="{file_path.split("/")[-1]}"'},
    )


@router.get(
    "/{knowledge_id}/files/{file_path:path}",
    response_model=FileContent,
)
async def get_file_api(
    knowledge_id: str,
    file_path: str,
    current_user: dict = Depends(require_access("read")),
):
    content = get_file_content(knowledge_id, file_path)
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文件不存在",
        )
    return content


@router.put("/{knowledge_id}/files/{file_path:path}")
async def update_file_api(
    knowledge_id: str,
    file_path: str,
    content: str = Body(..., media_type="text/plain"),
    current_user: dict = Depends(require_access("write")),
):
    if not update_file_content(knowledge_id, file_path, content):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="更新失败",
        )
    return {"message": "更新成功"}


@router.post("/{knowledge_id}/dirs")
async def create_dir_api(
    knowledge_id: str,
    dir_path: str,
    current_user: dict = Depends(require_access("write")),
):
    if not create_directory(knowledge_id, dir_path):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="目录已存在",
        )
    return {"message": "创建成功"}


@router.post("/{knowledge_id}/files/move")
async def move_file_api(
    knowledge_id: str,
    request: FileMoveRequest,
    current_user: dict = Depends(require_access("write")),
):
    if not move_file(knowledge_id, request.source_path, request.dest_path):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="移动失败：文件不存在或目标无效",
        )
    return {"message": "移动成功"}


@router.post("/{knowledge_id}/files/upload")
async def upload_file_api(
    knowledge_id: str,
    file: UploadFile,
    path: str = "",
    current_user: dict = Depends(require_access("write")),
):
    """Upload a file to the knowledge base"""
    content = await file.read()
    if len(content) > MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"文件大小超过限制（最大 {MAX_UPLOAD_SIZE // (1024 * 1024)}MB）",
        )

    file_path = f"{path}/{file.filename}" if path else file.filename
    if not upload_file(knowledge_id, file_path, content):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="上传失败",
        )
    return {"message": "上传成功", "path": file_path}
