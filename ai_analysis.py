import os
import PIL.Image
from google import genai
from dotenv import load_dotenv
import base64
import io
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS  # ✅ Added CORS support
from cube_string import generate_cube_string, convert_color_to_kociemba, solve_cube  # ✅ Import required functions

# Load variables from .env file
load_dotenv()

# Get API Key from environment variable
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("❌ ERROR: GEMINI_API_KEY is missing! Make sure it's set in the environment.")

client = genai.Client(api_key=API_KEY)

app = Flask(__name__)
CORS(app)  # ✅ Enable CORS for frontend access

@app.route("/")
def home():
    return render_template("index.html")

def parse_grid(response_text):
    """
    Convert AI output string to a structured 3x3 grid format.
    If AI response is invalid, return a default placeholder grid.
    """
    print(f"🛠 Raw AI Response Before Processing:\n{response_text}\n")  # Debugging statement

    # Remove triple backticks (```), which may be wrapping the AI response
    if response_text.startswith("```") and response_text.endswith("```"):
        response_text = response_text[3:-3].strip()

    # Split response into lines, stripping any excess whitespace
    lines = [line.strip() for line in response_text.strip().split("\n") if line.strip()]
    
    # Convert into a 3x3 grid
    grid = [line.split() for line in lines]

    # Ensure we have exactly 3 rows and each row has exactly 3 elements
    if len(grid) != 3 or any(len(row) != 3 for row in grid):
        print("❌ AI response is invalid. Returning placeholder grid.")
        return [["?"] * 3] * 3  # Default grid with placeholders
    
    return grid

def analyze_rubiks_faces(image_data_list):
    """
    Process images using AI and extract color grids for each face.
    """
    grids = {}
    face_labels = ["U", "R", "F", "D", "L", "B"]  # Mapping of faces in URFDLB order
    
    for i, image_data in enumerate(image_data_list, start=1):
        image_bytes = base64.b64decode(image_data.split(",")[1])
        face_img = PIL.Image.open(io.BytesIO(image_bytes))
        
        prompt = (
            "Analyze the image of a Rubik's Cube face. Identify the 9 squares of the visible face. "
            "For each square, determine its color from the following options: Blue, Orange, White, Yellow, Green, or Red. "
            "Return the result as a structured 3x3 grid, where each cell contains the first letter of the color name "
            "(e.g., B for Blue, O for Orange, W for White, Y for Yellow, G for Green, R for Red). "
            "Do not include any additional commentary."
        )
        
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[prompt, face_img]
        )
        
        print(response.text)

        grid = parse_grid(response.text)
        if not grid:
            print(f"❌ AI failed to generate a valid grid for Face {face_labels[i-1]}. Response was: {response.text}")
        
        grids[face_labels[i-1]] = {"grid": grid, "image": image_data}  # Store both grid & image
        
        print(f"AI Output for Face {face_labels[i-1]}:")
        for row in grid:
            print(" ".join(row))
        print("\n")
    
    return grids

@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.json
    image_data_list = data.get("images", [])
    print(f"📸 Received {len(image_data_list)} images for analysis.")

    if not image_data_list:
        print("❌ No images received!")
        return jsonify({"error": "No images provided"}), 400
    
    print(f"✅ Received {len(image_data_list)} images.")

    # Process the images to get per-face grids.
    face_assignment = analyze_rubiks_faces(image_data_list)
    
    if len(face_assignment) != 6:
        return jsonify({"error": "Incomplete cube data. Ensure all 6 faces are captured."}), 400
    
    # Return only the analysis; do not compute cube string etc. yet.
    return jsonify({"analysis": face_assignment})


import markdown  # Make sure to install this with: pip install markdown

@app.route("/generate", methods=["POST"])
def generate_solution():
    data = request.json
    grids = data.get("grids", {})
    # Validate that grids for all 6 faces are provided.
    if not grids or len(grids) != 6:
        return jsonify({"error": "Incomplete grid data. Ensure all 6 faces are provided."}), 400

    # Generate the color cube string using the (possibly corrected) grids.
    color_cube_string = generate_cube_string(grids)
    #print("Generated Color Cube String:", color_cube_string)
    
    # Convert to kociemba notation.
    kociemba_cube_string = convert_color_to_kociemba(color_cube_string)
    #print("Converted to Kociemba Notation:", kociemba_cube_string)
    
    # Solve the cube.
    cube_solution = solve_cube(kociemba_cube_string)
    #print("Cube Solution:", cube_solution)
    
    # Call Gemini AI to get step-by-step instructions in Markdown.
    prompt = (
        "Please provide step-by-step verbal instructions in markdown format for a user to solve the Rubik's Cube given the following Kociemba solution: " +
        cube_solution +
        ". Always start with the caveat: 'Note: Before executing the moves, ensure that the side with GREEN square in the center must face you while the face with WHITE square in the center faces the top.' Use markdown headers, bullet lists, and appropriate bold/italic formatting so the output is easy to read. Keep the steps brief and to the point"
    )
    gemini_response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[prompt]
    )
    instructions_markdown = gemini_response.text
    instructions_html = markdown.markdown(instructions_markdown)
    print("Gemini instructions (HTML):", instructions_html)
    
    return jsonify({
        "color_string": color_cube_string,
        "cube_string": kociemba_cube_string,
        "solution": cube_solution,
        "instructions": instructions_html
    })



if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))  # Use Heroku's port or default to 8080
    app.run(host="0.0.0.0", port=port, debug=False)
