import httpx
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS সেটিংস
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# আপনার Remove.bg API Key
API_KEY = "5X4svLdMjC3VsuxYE6n3Sme9"

@app.get("/")
async def remove_bg_api(image_url: str = None):
    if not image_url:
        return {"error": "Please provide an image_url parameter. Example: /?image_url=LINK"}

    async with httpx.AsyncClient() as client:
        try:
            # ইমেজ ডাউনলোড
            img_res = await client.get(image_url, timeout=20.0)
            if img_res.status_code != 200:
                raise HTTPException(status_code=400, detail="Could not fetch image from URL")

            # Remove.bg এপিআই কল
            response = await client.post(
                "https://api.remove.bg/v1.0/removebg",
                files={"image_file": ("image.png", img_res.content)},
                data={"size": "auto"},
                headers={"X-Api-Key": API_KEY},
                timeout=60.0
            )

            if response.status_code == 200:
                # সরাসরি ইমেজ রিটার্ন করা যাতে লিঙ্কটি ইমেজের মতো কাজ করে
                return Response(content=response.content, media_type="image/png")
            else:
                return {"error": "Background removal failed", "details": response.text}

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))