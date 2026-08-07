"""Stable public error codes for the full lazy runtime."""

from enum import Enum


class ErrorCode(str, Enum):
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    BUNDLE_INTEGRITY_FAILURE = "BUNDLE_INTEGRITY_FAILURE"
    INFERENCE_FAILURE = "INFERENCE_FAILURE"

    def __str__(self) -> str:
        return self.value


__all__ = ["ErrorCode"]
