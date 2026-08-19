# -*- coding: utf-8 -*-
import asyncio
from datetime import date as DateType, datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query
from app.config import settings
from pydantic import BaseModel
from sqlalchemy import delete, select, update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import BoardPlacement, BoardType, StickyNote, User
from app.models.board_placement import Lane
from app.schemas.board_placement import BoardPlacementResponse, MoveToPersonalBody
from app.schemas.sticky_note import (
    CopyToTeamBody,
    CopyToTeamResponse,
    ImportFromPostitBody,
    ImportFromPostitResponse,
    StickyNoteCreate,
    StickyNoteResponse,
    StickyNoteUpdate,
)

router = APIRouter(prefix="/sticky_notes", tags=["sticky_notes"])


def _get_jst_today() -> DateType:
    """JST基準の現在日付を取得"""
    return datetime.now(ZoneInfo("Asia/Tokyo")).date()


async def apply_due_date_rules_for_note(note_id: int, db: AsyncSession) -> None:
    """改善計画6に基づく期限連動移動ロジック:
    - DONE レーンにある配置は絶対に対象外（何もしない）
    - is_manually_moved_to_today が True の配置は判定をスキップ
    - days <= 0 (期限切れ・今日): TODAY
    - 0 < days < 30 (短期): [1, 2, 3, 4, 5, 10, 20] 日前なら TODAY、それ以外は INBOX
    - days >= 30 (長期): days % 30 == 0 なら TODAY、それ以外は INBOX
    """
    result = await db.execute(select(StickyNote).where(StickyNote.id == note_id))
    note = result.scalar_one_or_none()
    if not note:
        return

    placements_res = await db.execute(
        select(BoardPlacement).where(
            BoardPlacement.note_id == note_id,
            BoardPlacement.board_type == BoardType.PERSONAL,
        )
    )
    placements = list(placements_res.scalars().all())
    if not placements:
        return

    today = _get_jst_today()

    for p in placements:
        # DONE レーンにあるタスクは期限切れであっても移動しない
        if p.lane == Lane.DONE or p.lane == "DONE":
            continue
        # 手動移動済みフラグが ON の場合はスキップ
        if p.is_manually_moved_to_today:
            continue

        if not note.due_date:
            # 期限がクリアされた場合、TODAY にあれば INBOX に戻す
            if p.lane == Lane.TODAY:
                p.lane = Lane.INBOX
            continue

        days = (note.due_date - today).days

        should_be_today = False
        if days <= 0:
            should_be_today = True
        elif days < 30:
            if days in [1, 2, 3, 4, 5, 10, 20]:
                should_be_today = True
        else:
            if days % 30 == 0:
                should_be_today = True

        p.lane = Lane.TODAY if should_be_today else Lane.INBOX

    await db.flush()


def _note_response(note: StickyNote) -> StickyNoteResponse:
    due_date_str = (
        note.due_date.isoformat() if getattr(note, "due_date", None) else None
    )
    return StickyNoteResponse(
        id=note.id,
        content=note.content,
        author_id=note.author_id,
        status=note.status,
        postit_board_id=note.postit_board_id,
        postit_note_id=note.postit_note_id,
        due_date=due_date_str,
        created_at=note.created_at,
        updated_at=note.updated_at,
    )


