# Identity Propagation Demo - Uitgebreide Documentatie

Webapplicatie voor het demonstreren van Identity Propagation met OAuth tokens, On-Behalf-Of flows en applicatie-level Row Level Security (RLS).

## Inhoudsopgave

1. [Overzicht](#overzicht)
2. [Architectuur](#architectuur)
3. [Hoe het werkt - Stap voor Stap](#hoe-het-werkt)
4. [Componenten Uitleg](#componenten-uitleg)
5. [RLS (Row Level Security) Mechanisme](#rls-mechanisme)
6. [Identity Propagation Flow](#identity-propagation-flow)
7. [Installatie & Setup](#installatie--setup)
8. [API Endpoints](#api-endpoints)
9. [Database Structuur](#database-structuur)
10. [Troubleshooting](#troubleshooting)

---

## Overzicht

Deze applicatie demonstreert hoe **Identity Propagation** werkt in een moderne webapplicatie:

- **Identity Propagation**: De identiteit van een gebruiker wordt doorgegeven door verschillende lagen van de applicatie
- **OAuth Tokens**: Authenticatie via Azure AD OAuth 2.0 tokens
- **On-Behalf-Of (OBO) Flow**: Een service kan namens een gebruiker data ophalen
- **Row Level Security (RLS)**: Gebruikers zien alleen data waar ze toegang toe hebben

### Belangrijkste Features

- Applicatie-level RLS filtering (SQLite compatible)
- Demo modus zonder Azure AD setup
- Interactief organogram met visuele hiërarchie
- Kleurcodering per afdeling en behandelaar
- Uitgebreide RLS uitleg per gebruiker
- On-Behalf-Of flow demonstratie

---

## Architectuur

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Templates)                      │
│  - index.html: Hoofdpagina met demo overzicht               │
│  - rls_demo.html: RLS demo met organogram                    │
│  - dashboard.html: Gebruiker dashboard met data             │
│  - obo_demo.html: On-Behalf-Of flow demonstratie            │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              FastAPI Application (app/main.py)               │
│  - Routes: /, /rls-demo, /dashboard, /demo/{naam}          │
│  - API Endpoints: /api/gebruiker, /api/cliënten, etc.      │
│  - Authentication: Bearer token validatie                    │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│          Services Layer (app/services.py)                     │
│  - DataService: Business logic met RLS filtering            │
│  - get_cliënten_for_gebruiker(): RLS filtering logica        │
│  - get_rls_info(): Statistieken en uitleg                    │
│  - get_organogram_data(): Organisatiestructuur               │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│        Database Layer (app/database.py)                       │
│  - DatabaseConnection: SQLite connection manager            │
│  - set_current_user_id(): Context voor RLS                   │
│  - get_current_user_id(): Huidige gebruiker context         │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              SQLite Database (data/*.db)                     │
│  - Gebruikers: Rollen en afdelingen                         │
│  - Cliënten: Data met BehandelaarID en AfdelingID           │
│  - Toegangsrechten: Expliciete rechten tabel                 │
└─────────────────────────────────────────────────────────────┘
```

---

## Hoe het werkt - Stap voor Stap

### Scenario: Gebruiker bekijkt zijn dashboard

#### Stap 1: Gebruiker klikt op demo link
```
Gebruiker klikt op: /demo/Ralph
```

#### Stap 2: FastAPI Route ontvangt request
**Bestand**: `app/main.py` - Route `/demo/{gebruiker_naam}`

```python
@app.get("/demo/{gebruiker_naam}")
async def demo_mode(gebruiker_naam: str, request: Request):
    # 1. Haal database connectie op
    conn = await get_db_connection()
    
    # 2. Zoek gebruiker op naam
    temp_service = DataService(conn)
    gebruiker = await temp_service.get_gebruiker_by_naam(gebruiker_naam)
    
    # 3. Maak service met gebruiker_id voor RLS
    service = DataService(conn, gebruiker["GebruikerID"])
    
    # 4. Haal data op (RLS wordt automatisch toegepast)
    cliënten = await service.get_cliënten_for_gebruiker(...)
```

**Wat gebeurt er?**
- FastAPI ontvangt de request
- `get_db_connection()` maakt een SQLite connectie
- `DataService(conn, gebruiker_id)` stelt de gebruiker context in

#### Stap 3: DataService initialisatie
**Bestand**: `app/services.py` - `DataService.__init__()`

```python
def __init__(self, connection: sqlite3.Connection, gebruiker_id: Optional[int] = None):
    self.conn = connection
    if gebruiker_id:
        set_current_user_id(gebruiker_id)  # ← Dit is cruciaal!
```

**Wat gebeurt er?**
- `set_current_user_id()` wordt aangeroepen
- Dit zet een globale variabele `_current_user_id` in `app/database.py`
- Deze context wordt gebruikt voor alle RLS filtering

#### Stap 4: RLS Filtering in get_cliënten_for_gebruiker()
**Bestand**: `app/services.py` - `get_cliënten_for_gebruiker()`

```python
async def get_cliënten_for_gebruiker(self, gebruiker_id: int):
    # 1. Haal gebruiker info op (Rol, AfdelingID)
    user_rol = 'Behandelaar'
    user_afdeling_id = 1
    
    # 2. Haal ALLE cliënten op uit database
    all_cliënten = [...]  # Alle 20+ cliënten
    
    # 3. Filter applicatie-level op basis van rol
    filtered_cliënten = []
    for cliënt in all_cliënten:
        has_access = False
        
        # Vestigings Manager: alles
        if user_rol == 'Vestigings Manager':
            has_access = True
        
        # Manager: alleen eigen afdeling
        elif user_rol == 'Manager' and cliënt['AfdelingID'] == user_afdeling_id:
            has_access = True
        
        # Behandelaar: alleen eigen cliënten
        elif user_rol == 'Behandelaar' and cliënt['BehandelaarID'] == gebruiker_id:
            has_access = True
        
        # Check Toegangsrechten tabel
        if not has_access:
            # Check expliciete rechten...
        
        if has_access:
            filtered_cliënten.append(cliënt)
    
    return filtered_cliënten  # Alleen toegestane cliënten
```

**Wat gebeurt er?**
- Alle cliënten worden opgehaald uit de database
- **Applicatie-level filtering** wordt toegepast:
  - Vestigings Manager → ziet alles
  - Manager → ziet alleen cliënten in eigen afdeling
  - Behandelaar → ziet alleen eigen toegewezen cliënten
- Toegangsrechten tabel wordt gecheckt voor expliciete rechten
- Alleen toegestane cliënten worden geretourneerd

#### Stap 5: Template rendering
**Bestand**: `templates/dashboard.html`

```python
return templates.TemplateResponse("dashboard.html", {
    "request": request,
    "gebruiker": gebruiker,
    "cliënten": cliënten,  # ← Alleen gefilterde cliënten!
    "rls_info": rls_info
})
```

**Wat gebeurt er?**
- Jinja2 template wordt gerenderd
- Alleen de gefilterde cliënten worden getoond
- RLS statistieken worden getoond (totaal vs zichtbaar)

---

## Componenten Uitleg

### 1. Database Layer (`app/database.py`)

**Verantwoordelijkheid**: Database connectie management en user context

#### `DatabaseConnection` class
```python
class DatabaseConnection:
    def get_connection(self):
        # Maakt SQLite connectie
        # Enable foreign keys
        return conn
```

**Wat doet het?**
- Beheert SQLite database connecties
- Zorgt dat database bestaat
- Configureert foreign keys

#### `set_current_user_id()` / `get_current_user_id()`
```python
_current_user_id: Optional[int] = None

def set_current_user_id(user_id: Optional[int]):
    global _current_user_id
    _current_user_id = user_id

def get_current_user_id() -> Optional[int]:
    return _current_user_id
```

**Wat doet het?**
- Slaat huidige gebruiker ID op in globale variabele
- Wordt gebruikt voor applicatie-level RLS
- **Belangrijk**: Dit is thread-local in productie (nu global voor demo)

**Waarom?**
- SQLite heeft geen native RLS zoals SQL Server
- We simuleren RLS op applicatie niveau
- Elke query kan de huidige gebruiker checken

---

### 2. Services Layer (`app/services.py`)

**Verantwoordelijkheid**: Business logic en RLS filtering

#### `DataService` class

**Initialisatie**:
```python
service = DataService(conn, gebruiker_id=5)
# → Roept set_current_user_id(5) aan
```

**Belangrijkste methodes**:

##### `get_cliënten_for_gebruiker(gebruiker_id)`
**Wat doet het?**
1. Haalt gebruiker rol en afdeling op
2. Haalt **alle** cliënten op uit database
3. Filtert applicatie-level op basis van:
   - **Rol**: Vestigings Manager / Manager / Behandelaar
   - **AfdelingID**: Managers zien alleen eigen afdeling
   - **BehandelaarID**: Behandelaren zien alleen eigen cliënten
   - **Toegangsrechten tabel**: Expliciete rechten
4. Voegt kleurcodering toe per afdeling/behandelaar
5. Retourneert gefilterde lijst

**RLS Logica**:
```python
# Vestigings Manager: alles
if user_rol == 'Vestigings Manager':
    has_access = True

# Manager: alleen eigen afdeling
elif user_rol == 'Manager' and cliënt['AfdelingID'] == user_afdeling_id:
    has_access = True

# Behandelaar: alleen eigen cliënten
elif user_rol == 'Behandelaar' and cliënt['BehandelaarID'] == gebruiker_id:
    has_access = True
```

##### `get_rls_info(gebruiker_id)`
**Wat doet het?**
- Haalt statistieken op:
  - Totaal aantal cliënten in database
  - Aantal cliënten in eigen afdeling
  - Aantal eigen cliënten (voor behandelaren)
  - Aantal zichtbare cliënten (na RLS)
- Genereert RLS regels uitleg
- Retourneert dict met alle info

##### `get_organogram_data()`
**Wat doet het?**
- Haalt organisatiestructuur op:
  - Vestigings Manager
  - Afdelingen met managers
  - Behandelaren per afdeling
  - Aantal cliënten per behandelaar
- Retourneert geneste structuur voor organogram

##### `get_color_for_client(afdeling_id, behandelaar_id)`
**Wat doet het?**
- Genereert kleuren op basis van:
  - **AfdelingID**: Elke afdeling krijgt basiskleur
    - Afdeling 1 (X): Groen
    - Afdeling 2 (Y): Blauw
    - Afdeling 3 (Z): Paars
  - **BehandelaarID**: Verschillende tinten binnen afdeling
- Retourneert CSS kleuren (background, border, text)

---

### 3. Authentication Layer (`app/auth.py`)

**Verantwoordelijkheid**: Token validatie en gebruiker extractie

#### `get_current_user(authorization: str)`
**Wat doet het?**
1. Haalt `Authorization: Bearer <token>` header op
2. Decode JWT token (zonder signature verificatie in demo)
3. Extraheert claims:
   - `oid`: Azure AD Object ID
   - `name`: Volledige naam
   - `email`: Email adres
   - `roles`: Rollen array
4. Retourneert gebruiker dict

**In productie**:
- Token signature moet worden gevalideerd
- Azure AD public keys moeten worden opgehaald
- Token expiry moet worden gecheckt

---

### 4. FastAPI Routes (`app/main.py`)

**Verantwoordelijkheid**: HTTP endpoints en request handling

#### Route: `/demo/{gebruiker_naam}`
**Wat doet het?**
- Demo modus zonder authenticatie
- Zoekt gebruiker op naam
- Maakt DataService met gebruiker_id
- Haalt data op (RLS wordt toegepast)
- Renders dashboard template

#### Route: `/dashboard`
**Wat doet het?**
- Vereist Bearer token (via `get_current_user`)
- Haalt gebruiker op via Azure AD Object ID
- Maakt DataService met gebruiker_id
- Haalt data op (RLS wordt toegepast)
- Renders dashboard template

#### Route: `/rls-demo`
**Wat doet het?**
- Haalt organogram data op
- Renders RLS demo pagina met organogram

#### Route: `/api/obo/cliënten`
**Wat doet het?**
- Simuleert On-Behalf-Of flow
- Ontvangt gebruiker naam (in productie: OBO token)
- Maakt DataService met gebruiker_id
- Haalt cliënten op namens die gebruiker
- Retourneert JSON response

---

### 5. Templates (Frontend)

#### `templates/index.html`
**Wat doet het?**
- Hoofdpagina met demo overzicht
- Twee grote demo cards:
  - RLS & Identity Propagation Demo
  - On-Behalf-Of Flow Demo

#### `templates/rls_demo.html`
**Wat doet het?**
- RLS demo pagina met:
  - Uitleg over RLS
  - Interactief organogram met lijntjes
  - Klikbare gebruikers (gecommentarieerd door gebruiker)

#### `templates/dashboard.html`
**Wat doet het?**
- Gebruiker dashboard met:
  - Gebruiker info en rol badge
  - Statistieken (zichtbare cliënten, collega's)
  - RLS uitleg (collapsible)
  - Cliënten lijst met kleurcodering
  - Collega's lijst
  - Waarschuwing als niet alles zichtbaar is

#### `templates/obo_demo.html`
**Wat doet het?**
- On-Behalf-Of flow demonstratie
- Interactieve flow diagram
- Gebruiker selectie
- Backend service call simulatie

---

## RLS (Row Level Security) Mechanisme

### Waarom Applicatie-level RLS?

SQLite heeft **geen native RLS** zoals SQL Server. Daarom implementeren we RLS op applicatie niveau:

1. **Database**: Alle data is toegankelijk
2. **Applicatie**: Filtert data voordat het wordt getoond
3. **Voordeel**: Werkt met elke database
4. **Nadeel**: Moet in elke query worden toegepast

### RLS Filtering Logica

#### Stap 1: Gebruiker Context
```python
# In DataService.__init__()
set_current_user_id(gebruiker_id)
# → Slaat gebruiker ID op in globale variabele
```

#### Stap 2: Data Ophalen
```python
# Haal ALLE cliënten op
cursor.execute("SELECT * FROM Cliënten WHERE Actief = 1")
all_cliënten = cursor.fetchall()
```

#### Stap 3: Filter Applicatie-level
```python
for cliënt in all_cliënten:
    has_access = False
    
    # Check rol-gebaseerde regels
    if user_rol == 'Vestigings Manager':
        has_access = True
    elif user_rol == 'Manager' and cliënt['AfdelingID'] == user_afdeling_id:
        has_access = True
    elif user_rol == 'Behandelaar' and cliënt['BehandelaarID'] == gebruiker_id:
        has_access = True
    
    # Check expliciete rechten
    if not has_access:
        # Check Toegangsrechten tabel...
    
    if has_access:
        filtered_cliënten.append(cliënt)
```

### RLS Regels

#### Regel 1: Vestigings Manager
- **Toegang**: Alle cliënten in alle afdelingen
- **Implementatie**: `if user_rol == 'Vestigings Manager': has_access = True`
- **Waarom**: Hoogste niveau, moet alles kunnen zien

#### Regel 2: Manager
- **Toegang**: Alle cliënten in eigen afdeling
- **Implementatie**: `if user_rol == 'Manager' and cliënt['AfdelingID'] == user_afdeling_id`
- **Waarom**: Managers moeten overzicht hebben over hun afdeling

#### Regel 3: Behandelaar
- **Toegang**: Alleen eigen toegewezen cliënten
- **Implementatie**: `if user_rol == 'Behandelaar' and cliënt['BehandelaarID'] == gebruiker_id`
- **Waarom**: Privacy - behandelaren zien alleen hun eigen cliënten

#### Regel 4: Toegangsrechten Tabel
- **Toegang**: Expliciete rechten per cliënt of afdeling
- **Implementatie**: Check `Toegangsrechten` tabel
- **Waarom**: Flexibiliteit voor uitzonderingen

### RLS Statistieken

De `get_rls_info()` functie berekent:
- **Totaal cliënten**: `SELECT COUNT(*) FROM Cliënten WHERE Actief = 1`
- **Cliënten in afdeling**: `SELECT COUNT(*) FROM Cliënten WHERE AfdelingID = ?`
- **Eigen cliënten**: `SELECT COUNT(*) FROM Cliënten WHERE BehandelaarID = ?`
- **Zichtbare cliënten**: Lengte van gefilterde lijst

**Voorbeeld voor Behandelaar**:
- Totaal: 20 cliënten
- In afdeling: 9 cliënten
- Eigen: 4 cliënten
- Zichtbaar: 4 cliënten (na RLS)

---

## Identity Propagation Flow

### Scenario: On-Behalf-Of Flow

```
┌──────────┐
│ Gebruiker│
│  (Ralph) │
└────┬─────┘
     │ 1. Login met OAuth token
     ▼
┌─────────────────┐
│ Frontend App    │
│ (React/Vue/etc) │
└────┬────────────┘
     │ 2. Bearer token in header
     ▼
┌─────────────────┐
│ FastAPI Backend │
│ /api/obo/cliënten│
└────┬────────────┘
     │ 3. Valideer token
     │ 4. Extract gebruiker ID
     ▼
┌─────────────────┐
│ DataService     │
│ (gebruiker_id)  │
└────┬────────────┘
     │ 5. RLS filtering
     ▼
┌─────────────────┐
│ Database Query  │
│ (gefilterd)     │
└─────────────────┘
```

### Stap-voor-Stap OBO Flow

1. **Gebruiker logt in** → OAuth token ontvangen
2. **Frontend stuurt request** → `Authorization: Bearer <token>`
3. **Backend valideert token** → `get_current_user()` decode token
4. **Gebruiker opzoeken** → `get_gebruiker_by_azure_id(oid)`
5. **DataService maken** → `DataService(conn, gebruiker_id)`
6. **RLS filtering** → `get_cliënten_for_gebruiker()`
7. **Data retourneren** → Alleen toegestane cliënten

**Belangrijk**: De identiteit van de gebruiker wordt doorgegeven via:
- OAuth token → Azure AD Object ID
- Azure AD Object ID → Database GebruikerID
- GebruikerID → RLS filtering context

---

## Installatie & Setup

### Vereisten

- Python 3.10 of hoger
- Geen extra database server nodig (SQLite)

### Snelle Start (Windows)

```bash
start.bat
```

Dit script:
1. Maakt virtual environment aan
2. Installeert dependencies (`requirements.txt`)
3. Initialiseert database (`init_database.py`)
4. Start applicatie (`uvicorn app.main:app --reload`)

### Handmatige Installatie

```bash
# 1. Installeer dependencies
pip install -r requirements.txt

# 2. Initialiseer database
python init_database.py

# 3. Start applicatie
uvicorn app.main:app --reload
```

### Database Initialisatie

**Bestand**: `init_database.py`

**Wat doet het?**
1. Leest `dataset_identity_propagation_sqlite.sql`
2. Voert SQL script uit
3. Maakt tabellen aan:
   - `Gebruikers`: Managers, Behandelaren, Vestigings Manager
   - `Afdelingen`: Afdeling X, Y, Z
   - `Cliënten`: Test cliënten per afdeling
   - `Toegangsrechten`: Expliciete rechten
4. Vult testdata in

**Database locatie**: `data/IdentityPropagationDB.db`

---

## API Endpoints

### Frontend Routes

- `GET /` - Hoofdpagina met demo overzicht
- `GET /rls-demo` - RLS demo pagina met organogram
- `GET /dashboard` - Gebruiker dashboard (vereist Bearer token)
- `GET /demo/{gebruiker_naam}` - Demo modus zonder authenticatie
- `GET /obo-demo` - On-Behalf-Of flow demonstratie

### API Endpoints

- `GET /api/gebruiker` - Huidige gebruiker info (vereist Bearer token)
- `GET /api/cliënten` - Cliënten voor huidige gebruiker (RLS toegepast)
- `GET /api/collega-s` - Collega's in dezelfde afdeling
- `GET /api/obo/cliënten?gebruiker={naam}` - OBO flow simulatie

### Request/Response Voorbeelden

#### GET /demo/Ralph
**Response**: HTML dashboard pagina

#### GET /api/cliënten
**Headers**: `Authorization: Bearer <token>`
**Response**:
```json
[
  {
    "CliëntID": 1,
    "Voornaam": "Jan",
    "Achternaam": "Jansen",
    "AfdelingNaam": "Afdeling X",
    "BehandelaarNaam": "Ralph Behandelaar",
    "RLS_Reason": "Je bent de toegewezen behandelaar van deze cliënt",
    "colors": {
      "background": "rgba(0, 255, 136, 0.15)",
      "border": "rgb(30, 255, 166)",
      "text": "rgb(0, 255, 136)"
    }
  }
]
```

---

## Database Structuur

### Tabellen

#### `Gebruikers`
```sql
GebruikerID (PK)
Voornaam
Achternaam
Email
Rol ('Manager', 'Behandelaar', 'Vestigings Manager')
AfdelingID (FK)
AzureADObjectID
Actief
```

#### `Afdelingen`
```sql
AfdelingID (PK)
AfdelingNaam
Gebied
ManagerID (FK naar Gebruikers)
Actief
```

#### `Cliënten`
```sql
CliëntID (PK)
Voornaam
Achternaam
Geboortedatum
AfdelingID (FK)
BehandelaarID (FK naar Gebruikers)
Actief
```

#### `Toegangsrechten`
```sql
ToegangsrechtID (PK)
GebruikerID (FK)
CliëntID (FK, nullable)
AfdelingID (FK, nullable)
ToegangType ('Direct', 'ViaManager', 'ViaAfdeling')
Actief
```

### Relaties

```
Gebruikers ──┐
             ├──> Afdelingen (ManagerID)
             │
             └──> Cliënten (BehandelaarID)

Afdelingen ──> Cliënten (AfdelingID)

Toegangsrechten ──> Gebruikers (GebruikerID)
                 └──> Cliënten (CliëntID, optioneel)
                 └──> Afdelingen (AfdelingID, optioneel)
```

---

## Troubleshooting

### Database Fout

**Probleem**: Database niet gevonden of foutmelding

**Oplossing**:
```bash
# Verwijder oude database
rm data/IdentityPropagationDB.db

# Herinitialiseer
python init_database.py
```

### Data Niet Zichtbaar

**Probleem**: Gebruiker ziet geen cliënten

**Check**:
1. Gebruiker rol (Manager vs Behandelaar)
2. AfdelingID match
3. BehandelaarID match (voor Behandelaar)
4. Toegangsrechten tabel

**Debug**:
```python
# In app/services.py, voeg logging toe:
print(f"User rol: {user_rol}, Afdeling: {user_afdeling_id}")
print(f"Totaal cliënten: {len(all_cliënten)}")
print(f"Gefilterd: {len(filtered_cliënten)}")
```

### Organogram Toont Geen Data

**Probleem**: Organogram is leeg

**Oplossing**:
1. Check of `organogram_data` wordt doorgegeven aan template
2. Check database: `SELECT * FROM Gebruikers WHERE Rol = 'Vestigings Manager'`
3. Check `get_organogram_data()` functie

### Kleurcodering Werkt Niet

**Probleem**: Cliënten hebben geen kleuren

**Oplossing**:
1. Check of `get_color_for_client()` wordt aangeroepen
2. Check of `cliënt['colors']` in template wordt gebruikt
3. Check browser console voor CSS errors

---

## Belangrijke Concepten

### Identity Propagation

**Definitie**: Het doorgeven van gebruikersidentiteit door verschillende lagen van een applicatie.

**In deze app**:
1. OAuth token bevat Azure AD Object ID
2. Object ID wordt gemapped naar Database GebruikerID
3. GebruikerID wordt gebruikt voor RLS filtering
4. Identiteit blijft behouden door hele flow

### Applicatie-level RLS

**Definitie**: Row Level Security geïmplementeerd in applicatie code, niet in database.

**Voordelen**:
- Werkt met elke database (SQLite, MySQL, PostgreSQL)
- Flexibele filtering logica
- Makkelijk te debuggen

**Nadelen**:
- Moet in elke query worden toegepast
- Kan performance impact hebben (alle data ophalen, dan filteren)

### On-Behalf-Of Flow

**Definitie**: Een service applicatie kan namens een gebruiker resources ophalen.

**In deze app**:
- Frontend app krijgt OAuth token van gebruiker
- Frontend app vraagt backend om data
- Backend gebruikt OBO token om namens gebruiker data op te halen
- RLS wordt toegepast op basis van originele gebruiker

---

## Kleurcodering Systeem

### Per Afdeling

- **Afdeling X (ID 1)**: Groen (`hue: 150`)
- **Afdeling Y (ID 2)**: Blauw (`hue: 200`)
- **Afdeling Z (ID 3)**: Paars (`hue: 270`)

### Per Behandelaar

Binnen elke afdeling krijgen behandelaren verschillende tinten:
- Behandelaar ID 4: Lightness 38% (licht)
- Behandelaar ID 5: Lightness 46% (medium)
- Behandelaar ID 6: Lightness 54% (donker)

**Formule**: `lightness = 30 + (behandelaar_id % 5) * 8`

---

## Code Locaties

| Functionaliteit | Bestand | Functie |
|----------------|---------|---------|
| Database connectie | `app/database.py` | `DatabaseConnection.get_connection()` |
| User context | `app/database.py` | `set_current_user_id()` |
| RLS filtering | `app/services.py` | `get_cliënten_for_gebruiker()` |
| RLS statistieken | `app/services.py` | `get_rls_info()` |
| Organogram data | `app/services.py` | `get_organogram_data()` |
| Kleurcodering | `app/services.py` | `get_color_for_client()` |
| Token validatie | `app/auth.py` | `get_current_user()` |
| Demo route | `app/main.py` | `/demo/{gebruiker_naam}` |
| Dashboard route | `app/main.py` | `/dashboard` |
| OBO route | `app/main.py` | `/api/obo/cliënten` |

---

## Productie Overwegingen

### Security

1. **Token Validatie**: Implementeer echte Azure AD token validatie
2. **HTTPS**: Gebruik altijd HTTPS in productie
3. **Rate Limiting**: Voeg rate limiting toe aan API endpoints
4. **CORS**: Configureer CORS correct voor frontend

### Performance

1. **Database Indexen**: Voeg indexen toe op veel gebruikte kolommen
2. **Caching**: Cache RLS info en organogram data
3. **Connection Pooling**: Gebruik connection pooling voor SQLite
4. **Query Optimalisatie**: Filter in SQL waar mogelijk (niet alleen applicatie-level)

### Database

1. **SQL Server**: Migreer naar SQL Server met native RLS
2. **Azure SQL**: Gebruik Azure SQL met RLS policies
3. **Backup**: Implementeer database backups

---

## Licentie

Interne tool voor demonstratie doeleinden.

---

**Laatste update**: 2024
**Versie**: 1.0.0
