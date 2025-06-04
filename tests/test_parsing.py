import pytest
import re


def test_quantity_parsing_numeric():
    line = "- TICKER: ICWN, ACTION: BUY, QUANTITY: 2,300, REASON: Test"  # comma in quantity
    qty_segment = line.split("QUANTITY:")[1]
    if "REASON:" in qty_segment:
        qty_segment = qty_segment.split("REASON:")[0]
    quantity_raw = qty_segment.strip().rstrip(',')
    cleaned = quantity_raw.replace("$", "").replace(",", "")
    assert cleaned == "2300"
    assert float(cleaned) == 2300.0


def test_quantity_fallback():
    line = "- TICKER: ICWN, ACTION: BUY, QUANTITY: N/A, REASON: Test"
    quantity_raw = line.split("QUANTITY:")[1].split(",")[0].strip()
    cleaned = quantity_raw.replace("$", "").replace(",", "")
    with pytest.raises(ValueError):
        float(cleaned)  # should fail

import pytest
