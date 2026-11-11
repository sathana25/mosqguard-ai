from datetime import datetime

from pydantic import BaseModel, Field


class LoginIn(BaseModel):
    username: str
    password: str


class RegisterIn(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    name: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=6, max_length=100)


class UserOut(BaseModel):
    id: int
    username: str
    name: str
    role: str
    ward: int | None = None

    model_config = {"from_attributes": True}


class TokenOut(BaseModel):
    token: str
    user: UserOut


class AssignIn(BaseModel):
    worker_id: int


class VerifyIn(BaseModel):
    approve: bool


class ReportOut(BaseModel):
    id: int
    lat: float
    lon: float
    ward_id: int
    ward_name: str
    note: str
    photo_url: str
    after_photo_url: str | None
    detection: dict
    risk: dict
    status: str
    confirmations: int
    reporter_name: str
    assigned_to: UserOut | None
    created_at: datetime
    assigned_at: datetime | None
    cleaned_at: datetime | None
    closed_at: datetime | None


class SubmitOut(BaseModel):
    report: ReportOut
    duplicate: bool
    message: str
