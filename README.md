# 🎨 ComicFlow AI Studio 🖌️

ComicFlow AI Studio is a collaborative, AI-powered comic strip generator. Users contribute story snippets panel by panel, and AI assists by refining narration, generating dialogue, creating comic-style images, suggesting plot twists, and even adding sound effects!

The real magic happens when different contributors add their unique flair, potentially transforming a serious narrative into a comedic masterpiece or a simple scene into an epic saga – all through the joy of creating unexpected stories together!


This project was built as a micro-product, showcasing the integration of Google Gemini (for text and image generation), FastAPI (for the backend API), and Streamlit (for the interactive frontend).

**Live Demo:**

*   **Frontend:** https://comicflowaistudio-zmbjslumryjdbgoh5sjfcv.streamlit.app/
*   **Backend API Docs:** https://comicflow-ai-studio-backend.onrender.com/docs

![Capture](https://github.com/user-attachments/assets/30a54481-6dc7-491f-bc9e-905a1d4a14a4)


*(Note: I am using free tiers for deployment, services may occasionally sleep or have cold starts, so the first load might be slower.)*

## ✨ Features

*   **Truly Collaborative Storytelling:** Build comic stories panel by panel with other users. Watch as the narrative evolves in surprising directions based on collective input – the core fun of the app!
*   **Embrace the Unexpected:** The beauty of ComicFlow is how a story can morph. A contributor might introduce a sudden funny twist to a serious plot, or take a mundane scene to an absurdly epic level.
*   **AI-Powered Panel Generation:**
    *   **Narration & Dialogue:** AI refines user input into comic-style narration and character dialogue, adapting to the evolving tone.
    *   **Image Generation:** AI creates unique comic panel images reflecting the current (and perhaps newly twisted!) scene.
    *   **Sound Effects:** AI suggests classic comic book sound effects to punctuate the action.
*   **Director's Cut AI:** Get AI-generated suggestions for plot twists, new characters, or setting changes to further fuel the creative chaos or inspire the next contributor.
*   **Persistent Stories:** Comic stories and their wonderfully winding panels are saved and can be revisited to marvel at their unique journeys.
*   **Interactive Frontend:** Easy-to-use Streamlit interface for viewing and joyfully contributing to the ever-changing comics.
*   **API Backend:** FastAPI provides robust endpoints for managing stories and generating panels.

## 🛠️ Tech Stack

*   **Backend:**
    *   Python 3.10+
    *   FastAPI (for the REST API)
    *   Uvicorn (ASGI server)
    *   Google Gemini API (via `google-generativeai` SDK for LLM text processing and image generation)
    *   Pillow (for image handling, if any beyond direct API)
    *   Docker (for containerization and deployment)
*   **Frontend:**
    *   Python 3.10+
    *   Streamlit (for the web application interface)
    *   Requests (to communicate with the FastAPI backend)
*   **Deployment:**
    *   Backend: Render 
    *   Frontend: Streamlit Community Cloud

## 🚀 Getting Started Locally

### Prerequisites

*   Python 3.10 or higher
*   Git
*   Docker (recommended for backend, optional for understanding deployment)
*   A Google API Key with Gemini API enabled. Get yours from [Google AI Studio](https://aistudio.google.com/app/apikey).

### 1. Clone the Repository

```bash
git clone https://github.com/AdityaPandey4/ComicFlow_AI_Studio.git
cd comicflow_project
```
### 2. Backend Setup & Run
Follow these steps within the backend/ directory:
```bash
cd backend
```
Create a Virtual Environment (Recommended):

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

Install Dependencies:

```bash
pip install -r requirements.txt
```

Set Environment Variables:
Create a .env file in the backend/ directory (this file is gitignored):

```bash
GOOGLE_API_KEY="YOUR_GOOGLE_API_KEY_HERE"
```

Replace "YOUR_GOOGLE_API_KEY_HERE" with your actual API key.
Run the FastAPI Backend:
```bash
uvicorn main:app --reload
```

The backend API will typically be available at http://127.0.0.1:8000. You can access the API docs at http://127.0.0.1:8000/docs.

### 3. Frontend Setup & Run
Open a new terminal and follow these steps within the frontend/ directory:

```bash
cd frontend # (from the project root, or navigate from backend/ to ../frontend/)
```
Create a Virtual Environment (Recommended, can be separate from backend's):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

Install Dependencies:
```bash
pip install -r requirements.txt
```

Run the Streamlit Frontend:
(Ensure your backend is already running as per the previous step)
```bash
streamlit run app.py
```
The Streamlit app will typically open in your browser at http://localhost:8501. It will connect to the local backend running on port 8000 by default.
## ☁️ Deployment Notes
This application is designed for separate deployment of the backend and frontend.
*   Backend (FastAPI)
   *   The backend is containerized using the backend/Dockerfile.
   *   It expects the GOOGLE_API_KEY environment variable to be set on the deployment platform.
   *   It creates comic_stories_json/ and generated_comics_panels/ directories for data storage. For persistent storage on platforms like Render, configure persistent disks/volumes mounted to these paths (e.g., /app/comic_stories_json and /app/generated_comics_panels if WORKDIR in Docker is /app). As the persistant storage requires paid tier of the Render deployement platform, I don't have persistant storage at this stage 
   *   Remember to configure CORS in backend/main.py to allow requests from your deployed frontend's domain.
*   Frontend (Streamlit)
   *   The frontend can be easily deployed to Streamlit Community Cloud.
   *   It requires a secret (environment variable) named FASTAPI_BASE_URL to be set in Streamlit Cloud, pointing to the live URL of your deployed FastAPI backend (e.g., https://your-backend-name.onrender.com).
   *   The main application file is frontend/app.py.

## 💡 How to Use: The Joy of Unexpected Twists!
1. Access the Frontend: Open the live Streamlit app URL (or your local version).
2. Manage Stories:
*   Select Existing Story: Jump into an ongoing narrative and see where it's headed (or where you can steer it!).
*   Create New Story: Kick off a fresh adventure.
3. View Panels: Catch up on the current state of the selected story – characters, plot, and previous hilarious or dramatic turns.
4. Add Your Twist (or Contribution!):
*   Enter your idea for the next scene or action. This is your chance to continue the current thread, or throw in that comedic curveball, that sudden alien invasion, or that unexpected talking squirrel that changes everything!
*   (Optional) Click "🎬 Get AI Director's Suggestion" if you need a spark or want to see what the AI thinks could happen next.
*   Click "✨ Generate Next Panel".
5. Witness the Evolution: The AI processes your input, and the story continues, shaped by your (and others') creativity.
6. Embrace the Chaos: The true essence is in co-creating stories that go in directions no single person could have planned. A serious drama might become a side-splitting comedy, a simple quest might involve interdimensional travel – all thanks to the collaborative spirit!
## 🤝 Contributing (Example - Keep simple for now)
*   This was a rapid prototype. Potential areas for future development:
*   User accounts and authentication (to see who added which twist!).
*   More advanced image style controls.
*   Voting or rating for stories/panels, especially the "most unexpected twist."
*   Exporting comics (e.g., as a single image or PDF).
*   Improved error handling and UI refinement.
  
Created with 🧠 and ✨ by Aditya Pandey (AdityaPandey4)

