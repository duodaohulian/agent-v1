"""Lightweight transport contracts shared by the six formal tools."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

CONTRACT_VERSION: Literal["1.1.0"] = "1.1.0"
CaseRef = Annotated[str, Field(pattern=r"^[A-Za-z0-9_-]{1,64}$")]
QcArtifactId = Annotated[str, Field(pattern=r"^qc_[a-f0-9]{32}$")]
CtArtifactId = Annotated[str, Field(pattern=r"^ctf_[a-f0-9]{32}$")]
PathologyArtifactId = Annotated[str, Field(pattern=r"^pathf_[a-f0-9]{32}$")]
PredictionArtifactId = Annotated[str, Field(pattern=r"^pred_[a-f0-9]{32}$")]


class StrictContract(BaseModel):
    """Forbid undeclared transport fields and non-finite values."""

    model_config = ConfigDict(extra="forbid", allow_inf_nan=False, frozen=True)


class EmptyInput(StrictContract):
    """An intentionally empty tool input object."""


class ClinicalInput(StrictContract):
    """The locked four-field clinical input contract."""

    age: Annotated[int | float, Field(ge=0, le=120)]
    male: Literal[0, 1]
    Type: int | float
    T: int | float

    @field_validator("age", "male", "Type", "T", mode="before")
    @classmethod
    def reject_boolean(cls, value: object) -> object:
        if isinstance(value, bool):
            raise ValueError("clinical numeric fields must not be boolean")
        return value