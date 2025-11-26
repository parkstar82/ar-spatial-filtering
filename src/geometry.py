from shapely.geometry import Polygon, box, Point

def is_triangle_intersect(mbr: Polygon, query_triangle: Polygon) -> bool:
    """
    Checks if any line segment of the Query Triangle intersects with the MBR.
    
    Logic: Iterate through segments of both shapes and check for intersection.
    We use shapely's boundary intersection to achieve this.
    
    Args:
        mbr (Polygon): The Minimum Bounding Rectangle (as a shapely Polygon/box).
        query_triangle (Polygon): The Query Triangle (View Frustum).
        
    Returns:
        bool: True if boundaries intersect, False otherwise.
    """
    return mbr.boundary.intersects(query_triangle.boundary)

def is_triangle_in_mbr(mbr: Polygon, query_triangle: Polygon) -> bool:
    """
    Checks if the Query Triangle is completely or partially inside the MBR without intersection.
    (e.g., small triangle inside big MBR).
    
    Logic: Check if any point of the triangle is inside the MBR.
    Since we check intersection separately, checking if a vertex is inside covers the 'inside' case.
    
    Args:
        mbr (Polygon): The Minimum Bounding Rectangle.
        query_triangle (Polygon): The Query Triangle.
        
    Returns:
        bool: True if triangle is inside MBR.
    """
    # Check if the first point of the triangle is inside the MBR
    # We use the first coordinate of the exterior.
    p = Point(query_triangle.exterior.coords[0])
    return mbr.contains(p)

def is_mbr_in_triangle(mbr: Polygon, query_triangle: Polygon) -> bool:
    """
    Checks if the MBR is completely inside the Query Triangle.
    
    Logic: Check if any point of the MBR is inside the Triangle.
    
    Args:
        mbr (Polygon): The Minimum Bounding Rectangle.
        query_triangle (Polygon): The Query Triangle.
        
    Returns:
        bool: True if MBR is inside Triangle.
    """
    # Check if the first point of the MBR is inside the Triangle
    p = Point(mbr.exterior.coords[0])
    return query_triangle.contains(p)

def consistent(mbr: Polygon, query_triangle: Polygon) -> bool:
    """
    The main filter function.
    
    Logic:
    1. Check generic intersection: mbr.intersects(query_triangle.envelope).
    2. Apply AR Optimization: Return True IF (is_triangle_intersect OR is_triangle_in_mbr OR is_mbr_in_triangle).
    
    Args:
        mbr (Polygon): The Minimum Bounding Rectangle.
        query_triangle (Polygon): The Query Triangle.
        
    Returns:
        bool: True if the node should be searched, False otherwise (Dead Space).
    """
    # 1. Generic intersection check (MBR vs Triangle Envelope)
    if not mbr.intersects(query_triangle.envelope):
        return False
        
    # 2. AR Optimization
    return (is_triangle_intersect(mbr, query_triangle) or
            is_triangle_in_mbr(mbr, query_triangle) or
            is_mbr_in_triangle(mbr, query_triangle))

if __name__ == "__main__":
    # Test case demonstrating Dead Space
    # Triangle: (0,0), (10,0), (5,5). Envelope is box(0,0, 10,5).
    # MBR: box(8, 4, 9, 6). 
    # MBR x range [8, 9] overlaps Triangle x range [0, 10].
    # MBR y range [4, 6] overlaps Triangle y range [0, 5].
    # So Envelopes intersect.
    
    # However, at x=8, Triangle height is y = 10-8 = 2.
    # MBR starts at y=4. So they are disjoint.
    
    t_coords = [(0,0), (10,0), (5,5)]
    tri = Polygon(t_coords)
    
    # Create MBR using box(minx, miny, maxx, maxy)
    m = box(8, 4, 9, 6)
    
    print("--- AR Spatial Filtering Test ---")
    print(f"Triangle: {tri}")
    print(f"MBR: {m}")
    
    # Generic Check
    generic_check = m.intersects(tri.envelope)
    print(f"Generic Intersection (MBR vs Triangle Envelope): {generic_check}")
    
    # Specific Predicates
    intersect = is_triangle_intersect(m, tri)
    tri_in_mbr = is_triangle_in_mbr(m, tri)
    mbr_in_tri = is_mbr_in_triangle(m, tri)
    
    print(f"is_triangle_intersect: {intersect}")
    print(f"is_triangle_in_mbr: {tri_in_mbr}")
    print(f"is_mbr_in_triangle: {mbr_in_tri}")
    
    # Consistent Result
    result = consistent(m, tri)
    print(f"Consistent (Final Result): {result}")
    
    if generic_check and not result:
        print("\nSUCCESS: Demonstrated Dead Space elimination!")
    else:
        print("\nFAIL: Did not demonstrate Dead Space elimination as expected.")
