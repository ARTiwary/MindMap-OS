import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.db.redis import cache_delete_pattern
from app.models.tag import Tag
from app.models.user import User
from app.schemas.graph import TagCreate, TagUpdate
from app.schemas.node import TagOut

router = APIRouter(prefix="/tags", tags=["Tags"])

NOT_FOUND = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail={"error": {"code": "TAG_NOT_FOUND", "message": "The requested tag does not exist."}},
)


@router.get("", response_model=list[TagOut])
async def list_tags(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Tag).where(Tag.user_id == current_user.id).order_by(Tag.name))
    return result.scalars().all()


@router.post("", response_model=TagOut, status_code=status.HTTP_201_CREATED)
async def create_tag(
    payload: TagCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(
        select(Tag).where(Tag.user_id == current_user.id, Tag.name == payload.name)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": {"code": "TAG_EXISTS", "message": "A tag with this name already exists."}},
        )
    tag = Tag(user_id=current_user.id, name=payload.name, color=payload.color)
    db.add(tag)
    await db.commit()
    await db.refresh(tag)
    return tag


@router.patch("/{tag_id}", response_model=TagOut)
async def update_tag(
    tag_id: uuid.UUID,
    payload: TagUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Tag).where(Tag.id == tag_id, Tag.user_id == current_user.id))
    tag = result.scalar_one_or_none()
    if not tag:
        raise NOT_FOUND
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(tag, field, value)
    await db.commit()
    await db.refresh(tag)
    await cache_delete_pattern(f"dashboard:user:{current_user.id}*")
    return tag


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(
    tag_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Tag).where(Tag.id == tag_id, Tag.user_id == current_user.id))
    tag = result.scalar_one_or_none()
    if not tag:
        raise NOT_FOUND
    await db.delete(tag)
    await db.commit()
    await cache_delete_pattern(f"dashboard:user:{current_user.id}*")
    return None
