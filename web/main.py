# /adk-playground/web/main.py

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import uvicorn

# --- THIS IS THE KEY CHANGE ---
# Import from the sibling package 'agent_backend'
from agents.video_producer_agent.agent import root_agent
# If you need other tools directly, import them similarly:
# from agent_backend.image_process import save_uploaded_image

app = FastAPI()

@app.post("/generate-commercial")
async def generate_commercial(prompt: str):
    try:
        # No changes needed here, the agent is already imported
        plan = await root_agent.plan(prompt)
        return JSONResponse(content={"plan": plan})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload-image-and-generate")
async def upload_and_generate(file: UploadFile = File(...), prompt: str = ""):
    """
    This endpoint handles image uploads and then triggers video generation.
    """
    # You can adapt your existing image processing logic here.
    # For example, save the uploaded file and then pass the path to your tools.
    file_location = f"temp_{file.filename}"
    with open(file_location, "wb+") as file_object:
        file_object.write(file.file.read())

    # Now you can use file_location with your existing functions.
    # ... your logic here ...

    return JSONResponse(content={"message": "Image uploaded successfully", "file_path": file_location})


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
