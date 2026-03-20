import json

from mirror.ocr.reference_builder import build_reference_block
from mirror.ocr.vision_parser import parse_worksheet_to_json


def parse_worksheet(file):
    data = parse_worksheet_to_json(file)
    reference = build_reference_block(data)
    return {"json": data, "reference": reference}


def debug_parse(file, *, print_json: bool = True, print_reference: bool = True):
    """
    Debug helper for manual inspection.
    Returns the parsed result, but keeps console output under control.
    """
    result = parse_worksheet(file)

    if print_json:
        print("\n================ JSON ================\n")
        print(json.dumps(result["json"], indent=2, ensure_ascii=False))

    if print_reference:
        print("\n================ REFERENCE BLOCK ================\n")
        print(result["reference"])

    return result
