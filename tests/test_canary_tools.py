from __future__ import annotations

import asyncio

from crc_lnm_mcp import server

EXPECTED_TOOLS = {
    "crc_lnm_get_model_info",
    "crc_lnm_case_data_qc",
    "crc_lnm_prepare_ct_features",
    "crc_lnm_prepare_pathology_features",
    "crc_lnm_predict_multimodal",
    "crc_lnm_generate_report",
}


def test_full_runtime_registers_exactly_six_tools() -> None:
    assert set(asyncio.run(server.mcp.get_tools())) == EXPECTED_TOOLS


def test_canary_placeholder_tools_are_removed() -> None:
    names = set(asyncio.run(server.mcp.get_tools()))
    assert "healthcheck" not in names
    assert "describe_deployment" not in names
