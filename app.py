from flask import Flask, render_template, jsonify, request, redirect, url_for
import random
import math
import socket

app = Flask(__name__)

class Path:
    def __init__(self, id, label, segments, color="#ecf0f1", visible=True):
        self.id = id  # Unique identifier for the path
        self.label = label  # Display label for the path
        self.segments = segments  # List of segment tuples ((x1,y1), (x2,y2))
        self.color = color  # Color of the path
        self.visible = visible  # Whether the path is visible
        self.cells = []  # List of cells that make up the path
        
    def get_label_position(self):
        """Calculate a good position to place the label"""
        # Try to find a position near the middle of the path
        if len(self.segments) > 0:
            # Get the middle segment
            middle_segment = self.segments[len(self.segments) // 2]
            # Get the middle point of that segment
            (x0, y0), (x1, y1) = middle_segment
            return (int((x0 + x1) / 2), int((y0 + y1) / 2))
        return None

# Store the maze as a global variable to persist path visibility states
maze = None

class Maze:
    def __init__(self, size=64):
        self.size = size
        self.grid = [[" " for _ in range(size)] for _ in range(size)]
        self.center = (size // 2, size // 2)
        self.entrance = (0, size // 2)
        self.exit = (size - 1, size // 2)
        self.empty_size = 10  # Size of the empty space
        self.border_offset = 3  # Offset from the actual border
        self.min_straight = 5   # Minimum straight segment length
        
        # Dictionary to store all paths by ID
        self.paths = {}
        
        # Dictionary to map labels to path ids
        self.label_to_id = {}
        
        # Dictionary to store intersection points for later connections
        self.intersection_points = {}
        
        # Generate the maze
        self.generate()
    
    def generate(self):
        """Generate the maze with labeled paths"""
        # Create empty space in the middle
        self.create_center()
        
        # Mark entrance and exit
        self.create_entrance_exit()
        
        # Create and add all paths
        self.create_all_paths()
        
        # Draw all paths onto the grid
        self.reset_grid_and_draw_paths()
    
    def create_center(self):
        """Create the empty center space"""
        cx, cy = self.center
        for i in range(-self.empty_size, self.empty_size+1):
            for j in range(-self.empty_size, self.empty_size+1):
                if 0 <= cx+i < self.size and 0 <= cy+j < self.size:
                    self.grid[cx+i][cy+j] = "."  # Empty space
    
    def create_entrance_exit(self):
        """Mark the entrance and exit on the grid"""
        self.grid[self.entrance[0]][self.entrance[1]] = "E"  # Entrance
        self.grid[self.exit[0]][self.exit[1]] = "X"  # Exit
    
    def create_all_paths(self):
        """Create all paths in the maze"""
        cx, cy = self.center
        start_x, start_y = self.entrance[0] + 1, self.entrance[1]
        
        # Main border paths
        self.create_main_left_path(start_x, start_y, cx, cy)
        self.create_main_right_path(start_x, start_y, cx, cy)
        self.create_exit_path(cx, cy)
        
        # Additional paths
        self.create_additional_paths(cx, cy)
    
    def create_main_left_path(self, start_x, start_y, cx, cy):
        """Create the main left path that follows the border"""
        # Path segments for left side
        segments = [
            # Down from entrance
            ((start_x, start_y), (start_x + self.min_straight, start_y)),
            # Down to bottom border
            ((start_x + self.min_straight, start_y), (start_x + self.min_straight, self.size - self.border_offset)),
            # Left along bottom
            ((start_x + self.min_straight, self.size - self.border_offset), (self.border_offset, self.size - self.border_offset)),
            # Up along left border
            ((self.border_offset, self.size - self.border_offset), (self.border_offset, cy + self.min_straight)),
            # Right toward center (horizontal approach to center)
            ((self.border_offset, cy + self.min_straight), (cx - self.empty_size - 1, cy + self.min_straight))
        ]
        
        # Store intersection points
        self.intersection_points['left_bottom'] = (self.border_offset + 15, self.size - self.border_offset)
        self.intersection_points['left_vertical'] = (self.border_offset, cy - 10)
        self.intersection_points['left_approach'] = (cx - self.empty_size - 8, cy + self.min_straight)
        
        # Create the path object
        left_path = Path(
            id="main_left",
            label="Alpha",
            segments=segments
        )
        
        # Add to paths dictionary
        self.paths["main_left"] = left_path
        self.label_to_id["alpha"] = "main_left"
    
    def create_main_right_path(self, start_x, start_y, cx, cy):
        """Create the main right path that follows the border"""
        # Path segments for right side
        segments = [
            # Down from entrance
            ((start_x, start_y), (start_x + self.min_straight, start_y)),
            # Up towards top border
            ((start_x + self.min_straight, start_y), (start_x + self.min_straight, self.border_offset)), 
            # Right along top border
            ((start_x + self.min_straight, self.border_offset), (self.size - self.border_offset, self.border_offset)),
            # Down along right border
            ((self.size - self.border_offset, self.border_offset), (self.size - self.border_offset, cy - self.min_straight)),
            # Left toward center (horizontal approach to center)
            ((self.size - self.border_offset, cy - self.min_straight), (cx + self.empty_size + 1, cy - self.min_straight))
        ]
        
        # Store intersection points
        self.intersection_points['right_top'] = (self.size - self.border_offset - 15, self.border_offset)
        self.intersection_points['right_vertical'] = (self.size - self.border_offset, cy + 10)
        self.intersection_points['right_approach'] = (cx + self.empty_size + 8, cy - self.min_straight)
        
        # Create the path object
        right_path = Path(
            id="main_right",
            label="Beta",
            segments=segments
        )
        
        # Add to paths dictionary
        self.paths["main_right"] = right_path
        self.label_to_id["beta"] = "main_right"
    
    def create_exit_path(self, cx, cy):
        """Create the path from center to exit"""
        # Create path from center to exit (with 90-degree approach)
        segments = [
            # Right from center
            ((cx + self.empty_size + 1, cy), (cx + self.empty_size + self.min_straight, cy)),
            # Down to exit y-level
            ((cx + self.empty_size + self.min_straight, cy), (cx + self.empty_size + self.min_straight, self.exit[1])),
            # Right to exit
            ((cx + self.empty_size + self.min_straight, self.exit[1]), (self.exit[0] - 1, self.exit[1]))
        ]
        
        # Store intersection point for exit path
        self.intersection_points['exit_vertical'] = (cx + self.empty_size + self.min_straight, cy + 10)
        self.intersection_points['exit_horizontal'] = (cx + self.empty_size + self.min_straight + 7, self.exit[1])
        
        # Create the path object
        exit_path = Path(
            id="exit_path",
            label="Omega",
            segments=segments
        )
        
        # Add to paths dictionary
        self.paths["exit_path"] = exit_path
        self.label_to_id["omega"] = "exit_path"
    
    def create_additional_paths(self, cx, cy):
        """Create all additional paths"""
        # Create additional paths with labels
        self.create_path_with_segments(
            "path1", "Delta",
            [
                ((self.border_offset + 10, self.border_offset), (self.border_offset + 10, self.border_offset + 15)),
                ((self.border_offset + 10, self.border_offset + 15), (cx - self.empty_size - 1, self.border_offset + 15))
            ],
            [
                ((self.border_offset + 10, self.border_offset), (self.intersection_points['right_top'][0], self.border_offset))
            ]
        )
        
        self.create_path_with_segments(
            "path2", "Gamma",
            [
                ((self.size - self.border_offset - 10, self.border_offset), (self.size - self.border_offset - 10, self.border_offset + 25)),
                ((self.size - self.border_offset - 10, self.border_offset + 25), (cx + self.empty_size + 1, self.border_offset + 25))
            ],
            [
                ((self.size - self.border_offset - 10, self.border_offset + 25), (self.size - self.border_offset - 10, cy - self.min_straight))
            ]
        )
        
        self.create_path_with_segments(
            "path3", "Epsilon",
            [
                ((self.border_offset + 20, self.size - self.border_offset), (self.border_offset + 20, self.size - self.border_offset - 15)),
                ((self.border_offset + 20, self.size - self.border_offset - 15), (cx - self.empty_size - 1, self.size - self.border_offset - 15))
            ],
            [
                ((self.border_offset + 20, self.size - self.border_offset), (self.intersection_points['left_bottom'][0], self.size - self.border_offset))
            ]
        )
        
        self.create_path_with_segments(
            "path4", "Zeta",
            [
                ((self.size - self.border_offset - 15, self.size - self.border_offset), (self.size - self.border_offset - 15, self.size - self.border_offset - 25)),
                ((self.size - self.border_offset - 15, self.size - self.border_offset - 25), (cx + self.empty_size + 1, self.size - self.border_offset - 25))
            ],
            [
                ((self.size - self.border_offset - 15, self.size - self.border_offset), (self.size - self.border_offset, self.size - self.border_offset))
            ]
        )
        
        self.create_path_with_segments(
            "path5", "Eta",
            [
                ((self.border_offset, cy - 15), (self.border_offset + 12, cy - 15)),
                ((self.border_offset + 12, cy - 15), (self.border_offset + 12, cy - 5)),
                ((self.border_offset + 12, cy - 5), (cx - self.empty_size - 1, cy - 5))
            ],
            []
        )
        
        self.create_path_with_segments(
            "path6", "Theta",
            [
                ((self.size - self.border_offset, cy + 15), (self.size - self.border_offset - 12, cy + 15)),
                ((self.size - self.border_offset - 12, cy + 15), (self.size - self.border_offset - 12, cy + 5)),
                ((self.size - self.border_offset - 12, cy + 5), (cx + self.empty_size + 1, cy + 5))
            ],
            [
                ((self.size - self.border_offset - 12, cy + 15), (self.intersection_points['exit_vertical'][0], cy + 15))
            ]
        )
        
        # Add connections between paths
        connection_segments = [
            # Connect path 1 and path 5
            ((self.border_offset + 10, self.border_offset + 15), (self.border_offset + 12, cy - 15)),
            # Connect path 3 and path 4 via bottom
            ((self.border_offset + 20, self.size - self.border_offset - 10), (self.size - self.border_offset - 15, self.size - self.border_offset - 10)),
            # Connect path 2 and path 6
            ((self.size - self.border_offset - 10, self.border_offset + 15), (self.size - self.border_offset - 12, cy + 5))
        ]
        
        # Create connections path
        connections_path = Path(
            id="connections",
            label="Links",
            segments=[]
        )
        
        # Add l-shaped segments
        for start, end in connection_segments:
            l_segments = self.get_l_shaped_segments(start, end)
            connections_path.segments.extend(l_segments)
        
        # Add to paths dictionary
        self.paths["connections"] = connections_path
        self.label_to_id["links"] = "connections"
    
    def create_path_with_segments(self, path_id, label, main_segments, connection_segments=[]):
        """Helper to create a path with given segments"""
        segments = main_segments + connection_segments
        path = Path(
            id=path_id,
            label=label,
            segments=segments
        )
        self.paths[path_id] = path
        self.label_to_id[label.lower()] = path_id  # Store lowercase label to path ID mapping
    
    def get_l_shaped_segments(self, start, end):
        """Create an L-shaped path with a 90-degree turn between start and end"""
        x0, y0 = start
        x1, y1 = end
        
        # Create the intermediate point for the 90-degree turn
        # Choose to go horizontal first then vertical
        if random.random() < 0.5:
            return [
                ((x0, y0), (x1, y0)),  # Horizontal segment
                ((x1, y0), (x1, y1))   # Vertical segment
            ]
        else:
            return [
                ((x0, y0), (x0, y1)),  # Vertical segment
                ((x0, y1), (x1, y1))   # Horizontal segment
            ]
    
    def toggle_path(self, path_id_or_label):
        """Toggle the visibility of a path by its ID or label"""
        path_id = path_id_or_label
        
        # Check if the input is a label
        if path_id_or_label.lower() in self.label_to_id:
            path_id = self.label_to_id[path_id_or_label.lower()]
        
        if path_id in self.paths:
            self.paths[path_id].visible = not self.paths[path_id].visible
            self.reset_grid_and_draw_paths()
            return True, path_id
        return False, path_id_or_label
    
    def reset_grid_and_draw_paths(self):
        """Reset the grid and redraw all paths"""
        # Reset the grid (keep entrance, exit, and center)
        for i in range(self.size):
            for j in range(self.size):
                if (i, j) == self.entrance:
                    self.grid[i][j] = "E"
                elif (i, j) == self.exit:
                    self.grid[i][j] = "X"
                elif self.is_center(i, j):
                    self.grid[i][j] = "."
                else:
                    self.grid[i][j] = " "
        
        # Draw all visible paths
        self.draw_paths()
    
    def is_center(self, i, j):
        """Check if a cell is in the center area"""
        cx, cy = self.center
        return abs(i - cx) <= self.empty_size and abs(j - cy) <= self.empty_size
    
    def draw_paths(self):
        """Draw all path segments onto the grid"""
        # Draw each path's segments to the grid
        for path_id, path in self.paths.items():
            if path.visible:
                for segment in path.segments:
                    self.draw_segment(segment, path)
    
    def draw_segment(self, segment, path):
        """Draw a single segment on the grid with path information"""
        start, end = segment
        x0, y0 = start
        x1, y1 = end
        
        # Make sure coordinates are in bounds
        x0 = max(0, min(x0, self.size - 1))
        y0 = max(0, min(y0, self.size - 1))
        x1 = max(0, min(x1, self.size - 1))
        y1 = max(0, min(y1, self.size - 1))
        
        # Store all cells for this segment
        segment_cells = []
        
        # Horizontal line
        if y0 == y1:
            start_x, end_x = min(x0, x1), max(x0, x1)
            for x in range(start_x, end_x + 1):
                if 0 <= x < self.size and 0 <= y0 < self.size:
                    if self.grid[x][y0] == " ":
                        self.grid[x][y0] = "."
                    segment_cells.append((x, y0))
        # Vertical line
        elif x0 == x1:
            start_y, end_y = min(y0, y1), max(y0, y1)
            for y in range(start_y, end_y + 1):
                if 0 <= x0 < self.size and 0 <= y < self.size:
                    if self.grid[x0][y] == " ":
                        self.grid[x0][y] = "."
                    segment_cells.append((x0, y))
        
        # Add these cells to the path
        path.cells.extend(segment_cells)
    
    def to_html(self):
        """Generate HTML for the maze with path labels"""
        html = '<div class="maze">'
        
        # First create the maze cells
        for i, row in enumerate(self.grid):
            html += '<div class="row">'
            for j, cell in enumerate(row):
                cell_class = "wall"
                data_attrs = f'data-x="{i}" data-y="{j}"'
                
                if cell == ".":
                    cell_class = "path"
                elif cell == "E":
                    cell_class = "entrance"
                elif cell == "X":
                    cell_class = "exit"
                
                html += f'<div class="{cell_class}" {data_attrs}></div>'
            html += '</div>'
        html += '</div>'
        
        # Add labels container
        html += '<div class="path-labels">'
        
        # Now add labels for each path at their calculated positions
        for path_id, path in self.paths.items():
            if path.label and path.visible:  # Only show labels for visible paths
                label_pos = path.get_label_position()
                if label_pos:
                    x, y = label_pos
                    # Convert grid coordinates to pixel coordinates (10px per cell)
                    px = y * 10
                    py = x * 10
                    html += f'<div class="path-label" style="left: {px}px; top: {py}px;" data-path-id="{path_id}">{path.label}</div>'
        
        html += '</div>'
        
        return html

    def get_path_info(self):
        """Get information about all paths in the maze"""
        paths_info = {}
        for path_id, path in self.paths.items():
            label_pos = path.get_label_position()
            if label_pos:
                x, y = label_pos
                paths_info[path_id] = {
                    'id': path_id,
                    'label': path.label,
                    'visible': path.visible,
                    'color': path.color,
                    'labelPosition': {'x': y, 'y': x}  # Swap x and y for pixel coordinates
                }
        return paths_info

@app.route('/')
def index():
    global maze
    if maze is None:
        maze = Maze()
    
    # Check if reveal_all parameter is present
    reveal_all = request.args.get('reveal_all', '').lower() in ['true', '1', 'yes', 'y']
    
    if reveal_all:
        # Make all paths visible
        for path_id in maze.paths:
            maze.paths[path_id].visible = True
    else:
        # Make all paths hidden by default
        for path_id in maze.paths:
            maze.paths[path_id].visible = False
        
        # Check for path parameters in the URL
        visible_paths = request.args.getlist('path')
        if visible_paths:
            for path_name in visible_paths:
                # Convert to lowercase for case-insensitive matching
                path_name_lower = path_name.lower()
                
                # First check if it's a direct path ID
                if path_name in maze.paths:
                    maze.paths[path_name].visible = True
                # Then check if it's a path label
                elif path_name_lower in maze.label_to_id:
                    path_id = maze.label_to_id[path_name_lower]
                    maze.paths[path_id].visible = True
    
    # Redraw the maze with updated visibility
    maze.reset_grid_and_draw_paths()
    
    return render_template('index.html', maze_html=maze.to_html(), paths_info=maze.get_path_info())

@app.route('/toggle/<path_id_or_label>')
def toggle_path(path_id_or_label):
    global maze
    if maze is None:
        maze = Maze()
    
    success, path_id = maze.toggle_path(path_id_or_label)
    
    # Return path info after toggling
    path_info = None
    if success and path_id in maze.paths:
        path = maze.paths[path_id]
        path_info = {
            "id": path_id,
            "label": path.label,
            "visible": path.visible
        }
    
    return jsonify({
        "success": success,
        "path_id": path_id,
        "path_info": path_info
    })

@app.route('/paths')
def get_paths():
    global maze
    if maze is None:
        maze = Maze()
    
    return jsonify(maze.get_path_info())

@app.route('/toggle-all', methods=['POST'])
def toggle_all_paths():
    global maze
    if maze is None:
        maze = Maze()
    
    visible = request.json.get('visible', False)
    
    # Toggle all paths to the specified visibility
    for path_id in maze.paths:
        maze.paths[path_id].visible = visible
    
    maze.reset_grid_and_draw_paths()
    return jsonify({"success": True, "visible": visible})

@app.route('/labels')
def get_path_labels():
    global maze
    if maze is None:
        maze = Maze()
    
    # Create a dictionary mapping labels to path IDs
    labels = {}
    for path_id, path in maze.paths.items():
        labels[path.label.lower()] = path_id
    
    return jsonify(labels)

@app.route('/info')
def connection_info():
    """Display information about how to connect to the server"""
    # Get local IP address
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    
    # Create HTML response with connection information
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Maze Server Connection Info</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                line-height: 1.6;
            }
            .info-box {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 15px;
                margin: 20px 0;
            }
            code {
                background-color: #e0e0e0;
                padding: 2px 5px;
                border-radius: 3px;
                font-family: monospace;
            }
            h2 {
                border-bottom: 1px solid #ddd;
                padding-bottom: 10px;
            }
        </style>
    </head>
    <body>
        <h1>Maze Server Connection Information</h1>
        
        <div class="info-box">
            <h2>How to Connect</h2>
            <p>This server is now accessible from other computers on your network.</p>
            <p>Server is running at: <code>http://{0}:5002</code></p>
            <p>Others can access this maze by visiting the above URL in their web browsers.</p>
        </div>
        
        <div class="info-box">
            <h2>URL Parameters</h2>
            <p>Control visible paths with URL parameters:</p>
            <ul>
                <li><code>?path=alpha&path=beta</code> - Show specific paths by name</li>
                <li><code>?reveal_all=true</code> - Show all paths</li>
            </ul>
            <p>Example: <code>http://{0}:5002/?path=alpha&path=delta</code></p>
        </div>
        
        <div class="info-box">
            <h2>Available Path Names</h2>
            <p>The following path names are available:</p>
            <ul>
                <li><code>alpha</code> - Main left path</li>
                <li><code>beta</code> - Main right path</li>
                <li><code>delta</code> - Upper left path</li>
                <li><code>gamma</code> - Upper right path</li>
                <li><code>epsilon</code> - Lower left path</li>
                <li><code>zeta</code> - Lower right path</li>
                <li><code>eta</code> - Left middle path</li>
                <li><code>theta</code> - Right middle path</li>
                <li><code>omega</code> - Exit path</li>
                <li><code>links</code> - Connecting paths</li>
            </ul>
        </div>
        
        <p><a href="/">Return to Maze</a></p>
    </body>
    </html>
    """.format(local_ip)
    
    return html

@app.route('/ip')
def get_ip():
    """Return the server's IP address"""
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    return jsonify({
        "server_ip": local_ip,
        "port": 5002
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5002) 