@router.get("", response_model=list[StickyNoteResponse])
async def get_sticky_notes(
    board_type: BoardType | None = Query(None),
    owner_id: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(StickyNote)
    if board_type or owner_id is not None:
        stmt = stmt.join(BoardPlacement, StickyNote.id == BoardPlacement.note_id)
        if board_type:
            stmt = stmt.where(BoardPlacement.board_type == board_type)
        if owner_id is not None:
            stmt = stmt.where(BoardPlacement.owner_id == owner_id)
    result = await db.execute(stmt)
    notes = result.scalars().all()
    return [_note_response(n) for n in notes]


@router.post("/import_from_postit", response_model=ImportFromPostitResponse)
async def import_from_postit(
    body: ImportFromPostitBody, db: AsyncSession = Depends(get_db)
):
    import_count = 0
    skip_count = 0

    for item in body.items:
        parsed_due_date = None
        if item.due_date:
            try:
                parsed_due_date = DateType.fromisoformat(item.due_date)
            except ValueError:
                pass

        result = await db.execute(
            select(StickyNote).where(
                StickyNote.postit_board_id == body.board_id,
                StickyNote.postit_note_id == str(item.id),
            )
        )
        existing_note = result.scalar_one_or_none()

        if existing_note:
            # 既存付箋で due_date が変更されている場合は更新
            if item.due_date is not None and existing_note.due_date != parsed_due_date:
                existing_note.due_date = parsed_due_date
                await db.flush()
                await apply_due_date_rules_for_note(existing_note.id, db)
            skip_count += 1
            continue

        note = StickyNote(
            content=item.text or "（テキストなし）",
            postit_board_id=body.board_id,
            postit_note_id=str(item.id),
            due_date=parsed_due_date,
        )
        db.add(note)
        await db.flush()

        placement = BoardPlacement(
            note_id=note.id,
            board_type=BoardType.TASK,
            matrix_quadrant=1,
            sort_order=0,
            placement_source="postit",
        )
        db.add(placement)

        if parsed_due_date:
            await apply_due_date_rules_for_note(note.id, db)

        import_count += 1

    await db.commit()
    return ImportFromPostitResponse(created=import_count, skipped=skip_count)


@router.post("", response_model=StickyNoteResponse, status_code=201)
async def create_sticky_note(
    body: StickyNoteCreate, db: AsyncSession = Depends(get_db)
):
    parsed_due_date = None
    if body.due_date:
        try:
            parsed_due_date = DateType.fromisoformat(body.due_date)
        except ValueError:
            raise HTTPException(
                status_code=422,
                detail="due_date は YYYY-MM-DD 形式で指定してください",
            )

    note = StickyNote(
        content=body.content,
        author_id=body.author_id,
        postit_board_id=body.postit_board_id,
        postit_note_id=body.postit_note_id,
        due_date=parsed_due_date,
    )
    db.add(note)
    await db.flush()

    placement = BoardPlacement(
        note_id=note.id,
        board_type=BoardType.MAIN,
        owner_id=None,
        lane=None,
        sort_order=0,
    )
    db.add(placement)
    await db.flush()

    from app.services.orchestrator import process_new_note_ai

    await process_new_note_ai(note.id, db)
    await apply_due_date_rules_for_note(note.id, db)
    await db.commit()
    await db.refresh(note)
    return _note_response(note)


class CreatePersonalNoteBody(BaseModel):
    owner_id: int
    content: str
    due_date: str | None = None


@router.post("/create_personal", response_model=StickyNoteResponse, status_code=201)
async def create_personal_note(
    body: CreatePersonalNoteBody, db: AsyncSession = Depends(get_db)
):
    """パーソナルボードから直接付箋を作成する。初期レーンは INBOX（期限が今日以前なら TODAY）"""
    result = await db.execute(select(User).where(User.id == body.owner_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    parsed_due_date = None
    if body.due_date:
        try:
            parsed_due_date = DateType.fromisoformat(body.due_date)
        except ValueError:
            raise HTTPException(
                status_code=422,
                detail="due_date は YYYY-MM-DD 形式で指定してください",
            )

    note = StickyNote(
        content=body.content,
        author_id=body.owner_id,
        postit_board_id=None,
        postit_note_id=None,
        due_date=parsed_due_date,
    )
    db.add(note)
    await db.flush()

    initial_lane = Lane.INBOX
    if parsed_due_date and parsed_due_date <= _get_jst_today():
        initial_lane = Lane.TODAY

    placement = BoardPlacement(
        note_id=note.id,
        board_type=BoardType.PERSONAL,
        owner_id=body.owner_id,
        lane=initial_lane,
        sort_order=0,
    )
    db.add(placement)
    await db.flush()

    from app.services.orchestrator import process_new_note_ai

    await process_new_note_ai(note.id, db)
    await apply_due_date_rules_for_note(note.id, db)
    await db.commit()
    await db.refresh(note)
    return _note_response(note)


class SyncFromPostitBody(BaseModel):
    board_id: str
    note_id: str
    content: str | None = None
    due_date: str | None = None


@router.patch("/sync_from_postit", response_model=StickyNoteResponse)
async def sync_from_postit(
    body: SyncFromPostitBody, db: AsyncSession = Depends(get_db)
):
    """付箋ボード側で追記・更新された content / due_date を反映"""
    result = await db.execute(
        select(StickyNote).where(
            StickyNote.postit_board_id == body.board_id,
            StickyNote.postit_note_id == body.note_id,
        )
    )
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(
            status_code=404, detail="No sticky note linked to this postit note"
        )

    if body.content is not None:
        note.content = body.content

    if body.due_date is not None:
        parsed_due_date = None
        if body.due_date != "":
            try:
                parsed_due_date = DateType.fromisoformat(body.due_date)
            except ValueError:
                pass
        if note.due_date != parsed_due_date:
            note.due_date = parsed_due_date
            await db.execute(
                sa_update(BoardPlacement)
                .where(BoardPlacement.note_id == note.id)
                .values(is_manually_moved_to_today=False)
            )
            await db.flush()
            await apply_due_date_rules_for_note(note.id, db)

    await db.commit()
    await db.refresh(note)
    return _note_response(note)


@router.get("/{note_id}", response_model=StickyNoteResponse)
async def get_sticky_note(note_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(StickyNote).where(StickyNote.id == note_id))
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="Sticky note not found")
    return _note_response(note)


def _notify_postit_note(
    board_id: str,
    note_id: str,
    text: str | None = None,
    due_date: str | None = None,
) -> None:
    """付箋ボード (wl-sticky-note) へ content / due_date の変更を通知"""
    import json
    import urllib.request
    from app.config import settings

    url = (
        f"{settings.postit_board_url.rstrip('/')}/api/boards/{board_id}/notes/{note_id}"
    )
    payload = {}
    if text is not None:
        payload["text"] = text
    if due_date is not None:
        payload["due_date"] = due_date

    if not payload:
        return

    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="PATCH")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            pass
    except Exception:
        pass


@router.patch("/{note_id}", response_model=StickyNoteResponse)
async def update_sticky_note(
    note_id: int, body: StickyNoteUpdate, db: AsyncSession = Depends(get_db)
):
    """付箋の content / status / due_date を更新。
    - due_date 変更時、is_manually_moved_to_today フラグを False に一括リセット
    - 改善計画6のルールに従い、パーソナル配置のレーンを自動判定して移動
    - 付箋ボード（wl-sticky-note）へ content / due_date の変更を通知
    """
    result = await db.execute(select(StickyNote).where(StickyNote.id == note_id))
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="Sticky note not found")

    if body.content is not None:
        note.content = body.content
    if body.status is not None:
        note.status = body.status

    due_date_changed = False
    if body.due_date is not None:
        if body.due_date == "":
            if note.due_date is not None:
                note.due_date = None
                due_date_changed = True
        else:
            try:
                parsed_date = DateType.fromisoformat(body.due_date)
            except ValueError:
                raise HTTPException(
                    status_code=422,
                    detail="due_date は YYYY-MM-DD 形式で指定してください",
                )
            if note.due_date != parsed_date:
                note.due_date = parsed_date
                due_date_changed = True

    await db.flush()

    if due_date_changed:
        # 手動移動フラグの一括リセット（改善計画6）
        await db.execute(
            sa_update(BoardPlacement)
            .where(BoardPlacement.note_id == note_id)
            .values(is_manually_moved_to_today=False)
        )
        await db.flush()
        # 最新の due_date に基づきパーソナル配置のレーンルールを適用
        await apply_due_date_rules_for_note(note_id, db)

    await db.commit()
    await db.refresh(note)

    # 付箋ボード (wl-sticky-note) への通知同期
    if note.postit_board_id and note.postit_note_id:
        text_to_send = note.content if body.content is not None else None
        due_date_to_send = (
            (note.due_date.isoformat() if note.due_date else "")
            if body.due_date is not None
            else None
        )
        if text_to_send is not None or due_date_to_send is not None:
            await asyncio.to_thread(
                _notify_postit_note,
                note.postit_board_id,
                note.postit_note_id,
                text_to_send,
                due_date_to_send,
            )

    return _note_response(note)


