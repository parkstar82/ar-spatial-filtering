import sys
import os
import random
import math
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.collections import PatchCollection
from matplotlib.animation import FuncAnimation, PillowWriter
from shapely.geometry import Polygon, box
from tqdm import tqdm

# Ensure src can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.geometry import consistent

# --- Configuration ---
ASSETS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'assets'))
os.makedirs(ASSETS_DIR, exist_ok=True)

BATCH_SIZE = 5
MAX_DEPTH = 3 # 0, 1, 2, 3 (4 levels)
SPACE_SIZE = 1000

# Colors
COLOR_UNVISITED = 'black'
COLOR_VISITED = 'lime' # Bright Green
COLOR_QUERY = 'blue'

# --- 1. Data Structure ---
class Node:
    _id_counter = 0
    
    def __init__(self, mbr, depth, is_leaf=False):
        self.id = Node._id_counter
        Node._id_counter += 1
        self.mbr = mbr
        self.depth = depth
        self.is_leaf = is_leaf
        self.children = []
        
    def add_child(self, node):
        self.children.append(node)

def generate_deep_rtree(bbox, current_depth, max_depth):
    minx, miny, maxx, maxy = bbox
    width = maxx - minx
    height = maxy - miny
    
    node = Node(box(minx, miny, maxx, maxy), current_depth, is_leaf=(current_depth == max_depth))
    
    if current_depth == max_depth:
        return node
    
    # Branching factor
    rows, cols = 3, 3
    if current_depth == max_depth - 1:
        rows, cols = 4, 4 
        
    cell_w = width / cols
    cell_h = height / rows
    
    for r in range(rows):
        for c in range(cols):
            gap = 0.1 if current_depth < max_depth - 1 else 0.2
            
            cmx = minx + c * cell_w
            cmy = miny + r * cell_h
            
            jitter_x = random.uniform(-cell_w*0.05, cell_w*0.05)
            jitter_y = random.uniform(-cell_h*0.05, cell_h*0.05)
            
            sub_minx = cmx + cell_w * gap + jitter_x
            sub_miny = cmy + cell_h * gap + jitter_y
            sub_maxx = cmx + cell_w * (1 - gap) + jitter_x
            sub_maxy = cmy + cell_h * (1 - gap) + jitter_y
            
            sub_minx = max(minx, sub_minx)
            sub_miny = max(miny, sub_miny)
            sub_maxx = min(maxx, sub_maxx)
            sub_maxy = min(maxy, sub_maxy)
            
            if sub_maxx > sub_minx and sub_maxy > sub_miny:
                child = generate_deep_rtree((sub_minx, sub_miny, sub_maxx, sub_maxy), current_depth + 1, max_depth)
                node.add_child(child)
                
    return node

def flatten_tree(root):
    nodes = []
    def _recurse(node):
        nodes.append(node)
        for child in node.children:
            _recurse(child)
    _recurse(root)
    return nodes

# --- 2. Search Logic ---
def get_search_trace(root, query_shape, filter_func):
    visited_ids = []
    
    def _search(node):
        # Check filter
        if not filter_func(node.mbr, query_shape):
            return # Prune
        
        # Visit
        visited_ids.append(node.id)
        
        if not node.is_leaf:
            for child in node.children:
                _search(child)
                
    _search(root)
    return visited_ids

# --- 3. Visualization ---
def get_linewidth(depth):
    # Root/Level 1: 2.0
    # Level 2: 1.0
    # Level 3 (Leaf): 0.5
    if depth <= 1: return 2.0
    if depth == 2: return 1.0
    return 0.5

def create_baseline_image(all_nodes, output_path):
    if os.path.exists(output_path):
        print(f"Baseline exists: {output_path}")
        return

    fig, ax = plt.subplots(figsize=(10, 10))
    ax.set_xlim(0, SPACE_SIZE)
    ax.set_ylim(0, SPACE_SIZE)
    ax.set_aspect('equal')
    ax.axis('off')
    
    sorted_nodes = sorted(all_nodes, key=lambda n: n.depth)
    
    patches_list = []
    linewidths = []
    
    for node in sorted_nodes:
        x, y = node.mbr.exterior.xy
        poly = patches.Polygon(list(zip(x, y)), closed=True)
        patches_list.append(poly)
        linewidths.append(get_linewidth(node.depth))
        
    pc = PatchCollection(patches_list, facecolors='none', edgecolors=COLOR_UNVISITED, linewidths=linewidths)
    ax.add_collection(pc)
    
    plt.savefig(output_path, dpi=150, bbox_inches='tight', pad_inches=0)
    plt.close(fig)
    print(f"Saved Baseline: {output_path}")

