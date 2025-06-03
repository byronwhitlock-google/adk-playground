from . import agent

# Attempt to configure static file serving for the ADK's FastAPI app.
# This is speculative and depends on how google-adk exposes its app instance.
try:
    # Hypothetical: ADK might expose its FastAPI app instance via a module.
    # Common names could be 'app', 'main_app', 'current_app', etc.
    # Common modules could be 'google.adk.server', 'google.adk.web', 'google.adk.wsgi'.
    # This is a guess; the actual module and variable name might differ or not be exposed.
    from google.adk.server import app  # GUESSING the module and variable name
    # Or, if the app is created later and becomes a global, this import might work if __init__ is re-evaluated or app is set later
    # from some_adk_module import get_current_app
    # app = get_current_app()

    from fastapi.staticfiles import StaticFiles
    import os

    # Path to the frontend build directory
    # Assuming the script is run from the root of the repository where 'frontend' and 'agents' are.
    # The CWD for Gunicorn might be different, so this path needs to be robust.
    # If Gunicorn runs from /app/, then this path should be correct.
    # Using absolute path for the directory.
    # __file__ refers to the path of the current __init__.py
    # So, agents/video_producer_agent/__init__.py
    # Then, os.path.dirname(__file__) is agents/video_producer_agent/
    # Then, os.path.join(..., "..", "..", "frontend", "build") should go up two levels to /app/
    # and then to frontend/build.
    base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # Should be /app
    frontend_build_dir = os.path.join(base_path, "frontend", "build")


    # Ensure the directory exists before trying to mount it
    if os.path.exists(frontend_build_dir):
        print(f"Attempting to mount static files from: {frontend_build_dir}")
        # Mount at root. This could conflict with API routes if they are also at root.
        # It's generally safer if API routes are prefixed (e.g., /api/v1)
        # and the static files are mounted at "/" as a catch-all for non-API routes.
        # The `html=True` argument means it will serve `index.html` for directory requests.
        app.mount(
            "/",
            StaticFiles(directory=frontend_build_dir, html=True),
            name="static_frontend"
        )
        print(f"Successfully mounted static files from {frontend_build_dir} to /")
    else:
        print(f"WARNING: Frontend build directory not found at {frontend_build_dir}. Static files will not be served.")

except ImportError as e:
    print(f"WARNING: Could not import from 'google.adk.server' (Error: {e}). Static file serving for frontend not configured.")
    print("This might be because the ADK doesn't expose its app instance this way, or the module/variable name is different.")
except AttributeError as e:
    # This might happen if 'app' is imported but isn't a FastAPI instance / doesn't have 'mount'
    print(f"WARNING: Imported 'app' does not have 'mount' attribute (Error: {e}). Static file serving not configured.")
except Exception as e:
    print(f"An error occurred while trying to configure static file serving: {e}")
