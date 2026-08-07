"""Register exactly the six formal CRC-LNM tools."""

from typing import Any

from crc_lnm_mcp.runtime import RuntimeProvider

from .case_data_qc import register as register_case_data_qc, TOOL_DESCRIPTION as CASE_DATA_QC_DESCRIPTION
from .generate_report import register as register_generate_report, TOOL_DESCRIPTION as GENERATE_REPORT_DESCRIPTION
from .get_model_info import register as register_get_model_info, TOOL_DESCRIPTION as GET_MODEL_INFO_DESCRIPTION
from .predict_multimodal import register as register_predict_multimodal, TOOL_DESCRIPTION as PREDICT_MULTIMODAL_DESCRIPTION
from .prepare_ct_features import register as register_prepare_ct_features, TOOL_DESCRIPTION as PREPARE_CT_DESCRIPTION
from .prepare_pathology_features import register as register_prepare_pathology_features, TOOL_DESCRIPTION as PREPARE_PATHOLOGY_DESCRIPTION

TOOL_DESCRIPTIONS = {
    "crc_lnm_get_model_info": GET_MODEL_INFO_DESCRIPTION,
    "crc_lnm_case_data_qc": CASE_DATA_QC_DESCRIPTION,
    "crc_lnm_prepare_ct_features": PREPARE_CT_DESCRIPTION,
    "crc_lnm_prepare_pathology_features": PREPARE_PATHOLOGY_DESCRIPTION,
    "crc_lnm_predict_multimodal": PREDICT_MULTIMODAL_DESCRIPTION,
    "crc_lnm_generate_report": GENERATE_REPORT_DESCRIPTION,
}

def register_all(mcp: Any, runtime: RuntimeProvider) -> None:
 register_get_model_info(mcp, runtime)
 register_case_data_qc(mcp, runtime)
 register_prepare_ct_features(mcp, runtime)
 register_prepare_pathology_features(mcp, runtime)
 register_predict_multimodal(mcp, runtime)
 register_generate_report(mcp, runtime)

__all__ = ["register_all", "TOOL_DESCRIPTIONS"]
