from fastapi import FastAPI, Response

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Prophecy Service läuft 🚀"}

@app.get("/health")
def health():
    return "ok"
@app.get("/favicon.ico")
def favicon():
    return Response(status_code=204)
