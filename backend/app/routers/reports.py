import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from PIL import Image, ImageOps, UnidentifiedImageError
from sqlalchemy.orm import Session

from ..auth import current_user, require_role
from ..config import UPLOAD_DIR
from ..db import get_db
from ..models import Report, User, now
from ..schemas import AssignIn, ReportOut, SubmitOut, UserOut, VerifyIn
from ..services.detector import detect
from ..services.geo import find_duplicate, find_ward, image_hash
from ..services.risk import score_report

router = APIRouter(prefix="/api/reports", tags=["reports"])
MAX_UPLOAD_MB = 15


def to_out(r: Report) -> ReportOut:
    return ReportOut(
        id=r.id, lat=r.lat, lon=r.lon, ward_id=r.ward_id, ward_name=r.ward.name, note=r.note,
        photo_url=f"/uploads/{r.photo}",
        after_photo_url=f"/uploads/{r.after_photo}" if r.after_photo else None,
        detection=r.detection, risk=r.risk, status=r.status, confirmations=r.confirmations,
        reporter_name=r.reporter.name,
        assigned_to=UserOut.model_validate(r.assigned_to) if r.assigned_to else None,
        created_at=r.created_at, assigned_at=r.assigned_at, cleaned_at=r.cleaned_at, closed_at=r.closed_at,
    )


async def save_photo(upload: UploadFile) -> str:
    data = await upload.read()
    if len(data) > MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(413, f"Photo is larger than {MAX_UPLOAD_MB} MB")
    name = f"{uuid.uuid4().hex}.jpg"
    try:
        from io import BytesIO

        img = ImageOps.exif_transpose(Image.open(BytesIO(data))).convert("RGB")
    except (UnidentifiedImageError, OSError):
        raise HTTPException(400, "That file is not a photo we can read (use JPG or PNG)")
    img.thumbnail((1600, 1600))
    img.save(UPLOAD_DIR / name, "JPEG", quality=85)
    return name


def get_report(db: Session, report_id: int) -> Report:
    r = db.get(Report, report_id)
    if not r:
        raise HTTPException(404, "Report not found")
    return r


@router.post("", response_model=SubmitOut)
async def submit_report(
    photo: UploadFile = File(...),
    lat: float = Form(..., ge=-90, le=90),
    lon: float = Form(..., ge=-180, le=180),
    note: str = Form("", max_length=300),
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    name = await save_photo(photo)
    path = UPLOAD_DIR / name
    det = detect(path)
    h = image_hash(path)

    dup = find_duplicate(db, lat, lon, h) if det["suspected"] else None
    if dup:
        dup.confirmations += 1
        dup.risk = score_report(dup.detection, dup.ward, dup.confirmations)
        dup.risk_score = dup.risk["score"]
        db.commit()
        Path(path).unlink(missing_ok=True)
        return SubmitOut(report=to_out(dup), duplicate=True,
                         message=f"This spot was already reported. Your photo was added as confirmation number {dup.confirmations}.")

    ward = find_ward(db, lat, lon)
    risk = score_report(det, ward)
    r = Report(reporter_id=user.id, lat=lat, lon=lon, ward_id=ward.id, note=note.strip(), photo=name,
               image_hash=h, detection=det, risk=risk, risk_score=risk["score"])
    db.add(r)
    db.commit()
    db.refresh(r)
    msg = "Report sent. The ward officer can see it on the hotspot map." if det["suspected"] else \
        "Report sent. The AI did not find a breeding site, but an officer can still review it."
    return SubmitOut(report=to_out(r), duplicate=False, message=msg)


@router.get("", response_model=list[ReportOut])
def list_reports(
    status: str | None = None,
    ward: int | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    q = db.query(Report)
    if user.role == "resident":
        q = q.filter(Report.reporter_id == user.id)
    elif user.role == "worker":
        q = q.filter(Report.assigned_to_id == user.id)
    if status:
        q = q.filter(Report.status.in_(status.split(",")))
    if ward:
        q = q.filter(Report.ward_id == ward)
    return [to_out(r) for r in q.order_by(Report.risk_score.desc(), Report.created_at.desc()).all()]


@router.get("/map", response_model=list[ReportOut])
def map_reports(db: Session = Depends(get_db), _: User = Depends(current_user)):
    """Open reports for the public map (every role can see where the hotspots are)."""
    rs = db.query(Report).filter(Report.status != "closed").order_by(Report.risk_score.desc()).all()
    return [to_out(r) for r in rs]


@router.get("/{report_id}", response_model=ReportOut)
def report_detail(report_id: int, db: Session = Depends(get_db), _: User = Depends(current_user)):
    return to_out(get_report(db, report_id))


@router.post("/{report_id}/assign", response_model=ReportOut)
def assign(report_id: int, body: AssignIn, db: Session = Depends(get_db), _: User = Depends(require_role("officer"))):
    r = get_report(db, report_id)
    worker = db.get(User, body.worker_id)
    if not worker or worker.role != "worker":
        raise HTTPException(400, "Choose a field worker")
    if r.status == "closed":
        raise HTTPException(400, "This report is already closed")
    r.assigned_to_id, r.status, r.assigned_at = worker.id, "assigned", now()
    r.after_photo, r.cleaned_at = None, None
    db.commit()
    return to_out(r)


@router.post("/{report_id}/clean", response_model=ReportOut)
async def mark_cleaned(
    report_id: int,
    photo: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_role("worker")),
):
    r = get_report(db, report_id)
    if r.assigned_to_id != user.id:
        raise HTTPException(403, "This task is not assigned to you")
    if r.status != "assigned":
        raise HTTPException(400, "This task is not waiting for cleaning")
    r.after_photo = await save_photo(photo)
    r.status, r.cleaned_at = "cleaned", now()
    db.commit()
    return to_out(r)


@router.post("/{report_id}/verify", response_model=ReportOut)
def verify(report_id: int, body: VerifyIn, db: Session = Depends(get_db), _: User = Depends(require_role("officer"))):
    r = get_report(db, report_id)
    if r.status != "cleaned":
        raise HTTPException(400, "Only cleaned reports can be verified")
    if body.approve:
        r.status, r.closed_at = "closed", now()
    else:
        r.status, r.after_photo, r.cleaned_at = "assigned", None, None
    db.commit()
    return to_out(r)
