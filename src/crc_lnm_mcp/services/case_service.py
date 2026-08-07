"""Lazy indexed demo-case access and bounded process-local artifacts."""

from __future__ import annotations

import hashlib
import json
import math
import re
import secrets
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from crc_lnm_mcp.settings import (
    MAX_CASE_RECORD_BYTES,
    MAX_CASE_RESOURCE_BYTES,
    package_asset,
)

CASE_REF_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
ARTIFACT_PREFIX = {
    "case_qc": "qc",
    "ct_features": "ctf",
    "pathology_features": "pathf",
    "prediction": "pred",
    "report": "rpt",
}
FORBIDDEN_FIELDS = {
    "address",
    "email",
    "label",
    "mrn",
    "name",
    "outcome",
    "patient_id",
    "phone",
    "target",
}


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _format_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True, slots=True)
class CaseIndexEntry:
    offset: int
    length: int
    demo: bool


@dataclass(frozen=True, slots=True)
class ArtifactRecord:
    artifact_id: str
    artifact_type: str
    trace_id: UUID
    case_ref: str
    case_binding_sha256: str
    payload: Any
    content_sha256: str
    created_at: datetime
    expires_at: datetime

    def public_ref(self) -> dict[str, str]:
        return {
            "artifact_id": self.artifact_id,
            "artifact_type": self.artifact_type,
            "media_type": (
                "text/html; charset=utf-8" if self.artifact_type == "report" else "application/json"
            ),
            "content_sha256": self.content_sha256,
            "created_at": _format_utc(self.created_at),
            "expires_at": _format_utc(self.expires_at),
        }


