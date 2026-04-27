import httpx
import base64
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS সেটিংস
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# এপিআই কীসমূহ
REMOVE_BG_API_KEY = "cR25Nqo8LUHgN51tFR4AaFtd"
CLIPDROP_API_KEY = "kfjcLZc3whZjYHgV27IvCAj2"
IMGBB_API_KEY = "37267f9c89495c3451733659a68a5146" # ImgBB Free Hosting API Key

@app.get("/")
async def remove_background_api(image_url: str = None):
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

        # ২. ব্যাকগ্রাউন্ড রিমুভ প্রসেসিং
        processed_img = None
        try:
            # প্রথম চেষ্টা: Remove.bg
            rbg_res = await client.post(
                "https://api.remove.bg/v1.0/removebg",
                files={"image_file": ("image.png", img_content)},
                data={"size": "auto"},
                headers={"X-Api-Key": REMOVE_BG_API_KEY},
                timeout=60.0
            )

            if rbg_res.status_code == 200:
                processed_img = rbg_res.content
            else:
                # দ্বিতীয় চেষ্টা: Clipdrop
                cd_res = await client.post(
                    "https://clipdrop-api.co/remove-background/v1",
                    files={"image_file": ("image.png", img_content)},
                    headers={"x-api-key": CLIPDROP_API_KEY},
                    timeout=60.0
                )
                if cd_res.status_code == 200:
                    processed_img = cd_res.content

            if not processed_img:
                raise HTTPException(status_code=500, detail="Processing failed on both APIs")

            # ৩. ইমেজটি ফ্রি হোস্টিংয়ে (ImgBB) আপলোড করা
            base64_image = base64.b64encode(processed_img).decode('utf-8')
            upload_res = await client.post(
                "https://api.imgbb.com/1/upload",
                data={
                    "key": IMGBB_API_KEY,
                    "image": base64_image,
                    "name": "SB_Sakib_Removed"
                },
                timeout=30.0
            )

            if upload_res.status_code == 200:
                upload_data = upload_res.json()
                # প্রিমিয়াম JSON রেসপন্স
                return {
                    "status": "success",
                    "author": "SB-SAKIB",
                    "original_url": image_url,
                    "processed_url": upload_data["data"]["url"],
                    "delete_url": upload_data["data"]["delete_url"],
                    "timestamp": upload_data["data"]["time"]
                }
            else:
                raise HTTPException(status_code=500, detail="Failed to upload image to hosting")

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
