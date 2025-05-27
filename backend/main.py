import google.generativeai as genai_LLMs
from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO
import os
import json
import uuid
from typing import List, Dict, Optional

from fastapi import FastAPI, HTTPException, Body, Path as FastApiPath
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv # For .env file if used
from fastapi.middleware.cors import CORSMiddleware
# --- Load Environment Variables (Optional, if using .env) ---
load_dotenv()

# --- Directory Setups ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_OUTPUT_DIR = os.path.join(BASE_DIR, "generated_comics_panels")
STORY_JSON_DIR = os.path.join(BASE_DIR, "comic_stories_json")

os.makedirs(IMAGE_OUTPUT_DIR, exist_ok=True)
os.makedirs(STORY_JSON_DIR, exist_ok=True)

os.environ["GOOGLE_API_KEY"] = "AIzaSyD8XcO-lbEzlFB4ZbXxTEjWegpfuy-44JM"

# --- Prerequisites: API Key Configuration ---
try:
    GEMINI_API_KEY = os.environ.get("GOOGLE_API_KEY")
    if not GEMINI_API_KEY:
        raise KeyError("GOOGLE_API_KEY environment variable not set.")
    genai_LLMs.configure(api_key=GEMINI_API_KEY)
    print("✅ Gemini API Key Configured.")
except KeyError as e:
    print(f"🔴 FATAL: {e}")
    print("   Please set it before running the script. Example: export GOOGLE_API_KEY=\"YOUR_API_KEY\"")
    exit()
except Exception as e:
    print(f"🔴 FATAL: Error configuring Gemini: {e}")
    exit()

# --- LLM Configuration ---
TEXT_MODEL_NAME = "gemini-1.5-flash-latest"
try:
    text_model = genai_LLMs.GenerativeModel(TEXT_MODEL_NAME)
    print(f"✅ Text Model ({TEXT_MODEL_NAME}) Initialized.")
except Exception as e:
    print(f"🔴 FATAL: Error initializing text model ({TEXT_MODEL_NAME}): {e}")
    exit()

# --- Image Generation Model and Client Configuration ---
IMAGE_GEN_MODEL_NAME_FROM_SNIPPET = "gemini-2.0-flash-preview-image-generation"
try:
    image_client = genai.Client()
    print(f"✅ Gemini Client for Image Generation (for model {IMAGE_GEN_MODEL_NAME_FROM_SNIPPET}) Initialized.")
except Exception as e:
    print(f"🔴 FATAL: Error initializing Gemini Client for Image Gen: {e}")
    image_client = None
    # exit() # Or handle gracefully if image gen is optional

# --- JSON Story Persistence Functions ---
def get_story_filepath(story_id: str) -> str:
    return os.path.join(STORY_JSON_DIR, f"{story_id}.json")

def load_story_from_json(story_id: str) -> List[Dict[str, str]]:
    filepath = get_story_filepath(story_id)
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r') as f:
                panels = json.load(f)
                return panels if isinstance(panels, list) else []
        except (json.JSONDecodeError, Exception) as e:
            print(f"⚠️ Warning: Error loading story {filepath}: {e}. Starting fresh.")
            return []
    return []

def save_story_to_json(story_id: str, panels_data: List[Dict[str, str]]) -> None:
    filepath = get_story_filepath(story_id)
    try:
        with open(filepath, 'w') as f:
            json.dump(panels_data, f, indent=2)
        print(f"   💾 Story '{story_id}' saved to {filepath}")
    except Exception as e:
        print(f"🔴 Error saving story {filepath}: {e}")