class CaseAndFeatureProvider:
    """Open the one packaged JSONL only after a case-related tool call."""

    def __init__(self) -> None:
        self._index: dict[str, CaseIndexEntry] | None = None
        self._index_lock = threading.Lock()
        self._schema: dict[str, Any] | None = None
        self._schema_lock = threading.Lock()
        self._artifact_lock = threading.RLock()
        self._artifacts: dict[str, ArtifactRecord] = {}
        self._artifact_limit = 64

    @property
    def indexed_record_count(self) -> int:
        return 0 if self._index is None else len(self._index)

    @staticmethod
    def _validate_case_ref(case_ref: str) -> None:
        if not isinstance(case_ref, str) or not CASE_REF_PATTERN.fullmatch(case_ref):
            raise ValueError("case_ref must match the allowlist and cannot be a path")

    def _ensure_index(self) -> dict[str, CaseIndexEntry]:
        if self._index is not None:
            return self._index
        with self._index_lock:
            if self._index is not None:
                return self._index
            index: dict[str, CaseIndexEntry] = {}
            total = 0
            offset = 0
            resource = package_asset("cases", "demo_cases.jsonl")
            with resource.open("rb") as handle:
                while True:
                    line = handle.readline(MAX_CASE_RECORD_BYTES + 1)
                    if not line:
                        break
                    if len(line) > MAX_CASE_RECORD_BYTES:
                        raise ValueError("case resource record exceeds size limit")
                    total += len(line)
                    if total > MAX_CASE_RESOURCE_BYTES:
                        raise ValueError("case resource exceeds size limit")
                    value = json.loads(line.decode("utf-8"))
                    case_ref = value.get("case_ref") if isinstance(value, dict) else None
                    if not isinstance(case_ref, str) or not CASE_REF_PATTERN.fullmatch(case_ref):
                        raise ValueError("case resource contains an invalid case_ref")
                    if case_ref in index:
                        raise ValueError("case resource contains a duplicate case_ref")
                    index[case_ref] = CaseIndexEntry(
                        offset=offset,
                        length=len(line),
                        demo=value.get("demo") is True,
                    )
                    offset += len(line)
            self._index = index
            return index

    def _load_case(self, case_ref: str) -> dict[str, Any]:
        self._validate_case_ref(case_ref)
        entry = self._ensure_index().get(case_ref)
        if entry is None:
            raise KeyError("case_ref is not available")
        resource = package_asset("cases", "demo_cases.jsonl")
        with resource.open("rb") as handle:
            handle.seek(entry.offset)
            raw = handle.read(entry.length)
        value = json.loads(raw.decode("utf-8"))
        if not isinstance(value, dict) or value.get("case_ref") != case_ref:
            raise ValueError("indexed case resource is inconsistent")
        return value

    @staticmethod
    def _reject_privacy_fields(value: object) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                if str(key).lower() in FORBIDDEN_FIELDS:
                    raise ValueError("case contains a forbidden privacy or label field")
                CaseAndFeatureProvider._reject_privacy_fields(child)
        elif isinstance(value, list):
            for child in value:
                CaseAndFeatureProvider._reject_privacy_fields(child)

    @staticmethod
    def _validate_numeric_payload(payload: dict[str, Any], expected: int, name: str) -> None:
        if len(payload) != expected:
            raise ValueError(f"{name} dimension is invalid")
        for value in payload.values():
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError(f"{name} contains a non-numeric value")
            if not math.isfinite(float(value)):
                raise ValueError(f"{name} contains a non-finite value")

    def validated_case(self, case_ref: str) -> tuple[dict[str, Any], str]:
        record = self._load_case(case_ref)
        if record.get("resource_schema_version") != "1.0.12-demo" or record.get("demo") is not True:
            raise ValueError("case resource is not an approved demo record")
        manifest = record.get("manifest")
        payloads = record.get("payloads")
        digests = record.get("payload_sha256")
        if (
            not isinstance(manifest, dict)
            or not isinstance(payloads, dict)
            or not isinstance(digests, dict)
        ):
            raise ValueError("case resource is incomplete")
        if manifest.get("case_ref") != case_ref or manifest.get("input_mode") != "precomputed":
            raise ValueError("case manifest does not match the requested precomputed case")
        if set(payloads) != {"clinical", "ct_features", "pathology_features"}:
            raise ValueError("case modalities are incomplete")
        self._reject_privacy_fields(record)
        for name, payload in payloads.items():
            if not isinstance(payload, dict):
                raise ValueError("case modality is not a JSON object")
            actual = hashlib.sha256(_canonical_bytes(payload)).hexdigest()
            if digests.get(name) != actual:
                raise ValueError("case modality checksum mismatch")
        self._validate_numeric_payload(payloads["ct_features"], 1409, "CT")
        self._validate_numeric_payload(payloads["pathology_features"], 768, "pathology")
        clinical = payloads["clinical"]
        if set(clinical) != {"age", "male", "Type", "T"}:
            raise ValueError("clinical fields are invalid")
        self._validate_numeric_payload(clinical, 4, "clinical")
        binding_payload = {
            "case_ref": case_ref,
            "research_id": manifest.get("research_id"),
            "payload_sha256": digests,
        }
        binding = hashlib.sha256(_canonical_bytes(binding_payload)).hexdigest()
        return record, binding

    def _put_artifact(
        self,
        artifact_type: str,
        *,
        trace_id: UUID,
        case_ref: str,
        case_binding_sha256: str,
        payload: Any,
    ) -> ArtifactRecord:
        if artifact_type not in ARTIFACT_PREFIX:
            raise ValueError("unsupported artifact type")
        raw = _canonical_bytes(payload) if not isinstance(payload, str) else payload.encode("utf-8")
        if len(raw) > MAX_CASE_RECORD_BYTES:
            raise ValueError("artifact exceeds size limit")
        now = datetime.now(timezone.utc)
        with self._artifact_lock:
            if len(self._artifacts) >= self._artifact_limit:
                raise RuntimeError("artifact capacity is exhausted")
            artifact_id = f"{ARTIFACT_PREFIX[artifact_type]}_{secrets.token_hex(16)}"
            artifact = ArtifactRecord(
                artifact_id=artifact_id,
                artifact_type=artifact_type,
                trace_id=trace_id,
                case_ref=case_ref,
                case_binding_sha256=case_binding_sha256,
                payload=payload,
                content_sha256=hashlib.sha256(raw).hexdigest(),
                created_at=now,
                expires_at=now + timedelta(minutes=30),
            )
            self._artifacts[artifact_id] = artifact
            return artifact

    def put_artifact(
        self,
        artifact_type: str,
        *,
        trace_id: UUID,
        case_ref: str,
        case_binding_sha256: str,
        payload: Any,
    ) -> ArtifactRecord:
        return self._put_artifact(
            artifact_type,
            trace_id=trace_id,
            case_ref=case_ref,
            case_binding_sha256=case_binding_sha256,
            payload=payload,
        )

    def schema(self) -> dict[str, Any]:
        if self._schema is not None:
            return self._schema
        with self._schema_lock:
            if self._schema is None:
                resource = package_asset("schemas", "schema.json")
                with resource.open("rb") as handle:
                    raw = handle.read(MAX_CASE_RECORD_BYTES + 1)
                if len(raw) > MAX_CASE_RECORD_BYTES:
                    raise ValueError("schema exceeds size limit")
                value = json.loads(raw.decode("utf-8"))
                if not isinstance(value, dict):
                    raise ValueError("schema is not a JSON object")
                if (
                    len(value.get("pathology_features", [])) != 768
                    or len(value.get("ct_shape", [])) != 14
                    or len(value.get("ct_original", [])) != 93
                    or len(value.get("ct_wavelet", [])) != 744
                    or len(value.get("ct_transformed", [])) != 558
                ):
                    raise ValueError("schema dimensions are invalid")
                self._schema = value
            return self._schema

    def prepare_ct_features(
        self,
        case_ref: str,
        *,
        qc_artifact_id: str,
        request_id: UUID,
        trace_id: UUID,
    ) -> dict[str, Any]:
        from .ct_feature_service import prepare_ct_features

        return prepare_ct_features(
            self,
            case_ref,
            qc_artifact_id=qc_artifact_id,
            request_id=request_id,
            trace_id=trace_id,
        )

    def prepare_pathology_features(
        self,
        case_ref: str,
        *,
        qc_artifact_id: str,
        request_id: UUID,
        trace_id: UUID,
    ) -> dict[str, Any]:
        from .pathology_feature_service import prepare_pathology_features

        return prepare_pathology_features(
            self,
            case_ref,
            qc_artifact_id=qc_artifact_id,
            request_id=request_id,
            trace_id=trace_id,
        )

    def generate_report(
        self,
        case_ref: str,
        *,
        qc_artifact_id: str,
        prediction_artifact_id: str,
        request_id: UUID,
        trace_id: UUID,
    ) -> dict[str, Any]:
        from .report_service import generate_report

        return generate_report(
            self,
            case_ref,
            qc_artifact_id=qc_artifact_id,
            prediction_artifact_id=prediction_artifact_id,
            request_id=request_id,
            trace_id=trace_id,
        )

    def require_artifact(
        self,
        artifact_id: str,
        *,
        trace_id: UUID,
        case_ref: str,
        expected_type: str,
    ) -> ArtifactRecord:
        with self._artifact_lock:
            artifact = self._artifacts.get(artifact_id)
        if artifact is None:
            raise ValueError("artifact is unavailable")
        if artifact.trace_id != trace_id:
            raise ValueError("artifact trace does not match")
        if artifact.case_ref != case_ref:
            raise ValueError("artifact case does not match")
        if artifact.artifact_type != expected_type:
            raise ValueError("artifact type does not match")
        if artifact.expires_at <= datetime.now(timezone.utc):
            raise ValueError("artifact has expired")
        return artifact

    def case_data_qc(self, case_ref: str, *, request_id: UUID, trace_id: UUID) -> dict[str, Any]:
        del request_id
        _record, binding = self.validated_case(case_ref)
        payload = {
            "case_ref": case_ref,
            "case_binding_sha256": binding,
            "passed": True,
        }
        artifact = self._put_artifact(
            "case_qc",
            trace_id=trace_id,
            case_ref=case_ref,
            case_binding_sha256=binding,
            payload=payload,
        )
        return {
            "artifact": artifact.public_ref(),
            "case_ref": case_ref,
            "demo": True,
            "input_mode": "precomputed",
            "ct_source_preference": "precomputed",
            "ct_source_selected": "precomputed",
            "fallback_policy": "precomputed_if_available",
            "passed": True,
            "modalities": {"ct": "present", "pathology": "present", "clinical": "present"},
            "ct_sources": {"precomputed": "present"},
            "privacy_check": "passed",
            "files_checked": 3,
        }


__all__ = ["ArtifactRecord", "CaseAndFeatureProvider"]
