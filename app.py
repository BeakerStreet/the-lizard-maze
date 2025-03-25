from flask import Flask, render_template
import random
import math

app = Flask(__name__)

class Maze:
    def __init__(self, size=64, num_paths=2):
        self.size = size
        self.grid = [[" " for _ in range(size)] for _ in range(size)]
        self.center = (size // 2, size // 2)
        self.entrance = (0, size // 2)
        self.exit = (size - 1, size // 2)
        self.generate()
    
    def generate(self):
        # Create empty space in the middle
        cx, cy = self.center
        empty_size = 10  # Size of the empty space
        for i in range(-empty_size, empty_size+1):
            for j in range(-empty_size, empty_size+1):
                if 0 <= cx+i < self.size and 0 <= cy+j < self.size:
                    self.grid[cx+i][cy+j] = "."  # Empty space
        
        # Mark the entrance and exit
        self.grid[self.entrance[0]][self.entrance[1]] = "E"  # Entrance
        self.grid[self.exit[0]][self.exit[1]] = "X"  # Exit
        
        border_offset = 3  # Offset from the actual border
        min_straight = 5   # Minimum straight segment length
        
        # Dictionary to store intersection points for later connections
        intersection_points = {}
        
        # Create left path with 90-degree turns
        # Start from entrance and create path segments with 90-degree turns
        start_x, start_y = self.entrance[0] + 1, self.entrance[1]
        
        # Path segments for left side
        segments = [
            # Down from entrance
            ((start_x, start_y), (start_x + min_straight, start_y)),
            # Down to bottom border
            ((start_x + min_straight, start_y), (start_x + min_straight, self.size - border_offset)),
            # Left along bottom
            ((start_x + min_straight, self.size - border_offset), (border_offset, self.size - border_offset)),
            # Up along left border
            ((border_offset, self.size - border_offset), (border_offset, cy + min_straight)),
            # Right toward center (horizontal approach to center)
            ((border_offset, cy + min_straight), (cx - empty_size - 1, cy + min_straight))
        ]
        
        # Store intersection points where other paths can connect
        intersection_points['left_bottom'] = (border_offset + 15, self.size - border_offset)
        intersection_points['left_vertical'] = (border_offset, cy - 10)
        intersection_points['left_approach'] = (cx - empty_size - 8, cy + min_straight)
        
        for segment in segments:
            self.create_straight_path(segment[0], segment[1])
        
        # Create right path with 90-degree turns
        # Path segments for right side
        segments = [
            # Down from entrance
            ((start_x, start_y), (start_x + min_straight, start_y)),
            # Up towards top border
            ((start_x + min_straight, start_y), (start_x + min_straight, border_offset)), 
            # Right along top border
            ((start_x + min_straight, border_offset), (self.size - border_offset, border_offset)),
            # Down along right border
            ((self.size - border_offset, border_offset), (self.size - border_offset, cy - min_straight)),
            # Left toward center (horizontal approach to center)
            ((self.size - border_offset, cy - min_straight), (cx + empty_size + 1, cy - min_straight))
        ]
        
        # Store intersection points
        intersection_points['right_top'] = (self.size - border_offset - 15, border_offset)
        intersection_points['right_vertical'] = (self.size - border_offset, cy + 10)
        intersection_points['right_approach'] = (cx + empty_size + 8, cy - min_straight)
        
        for segment in segments:
            self.create_straight_path(segment[0], segment[1])
        
        # Create path from center to exit (with 90-degree approach)
        # Create a path that exits the center horizontally then turns toward exit
        exit_segments = [
            # Right from center
            ((cx + empty_size + 1, cy), (cx + empty_size + min_straight, cy)),
            # Down to exit y-level
            ((cx + empty_size + min_straight, cy), (cx + empty_size + min_straight, self.exit[1])),
            # Right to exit
            ((cx + empty_size + min_straight, self.exit[1]), (self.exit[0] - 1, self.exit[1]))
        ]
        
        # Store intersection point for exit path
        intersection_points['exit_vertical'] = (cx + empty_size + min_straight, cy + 10)
        intersection_points['exit_horizontal'] = (cx + empty_size + min_straight + 7, self.exit[1])
        
        for segment in exit_segments:
            self.create_straight_path(segment[0], segment[1])
            
        # Add 6 additional paths, ensuring connections to other paths or center
        
        # Path 1: Top-left to center (top approach)
        path1_segments = [
            # Create a vertical path from the top-left area
            ((border_offset + 10, border_offset), (border_offset + 10, border_offset + 15)),
            # Right toward center region
            ((border_offset + 10, border_offset + 15), (cx - empty_size - 1, border_offset + 15))
        ]
        
        # Store intersection point
        intersection_points['path1_vertical'] = (border_offset + 10, border_offset + 10)
        intersection_points['path1_horizontal'] = (border_offset + 25, border_offset + 15)
        
        # Connect to another path
        path1_connect_segments = [
            # Path 1 connect to right top
            ((border_offset + 10, border_offset), (intersection_points['right_top'][0], border_offset))
        ]
        
        for segment in path1_segments + path1_connect_segments:
            self.create_straight_path(segment[0], segment[1])
            
        # Path 2: Top-right to center (top approach)
        path2_segments = [
            # Create a vertical path from the top-right area
            ((self.size - border_offset - 10, border_offset), (self.size - border_offset - 10, border_offset + 25)),
            # Left toward center region
            ((self.size - border_offset - 10, border_offset + 25), (cx + empty_size + 1, border_offset + 25))
        ]
        
        # Store intersection point
        intersection_points['path2_vertical'] = (self.size - border_offset - 10, border_offset + 12)
        intersection_points['path2_horizontal'] = (self.size - border_offset - 25, border_offset + 25)
        
        # Connect to another path - connects to exit path
        path2_connect_segments = [
            # Connect to exit path
            ((self.size - border_offset - 10, border_offset + 25), (self.size - border_offset - 10, cy - min_straight))
        ]
        
        for segment in path2_segments + path2_connect_segments:
            self.create_straight_path(segment[0], segment[1])
            
        # Path 3: Bottom-left to center (bottom approach)
        path3_segments = [
            # Create a vertical path from the bottom-left area
            ((border_offset + 20, self.size - border_offset), (border_offset + 20, self.size - border_offset - 15)),
            # Right toward center region
            ((border_offset + 20, self.size - border_offset - 15), (cx - empty_size - 1, self.size - border_offset - 15))
        ]
        
        # Store intersection point
        intersection_points['path3_vertical'] = (border_offset + 20, self.size - border_offset - 8)
        intersection_points['path3_horizontal'] = (cx - empty_size - 10, self.size - border_offset - 15)
        
        # Connect to another path - connects to left bottom
        path3_connect_segments = [
            # Connect to left bottom path
            ((border_offset + 20, self.size - border_offset), (intersection_points['left_bottom'][0], self.size - border_offset))
        ]
        
        for segment in path3_segments + path3_connect_segments:
            self.create_straight_path(segment[0], segment[1])
            
        # Path 4: Bottom-right to center (bottom approach)
        path4_segments = [
            # Create a vertical path from the bottom-right area
            ((self.size - border_offset - 15, self.size - border_offset), (self.size - border_offset - 15, self.size - border_offset - 25)),
            # Left toward center region
            ((self.size - border_offset - 15, self.size - border_offset - 25), (cx + empty_size + 1, self.size - border_offset - 25))
        ]
        
        # Add intersection point
        intersection_points['bottom_right'] = (self.size - border_offset - 15, self.size - border_offset - 12)
        intersection_points['path4_horizontal'] = (cx + empty_size + 15, self.size - border_offset - 25)
        
        # Connect to another path - connects to right vertical
        path4_connect_segments = [
            # Connect to right vertical path
            ((self.size - border_offset - 15, self.size - border_offset), (self.size - border_offset, self.size - border_offset))
        ]
        
        for segment in path4_segments + path4_connect_segments:
            self.create_straight_path(segment[0], segment[1])
            
        # Path 5: Left side to center (with a few turns)
        path5_segments = [
            # Start from left edge, mid-top
            ((border_offset, cy - 15), (border_offset + 12, cy - 15)),
            # Down
            ((border_offset + 12, cy - 15), (border_offset + 12, cy - 5)),
            # Right to center
            ((border_offset + 12, cy - 5), (cx - empty_size - 1, cy - 5))
        ]
        
        # Store intersection point
        intersection_points['path5_turn'] = (border_offset + 12, cy - 10)
        
        # Connect to another path - directly connects to left vertical
        path5_connect_segments = [
            # Already connects to left vertical at the start point
        ]
        
        for segment in path5_segments + path5_connect_segments:
            self.create_straight_path(segment[0], segment[1])
            
        # Path 6: Right side to center (with a few turns)
        path6_segments = [
            # Start from right edge, mid-bottom
            ((self.size - border_offset, cy + 15), (self.size - border_offset - 12, cy + 15)),
            # Up
            ((self.size - border_offset - 12, cy + 15), (self.size - border_offset - 12, cy + 5)),
            # Left to center
            ((self.size - border_offset - 12, cy + 5), (cx + empty_size + 1, cy + 5))
        ]
        
        # Store intersection point
        intersection_points['path6_turn'] = (self.size - border_offset - 12, cy + 10)
        
        # Connect to exit path
        path6_connect_segments = [
            # Connect to exit path
            ((self.size - border_offset - 12, cy + 15), (intersection_points['exit_vertical'][0], cy + 15))
        ]
        
        for segment in path6_segments + path6_connect_segments:
            self.create_straight_path(segment[0], segment[1])
        
        # Additional connections between paths to ensure full connectivity
        additional_connections = [
            # Connect path 1 and path 5
            ((border_offset + 10, border_offset + 15), (border_offset + 12, cy - 15)),
            # Connect path 3 and path 4 via bottom
            ((border_offset + 20, self.size - border_offset - 10), (self.size - border_offset - 15, self.size - border_offset - 10)),
            # Connect path 2 and path 6
            ((self.size - border_offset - 10, border_offset + 15), (self.size - border_offset - 12, cy + 5))
        ]
        
        for segment in additional_connections:
            # Create intermediate points to ensure 90-degree turns
            self.create_l_shaped_path(segment[0], segment[1])
        
        # Add 15 more paths
        
        # Path 7: Top side of center, left half
        path7_segments = [
            # Direct horizontal approach to center
            ((cx - 20, border_offset), (cx - 20, border_offset + 15)),
            ((cx - 20, border_offset + 15), (cx - empty_size - 1, border_offset + 15))
        ]
        
        # Store intersection point
        intersection_points['path7_vertical'] = (cx - 20, border_offset + 10)
        
        # Connect path 7 to other paths
        path7_connect_segments = [
            # Connect horizontally to existing path
            ((cx - 20, border_offset), (border_offset + 20, border_offset))
        ]
        
        for segment in path7_segments + path7_connect_segments:
            self.create_straight_path(segment[0], segment[1])
        
        # Path 8: Top side of center, right half
        path8_segments = [
            # Direct horizontal approach to center
            ((cx + 20, border_offset), (cx + 20, border_offset + 15)),
            ((cx + 20, border_offset + 15), (cx + empty_size + 1, border_offset + 15))
        ]
        
        # Store intersection point
        intersection_points['path8_vertical'] = (cx + 20, border_offset + 10)
        
        # Connect path 8 to other paths
        path8_connect_segments = [
            # Connect horizontally to existing path
            ((cx + 20, border_offset), (self.size - border_offset - 20, border_offset))
        ]
        
        for segment in path8_segments + path8_connect_segments:
            self.create_straight_path(segment[0], segment[1])
        
        # Path 9: Bottom side of center, left half
        path9_segments = [
            # Direct horizontal approach to center
            ((cx - 15, self.size - border_offset), (cx - 15, self.size - border_offset - 15)),
            ((cx - 15, self.size - border_offset - 15), (cx - empty_size - 1, self.size - border_offset - 15))
        ]
        
        # Store intersection point
        intersection_points['path9_vertical'] = (cx - 15, self.size - border_offset - 10)
        
        # Connect path 9 to other paths
        path9_connect_segments = [
            # Connect horizontally to existing path
            ((cx - 15, self.size - border_offset), (border_offset + 20, self.size - border_offset))
        ]
        
        for segment in path9_segments + path9_connect_segments:
            self.create_straight_path(segment[0], segment[1])
        
        # Path 10: Bottom side of center, right half
        path10_segments = [
            # Direct horizontal approach to center
            ((cx + 15, self.size - border_offset), (cx + 15, self.size - border_offset - 15)),
            ((cx + 15, self.size - border_offset - 15), (cx + empty_size + 1, self.size - border_offset - 15))
        ]
        
        # Store intersection point
        intersection_points['path10_vertical'] = (cx + 15, self.size - border_offset - 10)
        
        # Connect path 10 to other paths
        path10_connect_segments = [
            # Connect horizontally to existing path
            ((cx + 15, self.size - border_offset), (self.size - border_offset - 15, self.size - border_offset))
        ]
        
        for segment in path10_segments + path10_connect_segments:
            self.create_straight_path(segment[0], segment[1])
        
        # Path 11: Left side of center, top half
        path11_segments = [
            # Direct vertical approach to center
            ((border_offset, cy - 20), (border_offset + 15, cy - 20)),
            ((border_offset + 15, cy - 20), (cx - empty_size - 1, cy - 20))
        ]
        
        # Store intersection point
        intersection_points['path11_horizontal'] = (border_offset + 10, cy - 20)
        
        # Connect path 11 to other paths
        path11_connect_segments = [
            # Connects to left vertical path already
        ]
        
        for segment in path11_segments + path11_connect_segments:
            self.create_straight_path(segment[0], segment[1])
        
        # Path 12: Left side of center, bottom half
        path12_segments = [
            # Direct vertical approach to center
            ((border_offset, cy + 20), (border_offset + 15, cy + 20)),
            ((border_offset + 15, cy + 20), (cx - empty_size - 1, cy + 20))
        ]
        
        # Store intersection point
        intersection_points['path12_horizontal'] = (border_offset + 10, cy + 20)
        
        # Connect path 12 to other paths - connects to left border
        
        for segment in path12_segments:
            self.create_straight_path(segment[0], segment[1])
        
        # Path 13: Right side of center, top half
        path13_segments = [
            # Direct vertical approach to center
            ((self.size - border_offset, cy - 20), (self.size - border_offset - 15, cy - 20)),
            ((self.size - border_offset - 15, cy - 20), (cx + empty_size + 1, cy - 20))
        ]
        
        # Store intersection point
        intersection_points['path13_horizontal'] = (self.size - border_offset - 10, cy - 20)
        
        # Connect path 13 to other paths - connects to right border
        
        for segment in path13_segments:
            self.create_straight_path(segment[0], segment[1])
        
        # Path 14: Right side of center, bottom half
        path14_segments = [
            # Direct vertical approach to center
            ((self.size - border_offset, cy + 20), (self.size - border_offset - 15, cy + 20)),
            ((self.size - border_offset - 15, cy + 20), (cx + empty_size + 1, cy + 20))
        ]
        
        # Store intersection point
        intersection_points['path14_horizontal'] = (self.size - border_offset - 10, cy + 20)
        
        # Connect path 14 to other paths - connects to right border
        
        for segment in path14_segments:
            self.create_straight_path(segment[0], segment[1])
        
        # Path 15: Diagonal-inspired approach top-left
        path15_segments = [
            # Start from top-left area with 90-degree turns
            ((border_offset + 25, border_offset + 5), (border_offset + 25, border_offset + 30)),
            ((border_offset + 25, border_offset + 30), (border_offset + 40, border_offset + 30)),
            ((border_offset + 40, border_offset + 30), (border_offset + 40, cy - empty_size - 5)),
            ((border_offset + 40, cy - empty_size - 5), (cx - empty_size - 1, cy - empty_size - 5))
        ]
        
        # Connect path 15 to other paths
        path15_connect_segments = [
            # Connect to path 1
            ((border_offset + 25, border_offset + 5), (border_offset + 10, border_offset + 5))
        ]
        
        for segment in path15_segments + path15_connect_segments:
            self.create_straight_path(segment[0], segment[1])
        
        # Path 16: Diagonal-inspired approach top-right
        path16_segments = [
            # Start from top-right area with 90-degree turns
            ((self.size - border_offset - 25, border_offset + 5), (self.size - border_offset - 25, border_offset + 30)),
            ((self.size - border_offset - 25, border_offset + 30), (self.size - border_offset - 40, border_offset + 30)),
            ((self.size - border_offset - 40, border_offset + 30), (self.size - border_offset - 40, cy - empty_size - 5)),
            ((self.size - border_offset - 40, cy - empty_size - 5), (cx + empty_size + 1, cy - empty_size - 5))
        ]
        
        # Connect path 16 to other paths
        path16_connect_segments = [
            # Connect to path 2
            ((self.size - border_offset - 25, border_offset + 5), (self.size - border_offset - 10, border_offset + 5))
        ]
        
        for segment in path16_segments + path16_connect_segments:
            self.create_straight_path(segment[0], segment[1])
        
        # Path 17: Diagonal-inspired approach bottom-left
        path17_segments = [
            # Start from bottom-left area with 90-degree turns
            ((border_offset + 30, self.size - border_offset - 5), (border_offset + 30, self.size - border_offset - 30)),
            ((border_offset + 30, self.size - border_offset - 30), (border_offset + 45, self.size - border_offset - 30)),
            ((border_offset + 45, self.size - border_offset - 30), (border_offset + 45, cy + empty_size + 5)),
            ((border_offset + 45, cy + empty_size + 5), (cx - empty_size - 1, cy + empty_size + 5))
        ]
        
        # Connect path 17 to other paths
        path17_connect_segments = [
            # Connect to path 3
            ((border_offset + 30, self.size - border_offset - 5), (border_offset + 20, self.size - border_offset - 5))
        ]
        
        for segment in path17_segments + path17_connect_segments:
            self.create_straight_path(segment[0], segment[1])
        
        # Path 18: Diagonal-inspired approach bottom-right
        path18_segments = [
            # Start from bottom-right area with 90-degree turns
            ((self.size - border_offset - 30, self.size - border_offset - 5), (self.size - border_offset - 30, self.size - border_offset - 30)),
            ((self.size - border_offset - 30, self.size - border_offset - 30), (self.size - border_offset - 45, self.size - border_offset - 30)),
            ((self.size - border_offset - 45, self.size - border_offset - 30), (self.size - border_offset - 45, cy + empty_size + 5)),
            ((self.size - border_offset - 45, cy + empty_size + 5), (cx + empty_size + 1, cy + empty_size + 5))
        ]
        
        # Connect path 18 to other paths
        path18_connect_segments = [
            # Connect to path 4
            ((self.size - border_offset - 30, self.size - border_offset - 5), (self.size - border_offset - 15, self.size - border_offset - 5))
        ]
        
        for segment in path18_segments + path18_connect_segments:
            self.create_straight_path(segment[0], segment[1])
        
        # Path 19: Intermediate path connecting quadrants
        path19_segments = [
            # Horizontal path through middle
            ((border_offset + 20, cy - 30), (self.size - border_offset - 20, cy - 30))
        ]
        
        # Connect path 19 to other paths
        path19_connect_segments = [
            # Connect to left and right sides vertically
            ((border_offset + 20, cy - 30), (border_offset + 20, border_offset + 20)),
            ((self.size - border_offset - 20, cy - 30), (self.size - border_offset - 20, border_offset + 20))
        ]
        
        for segment in path19_segments + path19_connect_segments:
            self.create_straight_path(segment[0], segment[1])
        
        # Path 20: Intermediate path connecting quadrants
        path20_segments = [
            # Horizontal path through middle
            ((border_offset + 20, cy + 30), (self.size - border_offset - 20, cy + 30))
        ]
        
        # Connect path 20 to other paths
        path20_connect_segments = [
            # Connect to left and right sides vertically
            ((border_offset + 20, cy + 30), (border_offset + 20, self.size - border_offset - 20)),
            ((self.size - border_offset - 20, cy + 30), (self.size - border_offset - 20, self.size - border_offset - 20))
        ]
        
        for segment in path20_segments + path20_connect_segments:
            self.create_straight_path(segment[0], segment[1])
        
        # Path 21: Grid path horizontal left top
        path21_segments = [
            # Horizontal grid path
            ((border_offset + 15, cy - 40), (cx - empty_size - 10, cy - 40))
        ]
        
        for segment in path21_segments:
            self.create_straight_path(segment[0], segment[1])
            
        # Connect to other paths with vertical segments
        self.create_straight_path((border_offset + 15, cy - 40), (border_offset + 15, border_offset + 15))
        self.create_straight_path((cx - empty_size - 10, cy - 40), (cx - empty_size - 10, cy - 20))
        
        # Add additional connections for remaining paths
        # These are just a sample - you can add more connections as needed
        additional_new_connections = [
            # Connect various paths in the grid for better connectivity
            ((border_offset + 30, border_offset + 30), (border_offset + 30, cy - 30)),
            ((self.size - border_offset - 30, border_offset + 30), (self.size - border_offset - 30, cy - 30)),
            ((border_offset + 30, self.size - border_offset - 30), (border_offset + 30, cy + 30)),
            ((self.size - border_offset - 30, self.size - border_offset - 30), (self.size - border_offset - 30, cy + 30)),
            
            # Create some additional cross-connections
            ((cx - 20, border_offset + 20), (cx - 20, cy - 30)),
            ((cx + 20, border_offset + 20), (cx + 20, cy - 30)),
            ((cx - 20, self.size - border_offset - 20), (cx - 20, cy + 30)),
            ((cx + 20, self.size - border_offset - 20), (cx + 20, cy + 30)),
            
            # Connect some of the center approach paths
            ((cx - empty_size - 15, cy - 10), (cx - empty_size - 15, cy + 10)),
            ((cx + empty_size + 15, cy - 10), (cx + empty_size + 15, cy + 10))
        ]
        
        for segment in additional_new_connections:
            self.create_straight_path(segment[0], segment[1])
    
    def create_l_shaped_path(self, start, end):
        """Create an L-shaped path with a 90-degree turn between start and end"""
        x0, y0 = start
        x1, y1 = end
        
        # Create the intermediate point for the 90-degree turn
        # Choose to go horizontal first then vertical
        if random.random() < 0.5:
            self.create_straight_path((x0, y0), (x1, y0))  # Horizontal segment
            self.create_straight_path((x1, y0), (x1, y1))  # Vertical segment
        else:
            self.create_straight_path((x0, y0), (x0, y1))  # Vertical segment
            self.create_straight_path((x0, y1), (x1, y1))  # Horizontal segment
    
    def create_straight_path(self, start, end):
        """Create a straight path between two points (either horizontal or vertical)"""
        x0, y0 = start
        x1, y1 = end
        
        # Make sure coordinates are in bounds
        x0 = max(0, min(x0, self.size - 1))
        y0 = max(0, min(y0, self.size - 1))
        x1 = max(0, min(x1, self.size - 1))
        y1 = max(0, min(y1, self.size - 1))
        
        # Horizontal line
        if y0 == y1:
            start_x, end_x = min(x0, x1), max(x0, x1)
            for x in range(start_x, end_x + 1):
                if 0 <= x < self.size and 0 <= y0 < self.size:
                    if self.grid[x][y0] == " ":
                        self.grid[x][y0] = "."
        # Vertical line
        elif x0 == x1:
            start_y, end_y = min(y0, y1), max(y0, y1)
            for y in range(start_y, end_y + 1):
                if 0 <= x0 < self.size and 0 <= y < self.size:
                    if self.grid[x0][y] == " ":
                        self.grid[x0][y] = "."
    
    def to_html(self):
        html = '<div class="maze">'
        for i, row in enumerate(self.grid):
            html += '<div class="row">'
            for j, cell in enumerate(row):
                cell_class = "wall"
                if cell == ".":
                    cell_class = "path"
                elif cell == "E":
                    cell_class = "entrance"
                elif cell == "X":
                    cell_class = "exit"
                
                html += f'<div class="{cell_class}"></div>'
            html += '</div>'
        html += '</div>'
        return html

@app.route('/')
def index():
    maze = Maze()
    return render_template('index.html', maze_html=maze.to_html())

if __name__ == '__main__':
    app.run(debug=True, port=5001) 