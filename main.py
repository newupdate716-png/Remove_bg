import httpx
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

# আপনার দেওয়া এপিআই কীসমূহ
REMOVE_BG_API_KEY = "cR25Nqo8LUHgN51tFR4AaFtd"
CLIPDROP_API_KEY = "kfjcLZc3whZjYHgV27IvCAj2"

@app.get("/")
async def remove_background_api(image_url: str = None):
    if not image_url:
        return {
            "status": "error",
            "message": "Please provide an image_url. Example: /?image_url=https://site.com/photo.jpg"
        }

    async with httpx.AsyncClient(follow_redirects=True) as client:
        # ১. ইমেজ ডাউনলোড
        try:
            image_res = await client.get(image_url, timeout=30.0)
            if image_res.status_code != 200:
                raise HTTPException(status_code=400, detail="Failed to fetch image from URL")
            img_content = image_res.content
        except Exception:
            raise HTTPException(status_code=500, detail="Error downloading the image from source")

        # ২. ব্যাকগ্রাউন্ড রিমুভ প্রসেসিং
        processed_img = None
        
        # প্রথম চেষ্টা: Remove.bg
        try:
            rbg_res = await client.post(
                "https://api.remove.bg/v1.0/removebg",
                files={"image_file": ("image.png", img_content)},
                data={"size": "auto"},
                headers={"X-Api-Key": REMOVE_BG_API_KEY},
                timeout=60.0
            )
            if rbg_res.status_code == 200:
                processed_img = rbg_res.content
        except:
            pass

        # দ্বিতীয় চেষ্টা (যদি প্রথমটি ফেইল করে): Clipdrop
        if not processed_img:
            try:
                cd_res = await client.post(
                    "https://clipdrop-api.co/remove-background/v1",
                    files={"image_file": ("image.png", img_content)},
                    headers={"x-api-key": CLIPDROP_API_KEY},
                    timeout=60.0
                )
                if cd_res.status_code == 200:
                    processed_img = cd_res.content
            except:
                pass

        if not processed_img:
            raise HTTPException(status_code=500, detail="Both background removal APIs failed or keys expired")

        # ৩. প্রসেস করা ইমেজটি Telegraph-এ আপলোড (ফাস্ট এবং ফ্রি হোস্টিং)
        try:
            upload_res = await client.post(
                "https://telegra.ph/upload",
                files={"file": ("image.png", processed_img, "image/png")},
                timeout=30.0
            )
            
            if upload_res.status_code == 200:
                upload_data = upload_res.json()
                if isinstance(upload_data, list) and "src" in upload_data[0]:
                    final_link = "https://telegra.ph" + upload_data[0]["src"]
                    
                    # প্রিমিয়াম JSON রেসপন্স
                    return {
                        "status": "success",
                        "developer": "SB-SAKIB",
                        "original_image": image_url,
                        "processed_image_url": final_link,
                        "instruction": "This link is permanent and transparent PNG.",
                        "credit_left": "Check your API dashboard"
                    }
            
            raise Exception("Upload to cloud failed")
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Hosting Error: {str(e)}")

