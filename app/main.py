"""
FastAPI applicatie voor Identity Propagation demonstratie
"""
from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import os
from pathlib import Path

from app.database import get_db_connection
from app.auth import get_current_user, get_user_from_token
from app.services import DataService

app = FastAPI(
    title="Identity Propagation Demo",
    description="Demonstratie van Identity Propagation met OAuth en RLS",
    version="1.0.0"
)

# Templates en static files
templates_dir = Path(__file__).parent.parent / "templates"
static_dir = Path(__file__).parent.parent / "static"
templates = Jinja2Templates(directory=str(templates_dir))

# Static files mount (als je CSS/JS nodig hebt)
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Hoofdpagina met demo overzicht"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/rls-demo", response_class=HTMLResponse)
async def rls_demo(request: Request):
    """RLS & Identity Propagation demo pagina"""
    conn = await get_db_connection()
    service = DataService(conn)
    organogram_data = await service.get_organogram_data()
    return templates.TemplateResponse("rls_demo.html", {
        "request": request,
        "organogram_data": organogram_data
    })


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Dashboard pagina voor ingelogde gebruikers"""
    try:
        # Haal gebruiker data op uit database
        conn = await get_db_connection()
        
        # Haal huidige gebruiker op
        temp_service = DataService(conn)
        gebruiker = await temp_service.get_gebruiker_by_azure_id(current_user.get("oid"))
        
        if not gebruiker:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Gebruiker niet gevonden in database"
            )
        
        # Maak service met gebruiker_id voor RLS
        service = DataService(conn, gebruiker["GebruikerID"])
        
        # Haal cliënten op die deze gebruiker mag zien (RLS)
        cliënten = await service.get_cliënten_for_gebruiker(gebruiker["GebruikerID"])
        
        # Haal collega's op in dezelfde afdeling
        collega_s = await service.get_collega_s(gebruiker["AfdelingID"], gebruiker["GebruikerID"])
        
        # Haal RLS informatie op
        rls_info = await service.get_rls_info(gebruiker["GebruikerID"])
        
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "gebruiker": gebruiker,
            "cliënten": cliënten,
            "collega_s": collega_s,
            "rls_info": rls_info
        })
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fout bij ophalen data: {str(e)}"
        )


@app.get("/api/gebruiker", response_model=dict)
async def get_gebruiker(current_user: dict = Depends(get_current_user)):
    """API endpoint om huidige gebruiker op te halen"""
    try:
        conn = await get_db_connection()
        service = DataService(conn)
        gebruiker = await service.get_gebruiker_by_azure_id(current_user.get("oid"))
        
        if not gebruiker:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Gebruiker niet gevonden"
            )
        
        return gebruiker
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.get("/api/cliënten", response_model=list)
async def get_cliënten(current_user: dict = Depends(get_current_user)):
    """API endpoint om cliënten op te halen (met RLS)"""
    try:
        conn = await get_db_connection()
        temp_service = DataService(conn)
        
        gebruiker = await temp_service.get_gebruiker_by_azure_id(current_user.get("oid"))
        if not gebruiker:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Gebruiker niet gevonden"
            )
        
        service = DataService(conn, gebruiker["GebruikerID"])
        cliënten = await service.get_cliënten_for_gebruiker(gebruiker["GebruikerID"])
        return cliënten
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.get("/api/collega-s", response_model=list)
async def get_collega_s(current_user: dict = Depends(get_current_user)):
    """API endpoint om collega's op te halen"""
    try:
        conn = await get_db_connection()
        temp_service = DataService(conn)
        
        gebruiker = await temp_service.get_gebruiker_by_azure_id(current_user.get("oid"))
        if not gebruiker:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Gebruiker niet gevonden"
            )
        
        service = DataService(conn, gebruiker["GebruikerID"])
        collega_s = await service.get_collega_s(gebruiker["AfdelingID"], gebruiker["GebruikerID"])
        return collega_s
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.get("/demo/{gebruiker_naam}")
async def demo_mode(gebruiker_naam: str, request: Request):
    """
    Demo modus: simuleer inloggen als specifieke gebruiker
    Voor testdoeleinden zonder Azure AD
    """
    conn = await get_db_connection()
    temp_service = DataService(conn)
    
    # Zoek gebruiker op naam
    gebruiker = await temp_service.get_gebruiker_by_naam(gebruiker_naam)
    
    if not gebruiker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Gebruiker '{gebruiker_naam}' niet gevonden"
        )
    
    # Maak service met gebruiker_id voor RLS
    service = DataService(conn, gebruiker["GebruikerID"])
    
    # Haal data op
    cliënten = await service.get_cliënten_for_gebruiker(gebruiker["GebruikerID"])
    collega_s = await service.get_collega_s(gebruiker["AfdelingID"], gebruiker["GebruikerID"])
    rls_info = await service.get_rls_info(gebruiker["GebruikerID"])
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "gebruiker": gebruiker,
        "cliënten": cliënten,
        "collega_s": collega_s,
        "rls_info": rls_info,
        "demo_mode": True
    })


@app.get("/obo-demo", response_class=HTMLResponse)
async def obo_demo(request: Request):
    """On-Behalf-Of flow demonstratie pagina"""
    return templates.TemplateResponse("obo_demo.html", {"request": request})


@app.get("/api/obo/cliënten")
async def obo_get_cliënten(gebruiker: str):
    """
    On-Behalf-Of endpoint: Backend service haalt data op namens een gebruiker
    In productie zou dit endpoint een OBO token ontvangen en valideren
    """
    try:
        conn = await get_db_connection()
        temp_service = DataService(conn)
        
        # Zoek gebruiker op naam (in productie: haal uit OBO token claims)
        gebruiker_data = await temp_service.get_gebruiker_by_naam(gebruiker)
        
        if not gebruiker_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Gebruiker '{gebruiker}' niet gevonden"
            )
        
        # Maak service met gebruiker_id voor RLS
        # Dit simuleert dat de backend service namens de gebruiker werkt
        service = DataService(conn, gebruiker_data["GebruikerID"])
        
        # Haal cliënten op (RLS wordt toegepast op basis van gebruiker_id)
        cliënten = await service.get_cliënten_for_gebruiker(gebruiker_data["GebruikerID"])
        
        return {
            "gebruiker": gebruiker_data["VolledigeNaam"],
            "gebruiker_id": gebruiker_data["GebruikerID"],
            "rol": gebruiker_data["Rol"],
            "cliënten": cliënten,
            "message": f"Data opgehaald namens {gebruiker_data['VolledigeNaam']} via On-Behalf-Of flow"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fout bij ophalen data: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

