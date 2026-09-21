from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import text

from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from fastapi import Request
import re

import secrets
import string

from backend.db import SessionLocal

from datetime import datetime

app = FastAPI()

app.mount("/frontend",StaticFiles(directory="frontend"),name="frontend")

BASE62 = string.ascii_letters + string.digits

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
            return {"message": "Custom code must have only A-Z,a-z and 0-9"}

    if not url.startswith(("http://","https://")):
        url = "https://"+url

    

    if(isURLValid(url)):
        print("Valid url: ",url)

        db = SessionLocal()

        if preference is not None:
            try:
                url_result = db.execute(text("""
                    SELECT original_url 
                    FROM urls 
                    WHERE original_url=:url;
                    """),
                    {"url":url}
                )

                existing = url_result.fetchone()

                if existing is not None:
                    code_result = db.execute(text("""
                        SELECT short_code
                        FROM urls
                        WHERE original_url=:url;
                    """),
                        {"url":url}
                    )

                    existing_code = code_result.fetchone()

                    return {"message": f"This URL already has a shortcode ", "code" :existing_code[0], "url":str(request.base_url)+code}

                
                code_result = db.execute(text("""
                    SELECT original_url 
                    FROM urls 
                    WHERE short_code=:code;
                    """),
                    {"code":preference}
                )

                collision = code_result.fetchone()

                if collision is None:
                    result = db.execute(text("""INSERT INTO urls(original_url,short_code) 
                    VALUES(:url,:code); 
                    """),
                        {"url":str(request.base_url)+url,"code":preference}
                    )
                    db.commit()
                    return {"code": preference, "url":url}
                #elif collision[0] == url:
                    #return {"code": preference, "url":url}
                else:
                    return {"message": "Retry preference, or leave blank"}
            finally:
                db.close()

        else:
            try:
                result = db.execute(text("SELECT short_code FROM urls WHERE original_url = :url;"),
                    {"url":url}
                )
                exists = result.fetchone()
                if exists is not None:
                    return {"code": exists[0], "url":str(request.base_url)+exists[0]}
                while(True):
                    code = generate_code(8)

                    collision =db.execute(text("SELECT original_url FROM urls WHERE short_code = :code;"),
                        {"code": code}
                    ).fetchone()

                    if collision: continue

                    result = db.execute(text("""INSERT INTO urls(original_url,short_code)
                    VALUES(:url,:code)"""),
                    {"url": url, "code": code}
                    )
                    db.commit()

                    return {"code": code, "url":str(request.base_url)+code}
            finally:
                db.close()
    
    return {"message":"Invalid URL"}

def generate_code(length=8):
    return "".join(secrets.choice(BASE62) for _ in range(length))

def isURLValid(url: str)->bool:
    pattern  = r"https?://[^\s]+$"
    return re.match(pattern, url) is not None


@app.get("/{code}/meta")
def metadata(code: str):
    db = SessionLocal()
    result = db.execute(text("""
        SELECT * FROM urls
        WHERE short_code = :code;
    """),{"code":code})

    data = result.fetchone()

    if data is None:
        return {"message":"No link exists for this shortcode"}
    db.close()
    return{"Original url": data[2],
           "Code": data[1], 
           "Created at": data[3], 
           "Last accessed": data[4], 
           "Click count": data[5]}

@app.get("/{code}")
def redirect(code:str):
    db = SessionLocal()
    data = db.execute(text("""SELECT original_url FROM urls
        WHERE short_code = :code;
    """),{"code":code}
    )

    url = data.fetchone()

    if url is None:
        return {"message": "No link exists for this shortcode"}

    now = datetime.now()

    result = db.execute(text("""
        UPDATE urls
        SET last_clicked_at = :now, click_count = click_count+1
        WHERE short_code = :code;
    """),{"code":code,"now":now})
    db.commit()
    db.close()

    return RedirectResponse(url[0],status_code=302)