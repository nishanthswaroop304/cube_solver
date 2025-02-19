# cube_string.py
# Make sure to install the kociemba package with:
# pip install kociemba

import kociemba  # Cube solver module

def vertical_flip(grid):
    """Flip a 3×3 grid vertically (reverse the order of rows)."""
    return grid[::-1]

def horizontal_flip(grid):
    """Flip a 3×3 grid horizontally (reverse each row)."""
    return [row[::-1] for row in grid]

def generate_cube_string(face_assignment):
    """
    Given a dictionary mapping face labels ("U", "R", "F", "D", "L", "B")
    to 3×3 grids, apply the following corrections:
      - U: vertical flip
      - R: horizontal flip
      - F: horizontal flip
      - D: vertical flip
      - L: horizontal flip
      - B: horizontal flip
    Then assemble and return the continuous 54-character color cube string,
    reading the faces in URFDLB order.
    """
    corrected_faces = {}
    corrected_faces["U"] = vertical_flip(face_assignment["U"])
    corrected_faces["R"] = horizontal_flip(face_assignment["R"])
    corrected_faces["F"] = horizontal_flip(face_assignment["F"])
    corrected_faces["D"] = vertical_flip(face_assignment["D"])
    corrected_faces["L"] = horizontal_flip(face_assignment["L"])
    corrected_faces["B"] = horizontal_flip(face_assignment["B"])
    
    cube_string = "".join(
        "".join(row) for face in ["U", "R", "F", "D", "L", "B"]
        for row in corrected_faces[face]
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
    # For standalone testing:
    face_assignment = {
        "U": [
            ["O", "W", "R"],
            ["O", "W", "B"],
            ["R", "G", "W"],
        ],
        "R": [
            ["G", "O", "W"],
            ["R", "R", "G"],
            ["O", "O", "R"],
        ],
        "F": [
            ["B", "R", "B"],
            ["W", "G", "Y"],
            ["Y", "Y", "O"],
        ],
        "D": [
            ["O", "W", "Y"],
            ["Y", "Y", "G"],
            ["W", "G", "B"],
        ],
        "L": [
            ["W", "W", "Y"],
            ["O", "O", "B"],
            ["G", "R", "B"],
        ],
        "B": [
            ["G", "R", "R"],
            ["Y", "B", "B"],
            ["Y", "B", "G"],
        ],
    }
    
    color_string = generate_cube_string(face_assignment)
    kociemba_string = convert_color_to_kociemba(color_string)
    solution = solve_cube(kociemba_string)
    
    print("Color Cube String:")
    print(color_string)
    print("\nKociemba Cube String:")
    print(kociemba_string)
    print("\nKociemba Solver Output:")
    print(solution)
