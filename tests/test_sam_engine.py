from sam_engine import sam_engine, SamSession

def assert_base_schema(resp: dict):
    assert isinstance(resp, dict)
    assert resp.get("voice") == "sam"
    assert isinstance(resp.get("mode"), str)
    assert isinstance(resp.get("summary"), str)

    # required keys your frontend expects
    for k in [
        "key_points", "item_list", "next_step",
        "primary_pairing", "alternative_pairings",
        "stops", "target_bottles", "store_targets"
    ]:
        assert k in resp

def test_clarify():
    s = SamSession(user_id="t-clarify")
    r = sam_engine("find allocation shops near me", s)
    assert_base_schema(r)
    assert r["mode"] == "clarify"

def test_hunt_then_target_capture_stays_hunt():
    s = SamSession(user_id="t-hunt")
    r1 = sam_engine("30344 best allocation shops", s)
    assert_base_schema(r1)
    assert r1["mode"] == "hunt"

    r2 = sam_engine("Weller Antique 107", s)
    assert_base_schema(r2)
    assert r2["mode"] == "hunt"
