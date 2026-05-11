import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from extractor.dataverse_client import build_batch_payload, build_create_request


def test_build_create_request():
    req = build_create_request("cree1_extractionjobs", {"cree1_jobid": "j1"}, "1")
    assert req["method"] == "POST"
    assert req["url"] == "cree1_extractionjobs"
    assert req["body"]["cree1_jobid"] == "j1"


def test_build_create_request_with_lookup():
    req = build_create_request(
        "cree1_extractedlineitems",
        {"cree1_lineitemname": "Cash"},
        "1",
        lookups={"cree1_ExtractionJob@odata.bind": "/cree1_extractionjobs(abc)"},
    )
    assert req["body"]["cree1_ExtractionJob@odata.bind"] == "/cree1_extractionjobs(abc)"


def test_build_batch_payload():
    requests = [
        build_create_request("cree1_extractedlineitems", {"cree1_lineitemname": f"item_{i}"}, str(i))
        for i in range(3)
    ]
    boundary, body = build_batch_payload(requests)
    assert boundary in body
    assert body.count("POST cree1_extractedlineitems") == 3
    assert "item_0" in body
    assert "item_2" in body