def refine_story_and_create_visual_prompt(
    user_input: str,
    previous_panels_data: List[Dict[str, str]]
) -> Optional[Dict[str, str]]:
    """
    Uses Gemini Pro to refine user input into narration, dialogue,
    a visual prompt, AND a potential sound effect.
    """
    print(f"\n🔷 Refining story for input: '{user_input}' (incl. sound effect)")
    context_summary = ""
    if previous_panels_data:
        context_summary = "Previous scenes included:\n"
        for i, panel_data in enumerate(previous_panels_data):
            visual_desc = panel_data.get('ai_visual_prompt', 'N/A')
            narration_desc = panel_data.get('ai_narration', 'N/A')
            context_summary += f"- Panel {i+1} Visual: {visual_desc}\n"
            context_summary += f"- Panel {i+1} Narration: {narration_desc}\n"
        last_narration = previous_panels_data[-1].get('ai_narration', "This is the first panel.")
    else:
        last_narration = "This is the first panel of the comic."

    prompt = f"""
    You are a creative comic book writer and artist assistant.
    Your goal is to help build a collaborative comic strip panel by panel.

    Context of the story so far:
    {context_summary}
    The narration for the IMMEDIATELY PRECEDING panel was: "{last_narration}"

    A user has just added the following to the story: "{user_input}"

    Based on this new input and the preceding context, your tasks are:
    1.  **Narration:** Write a concise and engaging narrative caption for THIS NEW comic panel (1-2 sentences).
    2.  **Dialogue:** If the user's input implies dialogue, extract or create it.
        Format as "CHARACTER NAME (optional): Dialogue text." If no clear dialogue, state "None".
    3.  **Visual Prompt for Image Generation:** Create a DETAILED visual prompt for an AI image generator.
        Describe characters, setting, action, mood, art style ("vibrant, dynamic comic book art style"), composition.
        Ensure this logically follows previous visual descriptions.
    4.  **Sound Effect (Optional):** If the action or mood strongly suggests a classic comic book sound effect
        (e.g., an impact, a sudden movement, an explosion, a magical zap), provide ONE such sound effect
        in ALL CAPS (e.g., "KAPOW!", "VRRROOOM!", "ZAP!", "THUD!", "CREAK!").
        If no sound effect is appropriate, state "None".

    Provide your response strictly as a JSON object with the following keys:
    "ai_narration": "Your generated narration for the new panel.",
    "ai_dialogue": "Your generated dialogue for the new panel, or 'None'.",
    "ai_visual_prompt": "Your detailed visual prompt for the image generator.",
    "ai_sound_effect": "Your suggested sound effect in ALL CAPS, or 'None'."

    Example of a good JSON output:
    {{
      "ai_narration": "The hero leaps across the chasm, narrowly avoiding the laser beams!",
      "ai_dialogue": "HERO: Almost there!",
      "ai_visual_prompt": "Dynamic shot of a superhero in mid-air, leaping over a deep chasm with red laser beams crisscrossing below. Cityscape in the background. Vibrant comic book art style.",
      "ai_sound_effect": "WHOOSH!"
    }}

    Ensure the JSON is valid.
    """
    try:
        print(f"   Sending prompt to {TEXT_MODEL_NAME} (with sound effect request)...")
        response = text_model.generate_content(prompt)
        cleaned_response_text = response.text.strip().removeprefix("```json").removesuffix("```").strip()
        
        refined_elements = json.loads(cleaned_response_text)

        # VALIDATE ALL EXPECTED KEYS, INCLUDING THE NEW ONE
        expected_keys = ["ai_narration", "ai_dialogue", "ai_visual_prompt", "ai_sound_effect"]
        if not all(k in refined_elements for k in expected_keys):
            print(f"🔴 Error: LLM response missing required JSON keys. Expected: {expected_keys}, Got: {list(refined_elements.keys())}")
            print(f"   LLM Raw Text was: {response.text}")
            return None
        
        # Normalize "None" string for sound effect if necessary
        if isinstance(refined_elements.get("ai_sound_effect"), str) and refined_elements["ai_sound_effect"].strip().lower() == "none":
            refined_elements["ai_sound_effect"] = None # Store as Python None

        print("   ✅ LLM (Text Refinement + Sound Effect) processing successful.")
        print(f"   ↪ Narration: {refined_elements['ai_narration']}")
        print(f"   ↪ Dialogue: {refined_elements['ai_dialogue']}")
        print(f"   ↪ Visual Prompt: {refined_elements['ai_visual_prompt']}")
        print(f"   ↪ Sound Effect: {refined_elements.get('ai_sound_effect')}") # Use .get for safety
        return refined_elements

    except json.JSONDecodeError as e:
        print(f"🔴 Error: Failed to decode JSON from LLM response: {e}")
        print(f"   LLM Raw Text was: {response.text if 'response' in locals() else 'N/A'}")
        return None
    except Exception as e:
        block_reason = getattr(getattr(response, 'prompt_feedback', None), 'block_reason', None) if 'response' in locals() else None
        if block_reason:
            print(f"🔴 Error: Gemini Pro request was blocked. Reason: {block_reason}")
        else:
            print(f"🔴 An unexpected error occurred with Gemini Pro ({TEXT_MODEL_NAME}): {e}")
        return None

