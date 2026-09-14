from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel
from urllib.request import urlopen
from urllib.error import HTTPError, URLError
from sqlalchemy import text

import secrets
import string

from backend.db import SessionLocal

app = FastAPI()

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
def submit(url_input: URLInput ):
    print("i got ",url_input.url)
    url = url_input.url
    preference = url_input.preference
    if preference == "":
        preference = None

    if not url.startswith(("http://","https://")):
        url = "https://"+url

    

    if(isURLValid(url)):
        print("Valid url: ",url)

        db = SessionLocal()

        if preference is not None:
            try:
                result = db.execute(text("""
                    SELECT original_url 
                    FROM urls 
                    WHERE short_code=:code;
                    """),
                    {"code":preference}
                )

                collision = result.fetchone()
                if collision is None:
                    result = db.execute(text("""INSERT INTO urls(original_url,short_code) 
                    VALUES(:url,:code); 
                    """),
                        {"url":url,"code":preference}
                    )
                    db.commit()
                    return {"code": preference, "url":url}
                elif collision[0] == url:
                    return {"code": preference, "url":url}
                else:
                    return {"result": None, "message": "Retry preference, or leave blank"}
            finally:
                db.close()

        else:
            try:
                result = db.execute(text("SELECT short_code FROM urls WHERE original_url = :url;"),
                    {"url":url}
                )
                exists = result.fetchone()
                if exists is not None:
                    return {"code": exists[0], "url":url}
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

                    return {"code": code, "url":url}
            finally:
                db.close()
    
    return {"result":"Invalid URL"}

def generate_code(length=8):
    return "".join(secrets.choice(BASE62) for _ in range(length))

def isURLValid(url: str)->bool:
    try:
        response = urlopen(url, timeout = 5)

        print("STATUS:", response.status)

        return response.status<400
    except HTTPError as e:
        print("HTTP error",e)
        return True
    except URLError as e:
        print("Error",e)
        return False
    except Exception as e:
        print("Except",e)
        return False