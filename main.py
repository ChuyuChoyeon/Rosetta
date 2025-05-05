import uvicorn
from Rosetta.asgi import application


if __name__ == "__main__":
    uvicorn.run(application, host="0.0.0.0", port=8888, log_level="info", workers=1) 
    