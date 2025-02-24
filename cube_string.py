# cube_string.py
# Make sure to install the kociemba package with:
# pip install kociemba
# Also install python-dotenv and the gemini client as required.

import os
from dotenv import load_dotenv
import kociemba  # Cube solver module
from google import genai  # Gemini client

# Load environment variables from .env file
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("❌ ERROR: GEMINI_API_KEY is missing! Make sure it's set in the environment.")

# Instantiate Gemini client
client = genai.Client(api_key=GEMINI_API_KEY)

def vertical_flip(grid):
    """Flip a 3×3 grid vertically (reverse the order of rows)."""
    return grid[::-1]

def horizontal_flip(grid):
    """Flip a 3×3 grid horizontally (reverse each row)."""
    return [row[::-1] for row in grid]

def generate_cube_string(face_assignment):
    """
    Given a dictionary mapping face labels ("U", "R", "F", "D", "L", "B")
    to 3×3 grids, assemble and return the continuous 54-character color cube string,
    reading the faces in URFDLB order without applying any inversions.
    """
    cube_string = "".join(
        "".join(row) for face in ["U", "R", "F", "D", "L", "B"]
        for row in face_assignment[face]
    )
    return cube_string

def convert_color_to_kociemba(color_cube_string):
    """
    Convert the color cube string to Kociemba notation using the mapping:
      W -> U, R -> R, G -> F, Y -> D, O -> L, B -> B.
    Returns the converted 54-character string.
    """
    mapping = {'W': 'U', 'R': 'R', 'G': 'F', 'Y': 'D', 'O': 'L', 'B': 'B'}
    try:
        return "".join(mapping[ch] for ch in color_cube_string)
    except KeyError as e:
        return None

def solve_cube(kociemba_cube_string):
    """
    Call the kociemba solver on the provided cube string.
    Returns the solution moves (or an error message if the cube is unsolvable).
    """
    try:
        solution = kociemba.solve(kociemba_cube_string)
    except Exception as e:
        solution = f"Error solving cube: {e}"
    return solution



if __name__ == '__main__':
    # For standalone testing, using sample grids for each face.
    face_assignment = {
        "U": [
            ["G", "Y", "Y"],
            ["W", "W", "G"],
            ["W", "R", "W"],
        ],
        "R": [
            ["O", "R", "B"],
            ["O", "R", "W"],
            ["O", "R", "W"],
        ],
        "F": [
            ["R", "Y", "B"],
            ["G", "G", "B"],
            ["G", "G", "B"],
        ],
        "D": [
            ["Y", "Y", "Y"],
            ["Y", "Y", "W"],
            ["W", "W", "O"],
        ],
        "L": [
            ["R", "O", "G"],
            ["R", "O", "O"],
            ["R", "O", "O"],
        ],
        "B": [
            ["R", "B", "Y"],
            ["G", "B", "B"],
            ["G", "B", "B"],
        ],
    }
    
    # Build the color cube string without inversion.
    color_string = generate_cube_string(face_assignment)
    print("Color Cube String:")
    print(color_string)
    
    # Convert to Kociemba notation.
    kociemba_string = convert_color_to_kociemba(color_string)
    print("\nKociemba Cube String:")
    print(kociemba_string)
    
    # Solve the cube.
    cube_solution = solve_cube(kociemba_string)
    print("\nKociemba Solver Output:")
    print(cube_solution)