# --- Function for Image Generation (Using client method) ---
def generate_comic_image_with_client(
    visual_prompt: str,
    output_dir: str = IMAGE_OUTPUT_DIR
) -> Optional[str]:
    if not image_client:
        print("🔴 Image client not initialized.")
        return None
    print(f"\n🎨 Generating image for prompt: '{visual_prompt[:100]}...'")
    try:
        response = image_client.models.generate_content(
            model=IMAGE_GEN_MODEL_NAME_FROM_SNIPPET,
            contents=[visual_prompt],
            config=types.GenerateContentConfig(response_modalities=['TEXT','IMAGE'])
        )
        image_data = None
        if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if part.inline_data and part.inline_data.mime_type.startswith("image/"):
                    image_data = part.inline_data.data
                    break
        if image_data:
            image = Image.open(BytesIO(image_data))
            filename = f"panel_{uuid.uuid4().hex}.png"
            filepath = os.path.join(output_dir, filename)
            image.save(filepath)
            print(f"   ✅ Image saved to: {filepath}")
            return filename # Return only filename for URL construction
        else:
            print(f"🔴 Error: No image data in Gemini response for model {IMAGE_GEN_MODEL_NAME_FROM_SNIPPET}.")
            return None
    except Exception as e:
        print(f"🔴 Error during image generation: {e}")
        return None

# --- Core Panel Creation Logic ---
def create_new_comic_panel_logic(
    story_id: str,
    user_story_input: str
) -> Optional[Dict[str, str]]: # Return type still Dict, but it will contain the new field
    print(f"\n🆕 Processing panel for story '{story_id}', user input: '{user_story_input}'")
    current_story_panels = load_story_from_json(story_id)
    
    refined_elements = refine_story_and_create_visual_prompt(user_story_input, current_story_panels)
    if not refined_elements: return None

    image_filename = generate_comic_image_with_client(refined_elements["ai_visual_prompt"])
    if not image_filename: return None

    image_url = f"/static/panels/{image_filename}" 

    new_panel_data = {
        "panel_number": len(current_story_panels) + 1,
        "user_input": user_story_input,
        "ai_narration": refined_elements["ai_narration"],
        "ai_dialogue": refined_elements.get("ai_dialogue"), # Use .get for safety
        "ai_visual_prompt": refined_elements["ai_visual_prompt"],
        "ai_sound_effect": refined_elements.get("ai_sound_effect"), # ADDED: Store the sound effect
        "image_url": image_url,
    }
    current_story_panels.append(new_panel_data)
    save_story_to_json(story_id, current_story_panels)
    print(f"✅ New panel added to story '{story_id}' (with sound effect: {new_panel_data.get('ai_sound_effect')}) and saved!")
    return new_panel_data