def _notify_postit_archive(board_id: str, note_id: str) -> None:
    import json
    import urllib.request
    from app.config import settings

    url = (
        f"{settings.postit_board_url.rstrip('/')}/api/boards/{board_id}/notes/{note_id}"
    )
    body = json.dumps({"gray": True}).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="PATCH")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            pass
    except Exception:
        pass


@router.delete("/by_postit", status_code=204)
async def delete_sticky_notes_by_postit(
    board_id: str = Query(..., description="付箋ボードの board_id"),
    note_id: str = Query(..., description="付箋ボード上の note id"),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(StickyNote).where(
            StickyNote.postit_board_id == board_id,
            StickyNote.postit_note_id == note_id,
        )
    )
    notes = list(result.scalars().all())
    for note in notes:
        await db.delete(note)
    await db.commit()


@router.delete("/{note_id}", status_code=204)
async def delete_sticky_note(note_id: int, db: AsyncSession = Depends(get_db)):
    """タスクボード等でのゴミ箱ドラッグ時用。StickyNote を削除。付箋ボード上はグレー化（アーカイブ）"""
    result = await db.execute(select(StickyNote).where(StickyNote.id == note_id))
    note = result.scalar_one_or_none()
    if not note:
        return

    postit_board_id = note.postit_board_id
    postit_note_id = note.postit_note_id

    await db.delete(note)
    await db.commit()

    if postit_board_id and postit_note_id:
        await asyncio.to_thread(_notify_postit_archive, postit_board_id, postit_note_id)


