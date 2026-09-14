from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel
from urllib.request import urlopen
from urllib.error import HTTPError, URLError
import os
from dotenv import load_dotenv

app = FastAPI()

DATABSE = os.getenv("DATABASE")

class URLInput(BaseModel):
    url: str

@app.get("/")
def home():
    return FileResponse("frontend/home.html")

@app.post("/submit")
def submit(urlInput: URLInput ):
    print("i got ",urlInput.url)
    url = urlInput.url
    if not url.startswith(("http://","https://")):
        url = "https://"+url

    if(isURLValid(url)):
        print("Valid url: ",url)
        
        return {"result": "Valid URL"}
    
    return {"result":"Invalid URL"}

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