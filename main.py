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

# এপিআই কীসমূহ (আপনার দেওয়া কী ব্যবহার করা হয়েছে)
REMOVE_BG_API_KEY = "cR25Nqo8LUHgN51tFR4AaFtd"
CLIPDROP_API_KEY = "kfjcLZc3whZjYHgV27IvCAj2"

@app.get("/")
async def remove_background_api(image_url: str = None):
    # ইউআরএল চেক
    if not image_url:
        return {"error": "Please provide an image_url. Example: /?image_url=https://site.com/image.jpg"}

    async with httpx.AsyncClient() as client:
        # ১. ইমেজ ডাউনলোড
        try:
            image_res = await client.get(image_url, timeout=30.0)
            if image_res.status_code != 200:
                raise HTTPException(status_code=400, detail="Failed to fetch image from URL")
            img_content = image_res.content
        except Exception:
            raise HTTPException(status_code=500, detail="Error downloading the image")

        # ২. Remove.bg এপিআই দিয়ে প্রসেসিং
        try:
            rbg_res = await client.post(
                "https://api.remove.bg/v1.0/removebg",
                files={"image_file": ("image.png", img_content)},
                data={"size": "auto"},
                headers={"X-Api-Key": REMOVE_BG_API_KEY},
                timeout=60.0
            )

            if rbg_res.status_code == 200:
                return Response(content=rbg_res.content, media_type="image/png")

            # ৩. প্রথম এপিআই ফেইল করলে Clipdrop এপিআই ট্রাই করা
            cd_res = await client.post(
                "https://clipdrop-api.co/remove-background/v1",
                files={"image_file": ("image.png", img_content)},
                headers={"x-api-key": CLIPDROP_API_KEY},
                timeout=60.0
            )

            if cd_res.status_code == 200:
                return Response(content=cd_res.content, media_type="image/png")
            
            raise HTTPException(status_code=500, detail="Processing failed on both APIs")

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