def create_animation(all_nodes, visited_ids, query_shape, query_mbr, title, output_path):
    fig, ax = plt.subplots(figsize=(10, 10))
    ax.set_xlim(0, SPACE_SIZE)
    ax.set_ylim(0, SPACE_SIZE)
    ax.set_aspect('equal')
    ax.axis('off')
    
    sorted_nodes = sorted(all_nodes, key=lambda n: n.depth)
    node_id_to_index = {node.id: i for i, node in enumerate(sorted_nodes)}
    
    patches_list = []
    linewidths = []
    
    for node in sorted_nodes:
        x, y = node.mbr.exterior.xy
        poly = patches.Polygon(list(zip(x, y)), closed=True)
        patches_list.append(poly)
        linewidths.append(get_linewidth(node.depth))
        
    # Initial: All Black
    pc = PatchCollection(patches_list, facecolors='none', edgecolors=COLOR_UNVISITED, linewidths=linewidths)
    ax.add_collection(pc)
    
    # Plot Query MBR (Dashed)
    if query_mbr:
        qmx, qmy = query_mbr.exterior.xy
        ax.plot(qmx, qmy, color=COLOR_QUERY, linestyle='--', linewidth=1.5, label='Query MBR')
        
    # Plot Query Triangle (Thick Blue)
    qx, qy = query_shape.exterior.xy
    ax.plot(qx, qy, color=COLOR_QUERY, linewidth=3, label='Query')
    
    # Counter Text
    text_artist = ax.text(0.02, 0.98, "Visited Nodes: 0", transform=ax.transAxes, 
                          fontsize=14, fontweight='bold', color='black',
                          bbox=dict(facecolor='white', alpha=0.9, edgecolor='none'))
    
    # Animation Logic
    current_edgecolors = [COLOR_UNVISITED] * len(sorted_nodes)
    
    # Pre-calculate batches
    batches = [visited_ids[i:i + BATCH_SIZE] for i in range(0, len(visited_ids), BATCH_SIZE)]
    
    # Frames: Start(10) + Batches + Pause
    num_batches = len(batches)
    pause_frames = 15
    start_frames = 10 # Show 0 for a bit
    total_frames = start_frames + num_batches + pause_frames
    
    pbar = tqdm(total=total_frames, desc=f"Generating {os.path.basename(output_path)}")
    
    def update(frame):
        pbar.update(1)
        
        if frame < start_frames:
            text_artist.set_text("Visited Nodes: 0")
            return pc, text_artist

        # Adjust frame index for batches
        batch_idx = frame - start_frames
        
        # If in batch range
        if batch_idx < num_batches:
            batch_ids = batches[batch_idx]
            for vid in batch_ids:
                if vid in node_id_to_index:
                    idx = node_id_to_index[vid]
                    current_edgecolors[idx] = COLOR_VISITED
            
            pc.set_edgecolors(current_edgecolors)
            
            # Update Counter
            current_count = min((batch_idx + 1) * BATCH_SIZE, len(visited_ids))
            text_artist.set_text(f"Visited Nodes: {current_count}")
            
        return pc, text_artist
    
    ani = FuncAnimation(fig, update, frames=total_frames, blit=True, interval=50)
    ani.save(output_path, writer=PillowWriter(fps=15))
    pbar.close()
    plt.close(fig)
    print(f"Saved Animation: {output_path}")

# --- Main ---
def main():
    random.seed(42)
    
    print("1. Generating Deep R-Tree...")
    root = generate_deep_rtree((0, 0, SPACE_SIZE, SPACE_SIZE), 0, MAX_DEPTH)
    all_nodes = flatten_tree(root)
    print(f"   Total Nodes: {len(all_nodes)}")
    
    query_triangle = Polygon([(100, 100), (900, 800), (800, 100)])
    query_envelope = query_triangle.envelope
    
    print("2. Generating Baseline Image...")
    create_baseline_image(all_nodes, os.path.join(ASSETS_DIR, '00_baseline_clean.png'))
    
    print("3. Tracing Search Paths...")
    visited_standard = get_search_trace(root, query_envelope, lambda m, q: m.intersects(q))
    visited_ar = get_search_trace(root, query_triangle, consistent)
    
    print(f"   Standard Visits: {len(visited_standard)}")
    print(f"   AR Filter Visits: {len(visited_ar)}")
    
    print("4. Generating Standard Animation...")
    create_animation(all_nodes, visited_standard, query_triangle, query_envelope,
                     "Standard Search", 
                     os.path.join(ASSETS_DIR, '01_standard_clean.gif'))
    
    print("5. Generating AR Filter Animation...")
    create_animation(all_nodes, visited_ar, query_triangle, None,
                     "AR Filter", 
                     os.path.join(ASSETS_DIR, '02_ar_filter_clean.gif'))
    
    print("Done!")

if __name__ == "__main__":
    main()
