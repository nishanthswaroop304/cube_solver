import streamlit as st
import cv2
import time
import os
from dotenv import load_dotenv
from google import genai
import PIL.Image
from cube_string import generate_cube_string, convert_color_to_kociemba, solve_cube  # Import cube string module

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TIMER_DURATION = int(os.getenv("TIMER_DURATION", "3"))

client = genai.Client(api_key=GEMINI_API_KEY)

st.title("Rubik's Cube Face Auto Capture with Gemini API")

# ---------- Capture Phase ----------
def capture_six_faces():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        st.error("Could not open webcam.")
        return []
    
    frame_placeholder = st.empty()
    captured_faces = []
    
    # Dictionary mapping for face label and color code
    mapping = {
        1: ("U", "W"),
        2: ("R", "R"),
        3: ("F", "G"),
        4: ("D", "Y"),
        5: ("L", "O"),
        6: ("B", "B")
    }
    
    # For converting short codes to full color names.
    color_names = {"W": "white (W)", "Y": "yellow (Y)", "R": "red (R)", "G": "green (G)", "O": "orange (O)", "B": "blue (B)"}
    
    for i in range(1, 7):
        st.write(f"Capturing Face #{i}...")
        start_time = time.time()
        captured_frame = None
        
        while time.time() - start_time < TIMER_DURATION:
            ret, frame = cap.read()
            if not ret:
                st.error("Failed to capture frame.")
                break
            frame = cv2.flip(frame, 1)
            (h, w) = frame.shape[:2]
            
            remaining = int(TIMER_DURATION - (time.time() - start_time))
            face_label, face_color = mapping[i]
            
            # Determine instruction text based on face color:
            if face_color in ["W", "Y"]:
                instr_line1 = f"Point the cube face with {color_names[face_color]} center"
                instr_line2 = "with red (R) center facing to your right."
            else:
                instr_line1 = f"Point the cube face with {color_names[face_color]} center"
                instr_line2 = "with white (W) center facing up."
            
            # Set font parameters and colors (white text on black background)
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 1.6
            thickness = 2
            text_color = (255, 255, 255)  # white
            bg_color = (0, 0, 0)          # black
            padding = 10
            
            # --- Draw instruction text (wrapped into two lines) ---
            (line1_width, line1_height), _ = cv2.getTextSize(instr_line1, font, font_scale, thickness)
            (line2_width, line2_height), _ = cv2.getTextSize(instr_line2, font, font_scale, thickness)
            
            # Position the instructions near the top center.
            instr_y1 = padding + line1_height
            instr_y2 = instr_y1 + line2_height + padding
            instr_x1 = (w - line1_width) // 2
            instr_x2 = (w - line2_width) // 2
            
            # Background rectangle for first instruction line
            cv2.rectangle(frame,
                          (instr_x1 - 5, instr_y1 - line1_height - 5),
                          (instr_x1 + line1_width + 5, instr_y1 + 5),
                          bg_color, cv2.FILLED)
            cv2.putText(frame, instr_line1, (instr_x1, instr_y1),
                        font, font_scale, text_color, thickness, cv2.LINE_AA)
            
            # Background rectangle for second instruction line
            cv2.rectangle(frame,
                          (instr_x2 - 5, instr_y2 - line2_height - 5),
                          (instr_x2 + line2_width + 5, instr_y2 + 5),
                          bg_color, cv2.FILLED)
            cv2.putText(frame, instr_line2, (instr_x2, instr_y2),
                        font, font_scale, text_color, thickness, cv2.LINE_AA)
            
            # --- Draw timer text with white font and black background ---
            timer_text = f"Timer: {remaining}s"
            (timer_width, timer_height), _ = cv2.getTextSize(timer_text, font, font_scale, thickness)
            timer_x = w - timer_width - 10
            timer_y = timer_height + 10
            cv2.rectangle(frame,
                          (timer_x - 5, timer_y - timer_height - 5),
                          (timer_x + timer_width + 5, timer_y + 5),
                          bg_color, cv2.FILLED)
            cv2.putText(frame, timer_text, (timer_x, timer_y),
                        font, font_scale, text_color, thickness, cv2.LINE_AA)
            
            # --- Insert 9-grid dots code here ---
            grid_size = int(0.8 * min(w, h))
            offset_x = (w - grid_size) // 2
            offset_y = (h - grid_size) // 2
            dot_radius = 5
            dot_color = (0, 0, 255)
            dot_thickness = -1
            for row in range(3):
                for col in range(3):
                    center_x = offset_x + int((col + 0.5) * grid_size / 3)
                    center_y = offset_y + int((row + 0.5) * grid_size / 3)
                    cv2.circle(frame, (center_x, center_y), dot_radius, dot_color, dot_thickness)
            
            frame_placeholder.image(frame, channels="BGR")
            time.sleep(0.05)
            captured_frame = frame.copy()
        
        if captured_frame is not None:
            captured_faces.append(captured_frame)
        time.sleep(1)
    
    cap.release()
    return captured_faces


def parse_grid(text):
    lines = text.strip().splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].startswith("```"):
        lines = lines[:-1]
    rows = [row.strip() for row in lines if row.strip()]
    grid = [row.split() if " " in row else list(row) for row in rows]

    return grid if len(grid) == 3 and all(len(row) == 3 for row in grid) else [["?"]*3]*3

