from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(
    title="Product Management API",
    description="API for managing products",
    version="1.0.0"
)

@app.get("/")
async def root():
    return {"message": "Product Management API is running"}

@app.get("/health")
async def health_check():
    return JSONResponse(
        status_code=200,
        content={"status": "healthy", "service": "product-management-api"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
