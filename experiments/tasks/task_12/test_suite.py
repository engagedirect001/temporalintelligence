import pytest
from buggy_code import PaginatedQuery


def make_data(n):
    return [{"id": i, "type": "even" if i % 2 == 0 else "odd", "value": i * 10} for i in range(n)]


def test_basic_pagination():
    pq = PaginatedQuery(make_data(25), page_size=10)
    r1 = pq.query()
    assert len(r1["items"]) == 10
    assert r1["has_more"] is True
    
    r2 = pq.query(cursor=r1["next_cursor"])
    assert len(r2["items"]) == 10
    
    r3 = pq.query(cursor=r2["next_cursor"])
    assert len(r3["items"]) == 5
    assert r3["has_more"] is False


def test_filter_returns_correct_count():
    """Bug 1: filtering after slicing means pages have fewer than page_size items."""
    data = make_data(40)  # 20 even, 20 odd
    pq = PaginatedQuery(data, page_size=10)
    
    result = pq.query(filters={"type": "even"})
    # Should return 10 even items (page_size=10 of matching items)
    assert len(result["items"]) == 10, \
        f"Expected 10 matching items per page, got {len(result['items'])}"


def test_filter_returns_all_matching():
    """Bug 1+2: all matching items across all pages must be returned."""
    data = make_data(100)  # 50 even, 50 odd
    pq = PaginatedQuery(data, page_size=10)
    
    all_items = pq.query_all(filters={"type": "even"})
    expected = [d for d in data if d["type"] == "even"]
    assert len(all_items) == len(expected), \
        f"Expected {len(expected)} items, got {len(all_items)}"


def test_no_duplicates_across_pages():
    data = make_data(30)
    pq = PaginatedQuery(data, page_size=10)
    
    all_items = pq.query_all()
    ids = [item["id"] for item in all_items]
    assert len(ids) == len(set(ids)), "Duplicate items across pages"


def test_no_items_skipped():
    data = make_data(30)
    pq = PaginatedQuery(data, page_size=10)
    
    all_items = pq.query_all()
    assert len(all_items) == 30


def test_empty_data():
    pq = PaginatedQuery([], page_size=10)
    result = pq.query()
    assert result["items"] == []
    assert result["has_more"] is False


def test_single_page():
    pq = PaginatedQuery(make_data(5), page_size=10)
    result = pq.query()
    assert len(result["items"]) == 5
    assert result["has_more"] is False


def test_invalid_cursor():
    pq = PaginatedQuery(make_data(10))
    with pytest.raises(ValueError):
        pq.query(cursor="invalid!!!")