# --- NEW: Function for AI Director's Suggestion ---
def get_ai_directors_suggestion(
    story_id: str,
    current_story_panels: List[Dict[str, str]]
) -> Optional[str]:
    """
    Uses Gemini Pro to generate a plot twist, new character, or setting change suggestion.
    """
    if not current_story_panels:
        return "The story hasn't started yet! Add a panel to get a suggestion."

    print(f"\n🎬 Generating Director's Cut suggestion for story '{story_id}'")

    # Summarize the story so far for context
    panel_summary_texts = []
    for i, panel in enumerate(current_story_panels):
        summary = f"Panel {i+1}: {panel.get('ai_narration', '')}"
        if panel.get('ai_dialogue') and panel.get('ai_dialogue', '').lower() != 'none':
            summary += f" Dialogue: {panel.get('ai_dialogue')}"
        panel_summary_texts.append(summary)
    
    story_context = "\n".join(panel_summary_texts)
    if not story_context.strip(): # Should not happen if current_story_panels is not empty
        story_context = "The story has panels but no narration or dialogue yet."

    prompt = f"""
    You are a creative "AI Director" for a collaborative comic book.
    The story so far is as follows:
    --- STORY CONTEXT ---
    {story_context}
    --- END STORY CONTEXT ---

    Based on this story, provide TWO OR THREE intriguing and concise suggestion for the *next* panel.
    This could be:
    - An unexpected plot twist.
    - The introduction of a new, interesting character.
    - A sudden change in setting or mood.
    - A mysterious object or event.

    Your suggestion should be a single sentence, designed to inspire the next human contributor.
    Make it sound like a "Director's Cut" idea. Be creative and a bit playful!

    Example Suggestions:
    - "What if suddenly, a hidden door creaks open revealing a secret passage?"
    - "Perhaps a shadowy figure has been watching them all along from the rooftops?"
    - "Just as they think they're safe, the ground starts to tremble violently!"
    - "Consider introducing a quirky sidekick with an unusual talent."

    Your suggestion:
    """

    try:
        print(f"   Sending prompt to {TEXT_MODEL_NAME} for Director's Cut...")
        # print(f"   Context sent: {story_context[:300]}...") # For debugging
        response = text_model.generate_content(prompt)

        suggestion = response.text.strip()
        
        if not suggestion:
            print("🔴 Error: LLM returned an empty suggestion.")
            return None

        # Basic cleanup (sometimes models add extra quotes or phrases like "Here's a suggestion:")
        suggestion = suggestion.removeprefix("Here's a suggestion:").removeprefix("Your suggestion:").strip()
        suggestion = suggestion.strip('"') # Remove leading/trailing quotes

        print(f"   ✅ Director's Suggestion: {suggestion}")
        return suggestion

    except Exception as e:
        block_reason = getattr(getattr(response, 'prompt_feedback', None), 'block_reason', None) if 'response' in locals() else None
        if block_reason:
            print(f"🔴 Error: Gemini Pro request for suggestion was blocked. Reason: {block_reason}")
        else:
            print(f"🔴 An unexpected error occurred while getting Director's suggestion: {e}")
        return None

# --- FastAPI App Definition ---
app = FastAPI(title="ComicFlow AI API")

# Add CORS middleware
origins = [
    "*" # Allows all origins - USE WITH CAUTION, for hackathon speed
    # Later, replace with your specific Streamlit frontend URL(s)
    # e.g., "https://your-streamlit-app-name.streamlit.app",
    # "http://localhost:8501" (for local Streamlit testing)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Allows all standard methods
    allow_headers=["*"], # Allows all headers
)

# Mount static files directory for images
# The path "/static/panels" will serve files from the IMAGE_OUTPUT_DIR directory
app.mount("/static/panels", StaticFiles(directory=IMAGE_OUTPUT_DIR, html=False), name="static_panels")

# --- Pydantic Models for Request/Response ---
class PanelInput(BaseModel):
    user_story_input: str

class PanelResponse(BaseModel):
    panel_number: int
    user_input: str
    ai_narration: str
    ai_dialogue: Optional[str] = None
    ai_sound_effect: Optional[str] = None
    # ai_visual_prompt: str # Probably not needed in frontend response
    image_url: str

class StoryResponse(BaseModel):
    story_id: str
    panels: List[PanelResponse]

class StoryListItem(BaseModel):
    story_id: str

class AISuggestionResponse(BaseModel): # NEW Pydantic model for the suggestion
    story_id: str
    suggestion: str


