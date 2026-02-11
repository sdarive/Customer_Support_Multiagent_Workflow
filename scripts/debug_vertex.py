import vertexai
from vertexai.generative_models import GenerativeModel
import sys

def list_models(project_id):
    vertexai.init(project=project_id, location="us-central1")
    # There isn't a direct "list_models" in GenerativeModel, 
    # but we can try to initialize one and see if it fails.
    try:
        model = GenerativeModel("gemini-1.5-flash-002")
        print("Initialized gemini-1.5-flash-002")
        response = model.generate_content("Hello")
        print(response.text)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_models(sys.argv[1])
