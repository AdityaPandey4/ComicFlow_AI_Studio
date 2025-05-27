import streamlit as st
import requests # To make HTTP requests to the FastAPI backend
import os
from PIL import Image
from io import BytesIO
import json # Ensure json is imported

# --- Configuration ---
FASTAPI_BASE_URL = "http://127.0.0.1:8000"

# Helper function to make GET requests
def get_from_api(endpoint):
    try:
        response = requests.get(f"{FASTAPI_BASE_URL}{endpoint}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to API ({endpoint}): {e}")
        return None
    except json.JSONDecodeError:
        st.error(f"Error: Could not decode JSON response from API ({endpoint}). Response: {response.text if 'response' in locals() else 'N/A'}")
        return None

# Helper function to make POST requests
def post_to_api(endpoint, data):
    try:
        response = requests.post(f"{FASTAPI_BASE_URL}{endpoint}", json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to API ({endpoint}): {e}")
        st.error(f"Response content: {response.content if 'response' in locals() else 'N/A'}")
        return None
    except json.JSONDecodeError:
        st.error(f"Error: Could not decode JSON response from API ({endpoint}). Response: {response.text if 'response' in locals() else 'N/A'}")
        return None

# --- Streamlit App Layout ---
st.set_page_config(page_title="ComicFlow AI Studio", layout="wide")
st.title("🎨 ComicFlow AI Studio เจน สตอรี่")

# Initialize session states if not already present
if 'current_panels' not in st.session_state:
    st.session_state.current_panels = []
if 'last_loaded_story_id' not in st.session_state:
    st.session_state.last_loaded_story_id = None
if 'ai_suggestion' not in st.session_state:
    st.session_state.ai_suggestion = None
if 'suggestion_for_story' not in st.session_state:
    st.session_state.suggestion_for_story = None
if 'active_story_id' not in st.session_state: # Centralize the currently active story ID
    st.session_state.active_story_id = None
if 'story_action' not in st.session_state:
    st.session_state.story_action = "Select Existing Story" # Default action


# --- Story Selection and Creation ---
st.sidebar.header("📚 Stories")

story_list_data = get_from_api("/stories")
existing_stories = [story['story_id'] for story in story_list_data] if story_list_data else []

# Use session state for the radio button choice
st.session_state.story_action = st.sidebar.radio(
    "Choose action:",
    ("Select Existing Story", "Create New Story"),
    key="story_action_radio",
    index=0 if st.session_state.story_action == "Select Existing Story" or not existing_stories else 1
)

# Logic to derive the currently active story ID
current_active_story_id = None

if st.session_state.story_action == "Select Existing Story":
    if existing_stories:
        # The selectbox's value is the source of truth for selected_story_id here
        # Its state is managed by Streamlit via its key
        selected_from_list = st.sidebar.selectbox(
            "Select a Story:",
            options=existing_stories,
            key="story_selector_dropdown",
            index=existing_stories.index(st.session_state.active_story_id) if st.session_state.active_story_id in existing_stories else 0
        )
        if selected_from_list != st.session_state.active_story_id: # If selection changed
            st.session_state.active_story_id = selected_from_list
            st.session_state.ai_suggestion = None # Clear suggestion on story change
            st.session_state.suggestion_for_story = None
            st.rerun() # Rerun to load new story data
        current_active_story_id = st.session_state.active_story_id

    else:
        st.sidebar.info("No existing stories found. Create a new one!")
        st.session_state.story_action = "Create New Story" # Auto-switch if none exist
        # No st.rerun() needed here, will fall through to "Create New Story" block if forced

elif st.session_state.story_action == "Create New Story":
    new_story_id_input = st.sidebar.text_input(
        "Enter New Story ID (e.g., 'space_cats'):",
        key="new_story_id_input_field"
    )
    if st.sidebar.button("Start This New Story", key="confirm_new_story_button"):
        if not new_story_id_input.strip():
            st.sidebar.error("New Story ID cannot be empty.")
        elif not all(c.isalnum() or c in ['_', '-'] for c in new_story_id_input): # Basic validation
            st.sidebar.warning("Story ID can only contain letters, numbers, underscores, and hyphens.")
        elif new_story_id_input in existing_stories:
            st.sidebar.warning(f"Story ID '{new_story_id_input}' already exists. Choose a different ID or select it.")
        else:
            st.session_state.active_story_id = new_story_id_input
            st.session_state.current_panels = [] # New story starts with no panels
            st.session_state.last_loaded_story_id = new_story_id_input # Mark as "loaded" (empty)
            st.session_state.ai_suggestion = None # Clear any old suggestion
            st.session_state.suggestion_for_story = None
            st.sidebar.success(f"Switched to new story: {st.session_state.active_story_id}")
            st.rerun() # Rerun to reflect the new active story
    current_active_story_id = st.session_state.active_story_id # It might be None if not confirmed

# Use the centrally managed active_story_id for the rest of the app
selected_story_id_for_display = st.session_state.active_story_id

# --- Display Story Panels ---
if selected_story_id_for_display:
    st.header(f"Comic: {selected_story_id_for_display}")

    if selected_story_id_for_display != st.session_state.get('last_loaded_story_id'):
        with st.spinner(f"Loading panels for '{selected_story_id_for_display}'..."):
            story_data = get_from_api(f"/stories/{selected_story_id_for_display}")
            if story_data and 'panels' in story_data:
                st.session_state.current_panels = story_data['panels']
            elif story_data is None and selected_story_id_for_display in existing_stories:
                st.error(f"Could not load panels for '{selected_story_id_for_display}'. API might be down.")
                st.session_state.current_panels = []
            else: # New story confirmed or story not found by API
                st.session_state.current_panels = []
            st.session_state.last_loaded_story_id = selected_story_id_for_display

    if st.session_state.current_panels:
        st.subheader("Story So Far:")
        for panel in st.session_state.current_panels:
            col1, col2 = st.columns([1, 2])
            with col1:
                image_url = f"{FASTAPI_BASE_URL}{panel['image_url']}"
                try:
                    image_response = requests.get(image_url, stream=True)
                    image_response.raise_for_status()
                    panel_image = Image.open(BytesIO(image_response.content))
                    st.image(panel_image, caption=f"Panel {panel['panel_number']}", use_column_width=True)
                except Exception as e:
                    st.error(f"Error loading/displaying image for panel {panel['panel_number']}: {e}")
            with col2:
                st.markdown(f"**Panel {panel['panel_number']}**")
                st.markdown(f"**Narration:** {panel['ai_narration']}")
                if panel.get('ai_dialogue') and panel['ai_dialogue'].lower() != 'none':
                    st.markdown(f"**Dialogue:** {panel['ai_dialogue']}")
            st.markdown("---")
    elif selected_story_id_for_display and selected_story_id_for_display not in existing_stories:
        st.info("This is a new story. Add the first panel below!")
    elif selected_story_id_for_display:
        st.info(f"Story '{selected_story_id_for_display}' has no panels yet. Add one below!")

    # --- Add New Panel Section ---
    st.subheader("✏️ Add Your Contribution")

    # Key for these elements must be unique based on the selected_story_id_for_display
    # This ensures that if the story ID changes, Streamlit sees them as new elements.
    suggestion_button_key = f"suggest_{selected_story_id_for_display}"
    clear_suggestion_button_key = f"clear_suggestion_{selected_story_id_for_display}"
    input_area_key = f"input_{selected_story_id_for_display}"
    generate_button_key = f"generate_{selected_story_id_for_display}"


    if st.button("🎬 Get AI Director's Suggestion", key=suggestion_button_key):
        with st.spinner("AI Director is thinking... 🤔"):
            suggestion_data = get_from_api(f"/stories/{selected_story_id_for_display}/suggestion")
            if suggestion_data and "suggestion" in suggestion_data:
                st.session_state.ai_suggestion = suggestion_data["suggestion"]
                st.session_state.suggestion_for_story = selected_story_id_for_display
            else:
                st.session_state.ai_suggestion = "Could not get a suggestion. Try again later!"
                st.session_state.suggestion_for_story = selected_story_id_for_display
            st.rerun() # Rerun to display the suggestion immediately

    if st.session_state.ai_suggestion and st.session_state.suggestion_for_story == selected_story_id_for_display:
        st.info(f"💡 **AI Director Suggests:** {st.session_state.ai_suggestion}")
        if st.button("Clear Suggestion", key=clear_suggestion_button_key):
            st.session_state.ai_suggestion = None
            st.session_state.suggestion_for_story = None
            st.rerun()

    user_input_for_panel = st.text_area(
        "Describe the next scene or action (you can use the AI suggestion above for inspiration!):",
        height=100,
        key=input_area_key
    )

    if st.button("✨ Generate Next Panel", key=generate_button_key):
        if not user_input_for_panel.strip():
            st.warning("Please describe the scene before generating.")
        else:
            with st.spinner("AI is conjuring the next panel... Please wait."):
                payload = {"user_story_input": user_input_for_panel}
                new_panel_data = post_to_api(f"/stories/{selected_story_id_for_display}/panels", data=payload)

                if new_panel_data:
                    st.success("New panel generated!")
                    st.session_state.current_panels.append(new_panel_data)
                    if selected_story_id_for_display not in existing_stories:
                        existing_stories.append(selected_story_id_for_display) # Update local list for session
                    st.session_state.ai_suggestion = None # Clear suggestion
                    st.session_state.suggestion_for_story = None
                    # Clear the text area after successful submission by changing its key or value
                    # Easiest way here is to rely on the rerun and the key being tied to story_id.
                    # If we wanted to explicitly clear it, we'd need to manage its value in session_state.
                    st.rerun()
                else:
                    st.error("Failed to generate the new panel. Check API logs or try again.")
else:
    st.info("👈 Select an existing story or create a new one from the sidebar to begin!")

st.sidebar.markdown("---")
st.sidebar.markdown("Built with [Streamlit](https://streamlit.io) & [FastAPI](https://fastapi.tiangolo.com/) & Google Gemini")