# 🎨 ComicFlow AI Studio 🖌️

ComicFlow AI Studio is a collaborative, AI-powered comic strip generator. Users contribute story snippets panel by panel, and AI assists by refining narration, generating dialogue, creating comic-style images, suggesting plot twists, and even adding sound effects!

The real magic happens when different contributors add their unique flair, potentially transforming a serious narrative into a comedic masterpiece or a simple scene into an epic saga – all through the joy of creating unexpected stories together!


This project was built as a micro-product, showcasing the integration of Google Gemini (for text and image generation), FastAPI (for the backend API), and Streamlit (for the interactive frontend).

**Live Demo:**

*   **Frontend:** https://comicflowaistudio-zmbjslumryjdbgoh5sjfcv.streamlit.app/
*   **Backend API Docs:** https://comicflow-ai-studio-backend.onrender.com/docs

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
git clone 
cd comicflow_project
```
