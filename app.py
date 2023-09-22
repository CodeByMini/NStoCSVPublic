from fastapi import FastAPI, WebSocket, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

import os
import uvicorn
from pathlib import Path
from io import StringIO

from nsdata import nsdata

origins = ["*"]

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory="static"), name="static")

BASE_PATH = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_PATH / "templates"))


@app.get("/", response_class=HTMLResponse)
async def Index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "title": "Diabetes 101",
        },
    )


@app.get("/getcsv", response_class=HTMLResponse)
async def GetCSV(request: Request):
    adress = request.query_params.get("adress")
    apisecret = request.query_params.get("apisecret")
    token = request.query_params.get("token")
    start_date = request.query_params.get("date")
    days = request.query_params.get("days")
    print(adress)

    json = nsdata(adress, start_date, days, apisecret, token)
    adress_split = adress[8:-14]
    print(adress_split)
    serial_numbers = [ord(letter) for letter in adress_split]
    serial_str = ""
    for letter in serial_numbers:
        serial_str += str(letter)
    print(serial_str)
    writer = StringIO()
    firstrow = "Glukosuppgifter,Skapat den,,Skapat av,\n"
    secondrow = "Enhet,Serienummer,Enhetens tidsstämpel,Registertyp,Historiskt glukosvärde mmol/L,Skanna glukosvärde mmol/L,Icke-numeriskt snabbverkande insulin,Snabbverkande insulin (enheter),Icke-numerisk mat,Kolhydrater (gram),Kolhydrater (portioner),Icke-numeriskt långtidsverkande insulin,Långtidsverkande insulin (enheter),Anteckningar,Glukossticka mmol/L,Keton mmol/L,Måltidsinsulin (enheter),Korrigeringsinsulin (enheter),Användarändrat insulin (enheter)\n"

    writer.writelines(firstrow)
    writer.writelines(secondrow)
    for line in json:
        if "sgv" in line.keys():
            row = (
                "Nightscout,"
                + serial_str
                + ","
                + line["date"].strftime("%m-%d-%Y %H:%M")
                + ',0,"'
                + str(line["sgv"])
                + '",,,'
                + ",,,,,,,,,,,\n"
            )
        if "insulin" in line.keys():
            row = (
                "Nightscout,"
                + serial_str
                + ","
                + line["date"].strftime("%m-%d-%Y %H:%M")
                + ",4,"
                + ",,,"
                + str(line["insulin"])
                + ",,,,,,,,,,,\n"
            )
        if "carbs" in line.keys():
            row = (
                "Nightscout,"
                + serial_str
                + ","
                + line["date"].strftime("%m-%d-%Y %H:%M")
                + ",5,"
                + ",,,,,"
                + str(line["carbs"])
                + ",,,,,,,,,\n"
            )
        if "basal" in line.keys():
            row = (
                "Nightscout,"
                + serial_str
                + ","
                + line["date"].strftime("%m-%d-%Y %H:%M")
                + ",4,"
                + ",,,,,,,,"
                + str(line["basal"])
                + ",,,,,\n"
            )
        writer.writelines(row)

    # f.close()
    writer.seek(0)
    export_media_type = "text/csv"
    export_headers = {
        "Content-Disposition": "attachment; filename={file_name}.csv".format(
            file_name=adress
        )
    }
    return StreamingResponse(
        writer, headers=export_headers, media_type=export_media_type
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info",
    )