@router.post("/{note_id}/move_to_personal", response_model=BoardPlacementResponse)
async def move_to_personal(
    note_id: int, body: MoveToPersonalBody, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(StickyNote).where(StickyNote.id == note_id))
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="Sticky note not found")

    result = await db.execute(select(User).where(User.id == body.owner_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    result = await db.execute(
        select(BoardPlacement).where(
            BoardPlacement.note_id == note_id,
            BoardPlacement.board_type == BoardType.PERSONAL,
            BoardPlacement.owner_id == body.owner_id,
        )
    )
    placement = result.scalar_one_or_none()

    target_lane = body.lane or Lane.INBOX
    if placement:
        placement.lane = target_lane
    else:
        placement = BoardPlacement(
            note_id=note_id,
            board_type=BoardType.PERSONAL,
            owner_id=body.owner_id,
            lane=target_lane,
            sort_order=0,
        )
        db.add(placement)

    await db.flush()

    if not note.postit_note_id:
        from app.services.orchestrator import _sync_note_to_postit_sync

        try:
            ok = await asyncio.to_thread(
                _sync_note_to_postit_sync,
                note.id,
                note.content or "",
                settings.postit_board_id,
                settings.postit_board_url,
            )
            if ok:
                note.postit_board_id = settings.postit_board_id
                note.postit_note_id = f"bs-{note.id}"
                await db.flush()
        except Exception:
            pass

    await db.commit()
    await db.refresh(placement)
    return placement


@router.post("/{note_id}/copy_to_team", response_model=CopyToTeamResponse)
async def copy_to_team(
    note_id: int, body: CopyToTeamBody, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(StickyNote).where(StickyNote.id == note_id))
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="Sticky note not found")

    result = await db.execute(select(User).where(User.team_id == body.team_id))
    members = list(result.scalars().all())
    if not members:
        return CopyToTeamResponse(
            created=0,
            user_ids=[],
            message="このチームには所属メンバーがいません",
        )

    copied_count = 0
    user_ids = []
    for member in members:
        res = await db.execute(
            select(BoardPlacement).where(
                BoardPlacement.note_id == note_id,
                BoardPlacement.board_type == BoardType.PERSONAL,
                BoardPlacement.owner_id == member.id,
            )
        )
        existing = res.scalar_one_or_none()
        if not existing:
            placement = BoardPlacement(
                note_id=note_id,
                board_type=BoardType.PERSONAL,
                owner_id=member.id,
                lane=Lane.INBOX,
                sort_order=0,
            )
            db.add(placement)
            copied_count += 1
            user_ids.append(member.id)

    await db.flush()

    if not note.postit_note_id:
        from app.services.orchestrator import _sync_note_to_postit_sync

        try:
            ok = await asyncio.to_thread(
                _sync_note_to_postit_sync,
                note.id,
                note.content or "",
                settings.postit_board_id,
                settings.postit_board_url,
            )
            if ok:
                note.postit_board_id = settings.postit_board_id
                note.postit_note_id = f"bs-{note.id}"
                await db.flush()
        except Exception:
            pass

    await db.commit()
    return CopyToTeamResponse(
        created=copied_count,
        user_ids=user_ids,
        message=f"チームメンバー {copied_count} 名の Personal ボードへ追加しました",
    )


@router.post("/{note_id}/release_to_task_board", status_code=200)
async def release_to_task_board(
    note_id: int,
    owner_id: int = Query(..., description="パーソナルボードの所有者 ID"),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(BoardPlacement).where(
            BoardPlacement.note_id == note_id,
            BoardPlacement.board_type == BoardType.PERSONAL,
            BoardPlacement.owner_id == owner_id,
        )
    )
    placement = result.scalar_one_or_none()
    if placement:
        await db.delete(placement)
        await db.commit()
    return {"message": "Released from personal board"}
