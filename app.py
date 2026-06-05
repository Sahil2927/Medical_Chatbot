from src.app_factory import create_app

app = create_app()

if __name__ == "__main__":
    import uvicorn

    port = int(__import__("os").getenv("PORT", "8080"))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=False)
