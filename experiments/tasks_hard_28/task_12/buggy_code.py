"""
Task 12: Cursor-Based Pagination with Filtering
Category: API/Protocol bugs
"""
import base64
import json


class PaginatedQuery:
    """Cursor-based pagination over a dataset with server-side filtering."""
    
    def __init__(self, data, page_size=10):
        self.data = data  # list of dicts
        self.page_size = page_size
    
    def _encode_cursor(self, index):
        """Encode position as opaque cursor."""
        return base64.b64encode(json.dumps({"idx": index}).encode()).decode()
    
    def _decode_cursor(self, cursor):
        """Decode cursor to position."""
        if cursor is None:
            return 0
        try:
            payload = json.loads(base64.b64decode(cursor))
            return payload["idx"]
        except Exception:
            raise ValueError("Invalid cursor")
    
    def query(self, cursor=None, filters=None):
        """
        Return next page of results.
        filters: dict of field -> value to match
        Returns: {"items": [...], "next_cursor": str|None, "has_more": bool}
        """
        start_idx = self._decode_cursor(cursor)
        
        # Bug 1: applies filter AFTER slicing, so filtered-out items
        # reduce the page size and some items are never returned
        page = self.data[start_idx:start_idx + self.page_size]
        
        if filters:
            page = [
                item for item in page
                if all(item.get(k) == v for k, v in filters.items())
            ]
        
        # Bug 2: next cursor is based on start_idx + page_size regardless
        # of how many items matched the filter
        next_idx = start_idx + self.page_size
        has_more = next_idx < len(self.data)
        
        # Bug 3: cursor should point to next unprocessed item,
        # but when filter eliminates items, we might skip items that
        # would match on a later page boundary
        next_cursor = self._encode_cursor(next_idx) if has_more else None
        
        return {
            "items": page,
            "next_cursor": next_cursor,
            "has_more": has_more,
        }
    
    def query_all(self, filters=None):
        """Iterate through all pages and collect all items."""
        all_items = []
        cursor = None
        
        while True:
            result = self.query(cursor=cursor, filters=filters)
            all_items.extend(result["items"])
            
            if not result["has_more"]:
                break
            cursor = result["next_cursor"]
        
        return all_items
