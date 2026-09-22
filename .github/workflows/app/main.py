from fastapi import FastAPI

app = FastAPI(title="DriveLocal API", version="0.1.0")

@app.get("/")
def read_root():
    return {"message": "DriveLocal API est opérationnelle"}

@app.get("/health")
def health_check():
    return {"status": "ok"}