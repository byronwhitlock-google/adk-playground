# AI Video Commercial Producer

## Description
This project is a Python-based system that automates the creation of TV commercials from user ideas. It leverages cutting-edge AI models from Google, including Veo for video generation, Lyria for music composition, and Google Cloud Text-to-Speech for narration. The system, orchestrated by the `video_producer_agent`, takes a creative brief and transforms it into a complete video commercial, scene by scene.

## Features
*   Generates complete video commercials from high-level user prompts or creative briefs.
*   Utilizes Google's advanced AI models:
    *   **Veo:** For generating video content.
    *   **Lyria:** For composing background music scores.
    *   **Google Cloud Text-to-Speech:** For creating narration.
*   Orchestrates a detailed scene-by-scene video generation process.
*   Muxes narration with video for each scene.
*   Joins individual scene clips into a cohesive final video.
*   Integrates a custom-generated musical score with the final commercial.
*   Outputs a publicly accessible URL to the final generated video.

## Workflow
1.  **User Input:** The user provides a creative brief, idea, or a general concept for the commercial.
2.  **Scene Breakdown:** The `video_producer_agent` analyzes the input and breaks it down into a sequence of manageable scenes.
3.  **Per-Scene Generation:** For each scene, the agent performs the following:
    *   **Narration:** Generates audio narration using Google Cloud Text-to-Speech based on the scene's script.
    *   **Video Clip:** Generates a video clip using Veo, tailored to the scene's description and ensuring its length accommodates the narration.
    *   **Audio-Video Muxing:** Combines the generated narration and video clip into a single scene video.
4.  **Video Assembly:** All individual scene video clips are joined together to form the complete commercial video.
5.  **Music Integration:** A unique musical score is generated using Lyria based on the overall mood and theme of the commercial. This score is then muxed with the assembled video.
6.  **Output:** The system provides a public URL (e.g., a GCS public link) to the final video commercial.

## Setup Instructions

### 1. Clone the Repository
```bash
git clone <repository_url>
cd <repository_directory>
```

### 2. Python Version
Ensure you have Python 3.9 or newer installed.

### 3. Create a Virtual Environment
It's highly recommended to use a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
```

### 4. Install Dependencies
Install the required Python packages using the `requirements.txt` file:
```bash
pip install -r requirements.txt
```

### 5. Environment Variables
This project requires several environment variables to be set for accessing Google Cloud services and configuring project-specific settings. Create a `.env` file in the project root directory or set these variables in your environment:

*   **`GOOGLE_APPLICATION_CREDENTIALS`**: Path to your Google Cloud service account key JSON file. This is required for authentication with Google Cloud services.
    ```
    GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/service-account-key.json"
    ```
*   **`GOOGLE_CLOUD_PROJECT`**: Your Google Cloud Project ID.
    ```
    GOOGLE_CLOUD_PROJECT="your-gcp-project-id"
    ```
*   **`GOOGLE_CLOUD_LOCATION`**: The default Google Cloud region for services like Video Transcoder and where resources might be located (e.g., `us-central1`).
    ```
    GOOGLE_CLOUD_LOCATION="us-central1"
    ```
*   **`GOOGLE_CLOUD_BUCKET`**: The Google Cloud Storage bucket name used for storing intermediate files and final video outputs (e.g., `byron-alpha-vpagent`).
    ```
    GOOGLE_CLOUD_BUCKET="byron-alpha-vpagent"
    ```
*   **`LYRIA_MODEL_ID`** (Optional): Specific Lyria model to use, if different from a default (e.g., `lyria-002`).
    ```
    LYRIA_MODEL_ID="lyria-002"
    ```

**Note:** The agent's prompt in `video_producer_agent/agent.py` mentions "Bucket name is gs://byron-alpha-vpagent and location is us-central1". Ensure your environment variables align with these or are parameterized appropriately in a production setup.

## Usage

### Running the Agent
This project is designed to be run using the Google Agent Development Kit (ADK). The primary way to run the agent is using the `adk web` command, which starts a local web server to interact with the agent.

1.  **Ensure your environment variables are set** as described in the "Environment Variables" section (e.g., by ensuring your `.env` file is present and populated).
2.  **Run the ADK web server:**
    ```bash
    adk web
    ```
    This will start a web interface, typically on `http://localhost:8000`, where you can interact with the `video_producer_agent`.

3.  **Interact with the Agent:**
    Once the web server is running, open the provided URL in your browser. You can then send prompts to the agent through the web interface. For example, you could provide a creative brief as described below.

### Example Input Prompt
Through the ADK web interface, provide the `video_producer_agent` with a creative brief like:
```
"Create a 30-second commercial for a new brand of coffee called 'Morning Spark'.
Scene 1: Show a person waking up groggy.
Scene 2: They make a cup of 'Morning Spark' coffee, the aroma fills the kitchen.
Scene 3: They take the first sip and their eyes light up, full of energy.
Scene 4: The person is now productive and happy, tackling their day.
The commercial should have an upbeat and positive background music."
```

### Expected Output
The primary output will be a URL to the generated video commercial, hosted on Google Cloud Storage. For example:
```
Final video available at: https://storage.googleapis.com/byron-alpha-vpagent/commercials/generated_video_ بتاريخ_timestamp.mp4
```
The agent might also output URLs for intermediate scene videos during the generation process.

## Key Technologies & Libraries
*   **Python 3.9+**
*   **Google Cloud Platform:**
    *   Vertex AI (for hosting/accessing Veo & Lyria models)
    *   Google Cloud Text-to-Speech API
    *   Google Cloud Video Transcoder API (for muxing and joining video segments)
    *   Google Cloud Storage (for storing video assets and final outputs)
*   **Google Generative AI Models:**
    *   Veo (Video generation)
    *   Lyria (Music generation)
*   **Google ADK (Agent Development Kit)**: Used for building and running the AI agent (includes `google-cloud-adk` components).
*   **`python-dotenv`**: For managing environment variables.
*   **`requests`**: For making HTTP requests.
*   **`tinytag`**, **`mutagen`**: Libraries for reading audio/video metadata.
```
