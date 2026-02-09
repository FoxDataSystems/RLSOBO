"""
Pydantic models voor data validatie
"""
from pydantic import BaseModel
from typing import Optional
from datetime import date


class Gebruiker(BaseModel):
    GebruikerID: int
    Voornaam: str
    Achternaam: str
    Email: str
    Rol: str
    AfdelingID: Optional[int]
    AzureADObjectID: Optional[str]
    AfdelingNaam: Optional[str] = None
    Gebied: Optional[str] = None


class Cliënt(BaseModel):
    CliëntID: int
    Voornaam: str
    Achternaam: str
    Geboortedatum: Optional[date]
    AfdelingID: int
    BehandelaarID: Optional[int]
    AfdelingNaam: Optional[str] = None
    BehandelaarNaam: Optional[str] = None