# ---------- Capture & Analysis Phase ----------
if st.button("Capture Cube Faces"):
    faces = capture_six_faces()
    if faces and len(faces) == 6:
        image_paths = []
        grids = []
        for i, face in enumerate(faces, start=1):
            path = f"face{i}.jpg"
            cv2.imwrite(path, face)
            image_paths.append(path)
        st.session_state["image_paths"] = image_paths

        for i, path in enumerate(image_paths, start=1):
            face_img = PIL.Image.open(path)
            prompt = (
                "Analyze the image of a Rubik's Cube face. Identify the 9 squares of the visible face. "
                "For each square, determine its color from the following options: Blue, Orange, White, Yellow, Green, or Red. "
                "Return the result as a structured 3x3 grid, where each cell contains the first letter of the color name "
                "(e.g., B for Blue, O for Orange, W for White, Y for Yellow, G for Green, R for Red). "
                "Do not include any additional commentary."
            )
            with st.spinner(f"Analyzing Face #{i} with Gemini API..."):
                response = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=[prompt, face_img]
                )
            grid = parse_grid(response.text)
            st.session_state[f"grid{i}"] = grid

            # Debug: Print AI response in terminal
            print(f"AI Output for Face #{i}:")
            for row in grid:
                print(" ".join(row))
            print("\n")

        st.session_state["captured"] = True

# ---------- Display Captured Faces & AI Output ----------
if st.session_state.get("captured", False):
    st.markdown("## Captured Faces and AI Output Grids")
    row1 = st.columns(3)
    row2 = st.columns(3)

    for i in range(3):
        row1[i].image(st.session_state["image_paths"][i], caption=f"Face #{i+1}", use_container_width=True)
    for i in range(3, 6):
        row2[i-3].image(st.session_state["image_paths"][i], caption=f"Face #{i+1}", use_container_width=True)

    st.markdown("### AI Output Grids")
    grid_row1 = st.columns(3)
    grid_row2 = st.columns(3)

    for i in range(3):
        grid = st.session_state.get(f"grid{i+1}", [["?"]*3]*3)
        grid_row1[i].subheader(f"Face #{i+1} AI Output")
        grid_row1[i].code("\n".join(" ".join(row) for row in grid), language="text")
    for i in range(3, 6):
        grid = st.session_state.get(f"grid{i+1}", [["?"]*3]*3)
        grid_row2[i-3].subheader(f"Face #{i+1} AI Output")
        grid_row2[i-3].code("\n".join(" ".join(row) for row in grid), language="text")

# ---------- Manual Correction (Hidden by default) ----------
with st.expander("Manual Correction", expanded=False):
    st.markdown("## Manual Correction")
    selected_face = st.selectbox("Select Face to Correct", [f"Face #{i}" for i in range(1, 7)])
    face_number = int(selected_face.split("#")[1])
    # Get the base grid for the selected face; default to a 3x3 grid of "?" if not available.
    base_grid = st.session_state.get(f"grid{face_number}", [["?"] * 3 for _ in range(3)])
    
    with st.form("manual_correction_form"):
        corrections = []
        for r in range(3):
            cols = st.columns(3)
            row_corr = []
            for c in range(3):
                key = f"corr_{selected_face}_{r}_{c}"
                cell_corr = cols[c].text_input("Cell", key=key, value=base_grid[r][c])
                row_corr.append(cell_corr)
            corrections.append(row_corr)
        submitted = st.form_submit_button("Apply Manual Correction")
    
    if submitted:
        st.session_state[f"grid{face_number}"] = corrections
        st.success(f"Manual update for {selected_face} successful!")
        
        # Debug: Print corrected grid in terminal
        print(f"Corrected {selected_face}:")
        for row in corrections:
            print(" ".join(row))
        print("\n")


# ---------- Cube Input String Generation ----------
st.markdown("## Generate Cube Input String for Solver")

if st.button("Generate Cube Input String"):
    # Retrieve the six grids from session state (each grid should be a 3x3 list of strings)
    grids = {i: st.session_state.get(f"grid{i}", [["?"] * 3 for _ in range(3)]) for i in range(1, 7)}

    # Map numeric keys to face labels:
    face_assignment = {
        "U": grids[1],
        "R": grids[2],
        "F": grids[3],
        "D": grids[4],
        "L": grids[5],
        "B": grids[6],
    }

    # Generate the color cube string.
    color_cube_string = generate_cube_string(face_assignment)
    
    if not color_cube_string:
        st.error("Error generating color cube string.")
    else:
        # Convert the color cube string to Kociemba notation.
        kociemba_cube_string = convert_color_to_kociemba(color_cube_string)
        if not kociemba_cube_string:
            st.error("Error converting color cube string to Kociemba notation.")
        else:
            # Solve the cube using the Kociemba solver.
            solution = solve_cube(kociemba_cube_string)
            
            st.markdown("### Color Cube String")
            st.code(color_cube_string, language="text")
            
            st.markdown("### Kociemba Cube String")
            st.code(kociemba_cube_string, language="text")
            
            st.markdown("### Kociemba Solver Output")
            st.code(solution, language="text")
            
            # Optionally store the color cube string in session state.
            st.session_state["cube_string"] = color_cube_string
            
            # Now send the Kociemba solution to Gemini AI for step-by-step solving instructions.
            client = genai.Client(api_key=GEMINI_API_KEY)
            prompt = (
                f"Given the Kociemba solution: {solution}, please provide step-by-step verbal "
                f"instructions for a user to solve the Rubik's Cube. Always start with the caveat: "
                f"'Note: The green cubelet in the middle must face you with white facing the top.'"
            )
            gemini_response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[prompt]
            )
            instructions = gemini_response.text
            
            st.markdown("### Gemini AI Step-by-Step Instructions")
            st.code(instructions, language="text")
