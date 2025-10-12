from app.schemas import EventIn, SearchIn


def test_event_contract(): assert EventIn(service="api",metric="latency",value=42).value==42
def test_search_limits():
    try: SearchIn(query="x",limit=500)
    except ValueError: pass
    else: raise AssertionError("validation should reject invalid search")