# --- API Endpoints ---
@app.post("/stories/{story_id}/panels", response_model=PanelResponse, status_code=201)
async def add_panel_to_story(
    story_id: str = FastApiPath(..., title="The ID of the story to add a panel to", min_length=1, max_length=50, regex="^[a-zA-Z0-9_-]+$"),
    panel_input: PanelInput = Body(...)
):
    """
    Adds a new panel to an existing story or creates a new story if story_id is new.
    The AI will generate narration, dialogue (if any), and a comic-style image for the panel.
    """
    # Consider running the AI logic in a threadpool for true async if it's very slow
    # from starlette.concurrency import run_in_threadpool
    # new_panel = await run_in_threadpool(create_new_comic_panel_logic, story_id, panel_input.user_story_input)
    
    new_panel = create_new_comic_panel_logic(story_id, panel_input.user_story_input)

    if not new_panel:
        raise HTTPException(status_code=500, detail="Failed to generate comic panel due to an internal AI or processing error.")
    
    # Adapt to PanelResponse model (remove ai_visual_prompt if not in PanelResponse)
    response_panel = PanelResponse(
        panel_number=new_panel["panel_number"],
        user_input=new_panel["user_input"],
        ai_narration=new_panel["ai_narration"],
        ai_dialogue=new_panel.get("ai_dialogue"),
        ai_sound_effect=new_panel.get("ai_sound_effect"),
        image_url=new_panel["image_url"]
    )
    return response_panel

@app.get("/stories/{story_id}", response_model=StoryResponse)
async def get_story_panels(
    story_id: str = FastApiPath(..., title="The ID of the story to retrieve", min_length=1, max_length=50, regex="^[a-zA-Z0-9_-]+$")
):
    """
    Retrieves all panels for a given story_id.
    """
    panels_data = load_story_from_json(story_id)
    if not panels_data:
        raise HTTPException(status_code=404, detail=f"Story with ID '{story_id}' not found.")
    
    # Adapt loaded panels to PanelResponse model
    response_panels = [
        PanelResponse(
            panel_number=p["panel_number"],
            user_input=p["user_input"],
            ai_narration=p["ai_narration"],
            ai_dialogue=p.get("ai_dialogue"),
            ai_sound_effect=p.get("ai_sound_effect"),
            image_url=p["image_url"] # Assuming image_url is already stored correctly
        ) for p in panels_data
    ]
    return StoryResponse(story_id=story_id, panels=response_panels)

@app.get("/stories", response_model=List[StoryListItem])
async def list_all_stories():
    """
    Lists all available story IDs.
    """
    story_ids = []
    try:
        for filename in os.listdir(STORY_JSON_DIR):
            if filename.endswith(".json"):
                story_ids.append(StoryListItem(story_id=filename[:-5])) # Remove .json extension
    except Exception as e:
        print(f"Error listing stories: {e}")
        raise HTTPException(status_code=500, detail="Could not retrieve story list.")
    return story_ids

@app.get("/stories/{story_id}/suggestion", response_model=AISuggestionResponse)
async def get_director_suggestion_for_story(
    story_id: str = FastApiPath(..., title="The ID of the story to get a suggestion for", min_length=1, max_length=50, regex="^[a-zA-Z0-9_-]+$")
):
    """
    Provides an AI-generated "Director's Cut" suggestion for the next panel
    of the specified story.
    """
    current_panels = load_story_from_json(story_id)
    if not current_panels:
        # You could also return a generic "start the story first" message if no panels exist.
        # For now, this is handled by the get_ai_directors_suggestion function.
        pass # Let the function handle it, or raise 404 if story MUST exist.
        # For this feature, it's okay if the story is new and has no panels yet.

    # Consider running in threadpool if this LLM call is slow
    # from starlette.concurrency import run_in_threadpool
    # suggestion = await run_in_threadpool(get_ai_directors_suggestion, story_id, current_panels)
    suggestion = get_ai_directors_suggestion(story_id, current_panels)

    if suggestion is None: # Indicates an error during suggestion generation
        raise HTTPException(status_code=500, detail="Could not generate an AI suggestion at this time.")
    
    return AISuggestionResponse(story_id=story_id, suggestion=suggestion)


# --- Root endpoint for basic check ---
@app.get("/")
async def root():
    return {"message": "Welcome to ComicFlow AI API! Visit /docs for API documentation."}

# --- To run the app (if this file is executed directly) ---
if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting FastAPI server...")
    print("   Access API docs at http://127.0.0.1:8000/docs")
    print("   Access ReDoc at http://127.0.0.1:8000/redoc")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)