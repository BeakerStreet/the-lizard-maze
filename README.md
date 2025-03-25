# The Lizard Maze

A simple Flask web application that generates and displays a maze with:
- One entrance and one exit
- A center hub with 18-24 paths converging
- All paths provide access back to the entrance
- Only one path leads to the exit

## Installation

1. Clone this repository
2. Create a virtual environment (optional but recommended):
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install the requirements:
   ```
   pip install -r requirements.txt
   ```

## Running the Application

1. Start the Flask application:
   ```
   python app.py
   ```
2. Open your web browser and navigate to:
   ```
   http://127.0.0.1:5000
   ```

## Features

- Dynamic maze generation on each page refresh
- Visual representation with color-coded elements:
  - Green: Entrance
  - Red: Exit
  - Orange: Center hub
  - Light gray: Paths
  - Dark blue: Walls
- Generate a new maze by clicking the button 