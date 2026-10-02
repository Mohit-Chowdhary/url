from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select

from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from fastapi import Request
import re

import secrets
import string

from backend.db import SessionLocal
from backend.models import URL

from datetime import datetime

app = FastAPI()

app.mount("/frontend",StaticFiles(directory="frontend"),name="frontend")

BASE62 = string.ascii_letters + string.digits

invalidCodes = ('test-db','submit')

class URLInput(BaseModel):
    url: str
    preference: str | None = None

@app.get("/test-db")
def test_db():
    db = SessionLocal()

    try:
        result = db.execute(text("SELECT 1"))
        return {"database": result.scalar()}
    finally:
        db.close()

@app.get("/")
def home():
    return FileResponse("frontend/home.html")

@app.post("/submit")
def submit(url_input: URLInput , request: Request):
    print("i got ",url_input.url)
    url = url_input.url
    preference = url_input.preference
    if preference == "":
        preference = None

    if preference is not None:
        len_pref = len(preference)

        if len_pref>10 or len_pref<3:
            return {"message": "Custom code must be between 3 and 10 characters"}

        if not preference.isalnum():
            return {"message": "Custom code must have only A-Z, a-z and 0-9"}

    if not url.startswith(("http://","https://")):
        url = "https://"+url

    

    if not isURLValid(url):
        return {"message":"Invalid URL"}

    db = SessionLocal()
    try:
        print("Valid url: ",url)

        if preference is not None:
            if preference in invalidCodes:
                return {"message": "Cannot use this code as it serves as an endpoint"}
            url_result = db.execute(select(URL).where(URL.original_url == url)).scalar_one_or_none()

            if url_result is not None:
                existing = url_result.short_code
                return {"message": f"This URL already has a shortcode", 
                        "code" :existing, 
                        "url":str(request.base_url)+existing}

            code_result = db.execute(select(URL).where(URL.short_code == preference)).scalar_one_or_none()

            if code_result is None:
                new_url = URL(short_code = preference, original_url = url)
                db.add(new_url)
                db.commit()
                return {"code": preference, 
                        "url":str(request.base_url)+preference}
            #elif collision[0] == url:
                #return {"code": preference, "url":url}
            else:
                return {"message": "Retry preference, or leave blank"}

        else:
            result = db.execute(select(URL).where(URL.original_url == url)).scalar_one_or_none()
            if result is not None:
                return {"code": result.short_code, "url":str(request.base_url)+result.short_code}
            while(True):
                code = generate_code(8)

                collision = db.execute(select(URL).where(URL.short_code == preference)).scalar_one_or_none().original_url

                if collision: continue

                new_url = URL(original_url = url, short_code = preference)
                db.insert(new_url)
                db.commit()

                return {"code": code, "url":str(request.base_url)+code}

    finally:
        db.close()

def generate_code(length=8):
    return "".join(secrets.choice(BASE62) for _ in range(length))

def isURLValid(url: str)->bool:
    pattern  = r"https?://[^\s]+$"
    return re.match(pattern, url) is not None


@app.get("/{code}/meta")
def metadata(code: str):
    db = SessionLocal()
    data = db.execute(select(URL).where(URL.short_code == code)).scalar_one_or_none()

    db.close()
    if data is None:
        return {"message":"No link exists for this shortcode"}
    return{"Original url": data.original_url,
           "Code": data.short_code, 
           "Created at": data.created_at, 
           "Last accessed": data.last_clicked_at, 
           "Click count": data.click_count}

@app.get("/{code}")
def redirect(code:str):
    db = SessionLocal()
    data = db.execute(select(URL).where(URL.short_code == code)).scalar_one_or_none()

    if data is None:
        return {"message": "No link exists for this shortcode"}
    
    url = data.original_url

    now = datetime.now()

    data.last_clicked_at = now
    data.click_count += 1
    db.commit()
    db.close()

    return RedirectResponse(url[0],status_code=302)