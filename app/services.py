"""
Business logic services voor data ophalen
"""
from typing import List, Optional, Dict, Any
import sqlite3
from app.database import get_current_user_id, set_current_user_id


def get_color_for_client(afdeling_id: Optional[int], behandelaar_id: Optional[int]) -> Dict[str, str]:
    """
    Genereer kleuren op basis van afdeling en behandelaar.
    Elke afdeling krijgt een basiskleur, behandelaren binnen die afdeling krijgen verschillende tinten.
    """
    # Basis kleuren per afdeling (in HSL voor makkelijke tint variatie)
    afdeling_colors = {
        1: {'h': 150, 's': 100, 'l': 50},  # Groen voor Afdeling X
        2: {'h': 200, 's': 100, 'l': 50},  # Blauw voor Afdeling Y
        3: {'h': 270, 's': 100, 'l': 50},  # Paars voor Afdeling Z
    }
    
    # Default kleur (grijs) als afdeling niet bekend is
    default_color = {'h': 0, 's': 0, 'l': 50}
    
    base_color = afdeling_colors.get(afdeling_id, default_color)
    
    # Genereer verschillende tinten per behandelaar binnen dezelfde afdeling
    # Lichtere tinten voor lagere behandelaar IDs, donkerdere voor hogere
    if behandelaar_id:
        # Variatie in lightness: 30-70% (licht tot donker)
        # Verdeel behandelaars over het bereik
        behandelaar_index = (behandelaar_id % 5) + 1  # 1-5
        lightness = 30 + (behandelaar_index * 8)  # 30, 38, 46, 54, 62
    else:
        # Geen behandelaar: medium tint
        lightness = 50
    
    # Converteer HSL naar RGB (vereenvoudigde versie)
    h = base_color['h'] / 360
    s = base_color['s'] / 100
    l = lightness / 100
    
    # HSL naar RGB conversie
    if s == 0:
        r = g = b = l
    else:
        def hue_to_rgb(p, q, t):
            if t < 0: t += 1
            if t > 1: t -= 1
            if t < 1/6: return p + (q - p) * 6 * t
            if t < 1/2: return q
            if t < 2/3: return p + (q - p) * (2/3 - t) * 6
            return p
        
        q = l * (1 + s) if l < 0.5 else l + s - l * s
        p = 2 * l - q
        r = hue_to_rgb(p, q, h + 1/3)
        g = hue_to_rgb(p, q, h)
        b = hue_to_rgb(p, q, h - 1/3)
    
    # Converteer naar 0-255 range
    r = int(r * 255)
    g = int(g * 255)
    b = int(b * 255)
    
    # Genereer border en background kleuren
    border_r = min(255, r + 30)
    border_g = min(255, g + 30)
    border_b = min(255, b + 30)
    
    return {
        'background': f'rgba({r}, {g}, {b}, 0.15)',
        'border': f'rgb({border_r}, {border_g}, {border_b})',
        'text': f'rgb({r}, {g}, {b})',
        'background_hover': f'rgba({r}, {g}, {b}, 0.25)',
    }


class DataService:
    """Service voor database operaties met applicatie-level RLS"""
    
    def __init__(self, connection: sqlite3.Connection, gebruiker_id: Optional[int] = None):
        self.conn = connection
        if gebruiker_id:
            set_current_user_id(gebruiker_id)
    
    async def get_gebruiker_by_azure_id(self, azure_ad_object_id: Optional[str]) -> Optional[Dict[str, Any]]:
        """Haal gebruiker op basis van Azure AD Object ID"""
        if not azure_ad_object_id:
            return None
        
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                SELECT 
                    g.GebruikerID,
                    g.Voornaam,
                    g.Achternaam,
                    g.Email,
                    g.Rol,
                    g.AfdelingID,
                    g.AzureADObjectID,
                    a.AfdelingNaam,
                    a.Gebied
                FROM Gebruikers g
                LEFT JOIN Afdelingen a ON g.AfdelingID = a.AfdelingID
                WHERE g.AzureADObjectID = ? AND g.Actief = 1
            """, (azure_ad_object_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            return {
                "GebruikerID": row[0],
                "Voornaam": row[1],
                "Achternaam": row[2],
                "Email": row[3],
                "Rol": row[4],
                "AfdelingID": row[5],
                "AzureADObjectID": row[6] if row[6] else None,
                "AfdelingNaam": row[7],
                "Gebied": row[8],
                "VolledigeNaam": f"{row[1]} {row[2]}"
            }
        finally:
            cursor.close()
    
    async def get_gebruiker_by_naam(self, naam: str) -> Optional[Dict[str, Any]]:
        """Haal gebruiker op basis van voornaam of volledige naam (voor demo modus)"""
        cursor = self.conn.cursor()
        try:
            # Probeer eerst op volledige naam (Voornaam + Achternaam)
            if ' ' in naam:
                parts = naam.split(' ', 1)
                cursor.execute("""
                    SELECT 
                        g.GebruikerID,
                        g.Voornaam,
                        g.Achternaam,
                        g.Email,
                        g.Rol,
                        g.AfdelingID,
                        g.AzureADObjectID,
                        a.AfdelingNaam,
                        a.Gebied
                    FROM Gebruikers g
                    LEFT JOIN Afdelingen a ON g.AfdelingID = a.AfdelingID
                    WHERE g.Voornaam = ? AND g.Achternaam = ? AND g.Actief = 1
                """, (parts[0], parts[1]))
            else:
                # Anders zoek alleen op voornaam
                cursor.execute("""
                    SELECT 
                        g.GebruikerID,
                        g.Voornaam,
                        g.Achternaam,
                        g.Email,
                        g.Rol,
                        g.AfdelingID,
                        g.AzureADObjectID,
                        a.AfdelingNaam,
                        a.Gebied
                    FROM Gebruikers g
                    LEFT JOIN Afdelingen a ON g.AfdelingID = a.AfdelingID
                    WHERE g.Voornaam = ? AND g.Actief = 1
                """, (naam,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            return {
                "GebruikerID": row[0],
                "Voornaam": row[1],
                "Achternaam": row[2],
                "Email": row[3],
                "Rol": row[4],
                "AfdelingID": row[5],
                "AzureADObjectID": row[6] if row[6] else None,
                "AfdelingNaam": row[7],
                "Gebied": row[8],
                "VolledigeNaam": f"{row[1]} {row[2]}"
            }
        finally:
            cursor.close()
    
    async def get_rls_info(self, gebruiker_id: int) -> Dict[str, Any]:
        """Haal RLS informatie op voor een gebruiker"""
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                SELECT Rol, AfdelingID, Voornaam, Achternaam
                FROM Gebruikers
                WHERE GebruikerID = ?
            """, (gebruiker_id,))
            
            user_row = cursor.fetchone()
            if not user_row:
                return {}
            
            user_rol = user_row[0]
            user_afdeling_id = user_row[1]
            user_naam = f"{user_row[2]} {user_row[3]}"
            
            # Haal afdeling naam op (kan NULL zijn voor Vestigings Manager)
            afdeling_naam = "Alle Afdelingen"
            if user_afdeling_id:
                cursor.execute("SELECT AfdelingNaam FROM Afdelingen WHERE AfdelingID = ?", (user_afdeling_id,))
                afdeling_row = cursor.fetchone()
                if afdeling_row:
                    afdeling_naam = afdeling_row[0]
            
            # Haal totaal aantal cliënten op
            cursor.execute("SELECT COUNT(*) FROM Cliënten WHERE Actief = 1")
            totaal_cliënten = cursor.fetchone()[0]
            
            # Haal aantal cliënten in eigen afdeling
            cursor.execute("""
                SELECT COUNT(*) FROM Cliënten 
                WHERE AfdelingID = ? AND Actief = 1
            """, (user_afdeling_id,))
            cliënten_in_afdeling = cursor.fetchone()[0]
            
            # Haal aantal eigen cliënten (voor behandelaren)
            cursor.execute("""
                SELECT COUNT(*) FROM Cliënten 
                WHERE BehandelaarID = ? AND Actief = 1
            """, (gebruiker_id,))
            eigen_cliënten = cursor.fetchone()[0]
            
            rls_rules = []
            if user_rol == 'Vestigings Manager':
                rls_rules.append({
                    "regel": "Vestigings Manager Regel",
                    "beschrijving": "Als Vestigings Manager heb je toegang tot alle cliënten in alle afdelingen",
                    "toepassing": f"Je ziet alle {totaal_cliënten} cliënten in de database"
                })
            elif user_rol == 'Manager':
                rls_rules.append({
                    "regel": "Manager Regel",
                    "beschrijving": f"Als Manager van {afdeling_naam} zie je alle cliënten in je afdeling",
                    "toepassing": f"Je ziet {cliënten_in_afdeling} cliënten in je afdeling (van {totaal_cliënten} totaal)"
                })
            elif user_rol == 'Behandelaar':
                rls_rules.append({
                    "regel": "Behandelaar Regel",
                    "beschrijving": "Als Behandelaar zie je alleen cliënten die aan jou zijn toegewezen",
                    "toepassing": f"Je ziet {eigen_cliënten} cliënten die aan jou zijn toegewezen (van {cliënten_in_afdeling} in je afdeling, {totaal_cliënten} totaal)"
                })
            
            rls_rules.append({
                "regel": "Toegangsrechten Tabel",
                "beschrijving": "Expliciete toegangsrechten kunnen worden toegekend via de Toegangsrechten tabel",
                "toepassing": "Wordt gecontroleerd per cliënt"
            })
            
            return {
                "gebruiker_naam": user_naam,
                "rol": user_rol,
                "afdeling_id": user_afdeling_id,
                "afdeling_naam": afdeling_naam,
                "totaal_cliënten": totaal_cliënten,
                "cliënten_in_afdeling": cliënten_in_afdeling,
                "eigen_cliënten": eigen_cliënten,
                "rls_rules": rls_rules
            }
        finally:
            cursor.close()
    
    async def get_cliënten_for_gebruiker(self, gebruiker_id: int) -> List[Dict[str, Any]]:
        """
        Haal cliënten op die deze gebruiker mag zien
        Applicatie-level RLS filtering (SQLite heeft geen native RLS)
        """
        cursor = self.conn.cursor()
        try:
            # Haal gebruiker info op
            cursor.execute("""
                SELECT Rol, AfdelingID
                FROM Gebruikers
                WHERE GebruikerID = ?
            """, (gebruiker_id,))
            
            user_row = cursor.fetchone()
            if not user_row:
                return []
            
            user_rol = user_row[0]
            user_afdeling_id = user_row[1]
            
            # Haal alle cliënten op (we filteren applicatie-level)
            cursor.execute("""
                SELECT 
                    c.CliëntID,
                    c.Voornaam,
                    c.Achternaam,
                    c.Geboortedatum,
                    c.AfdelingID,
                    c.BehandelaarID,
                    a.AfdelingNaam,
                    g.Voornaam || ' ' || g.Achternaam AS BehandelaarNaam
                FROM Cliënten c
                LEFT JOIN Afdelingen a ON c.AfdelingID = a.AfdelingID
                LEFT JOIN Gebruikers g ON c.BehandelaarID = g.GebruikerID
                WHERE c.Actief = 1
                ORDER BY c.Voornaam, c.Achternaam
            """)
            
            columns = [column[0] for column in cursor.description]
            all_cliënten = []
            for row in cursor.fetchall():
                result = dict(zip(columns, row))
                if result.get("Geboortedatum"):
                    result["Geboortedatum"] = result["Geboortedatum"]
                all_cliënten.append(result)
            
            # Applicatie-level RLS filtering met uitleg
            filtered_cliënten = []
            for cliënt in all_cliënten:
                has_access = False
                access_reason = []
                
                # Vestigings Manager: toegang tot alles
                if user_rol == 'Vestigings Manager':
                    has_access = True
                    access_reason.append("Vestigings Manager heeft toegang tot alle cliënten")
                
                # Manager: toegang tot alle cliënten in eigen afdeling
                elif user_rol == 'Manager' and cliënt['AfdelingID'] == user_afdeling_id:
                    has_access = True
                    access_reason.append(f"Manager heeft toegang tot alle cliënten in {cliënt.get('AfdelingNaam', 'eigen afdeling')}")
                
                # Behandelaar: toegang tot eigen cliënten
                elif user_rol == 'Behandelaar' and cliënt['BehandelaarID'] == gebruiker_id:
                    has_access = True
                    access_reason.append("Je bent de toegewezen behandelaar van deze cliënt")
                
                # Check Toegangsrechten tabel
                if not has_access:
                    cursor.execute("""
                        SELECT ToegangType FROM Toegangsrechten
                        WHERE GebruikerID = ? 
                        AND Actief = 1
                        AND (
                            CliëntID = ? OR
                            (CliëntID IS NULL AND AfdelingID = ?)
                        )
                    """, (gebruiker_id, cliënt['CliëntID'], cliënt['AfdelingID']))
                    toegang_row = cursor.fetchone()
                    if toegang_row:
                        has_access = True
                        toegang_type = toegang_row[0]
                        if toegang_type == 'Direct':
                            access_reason.append("Directe toegang via Toegangsrechten tabel")
                        elif toegang_type == 'ViaManager':
                            access_reason.append("Toegang via manager rol")
                        elif toegang_type == 'ViaAfdeling':
                            access_reason.append("Toegang via afdeling in Toegangsrechten")
                
                if has_access:
                    cliënt['RLS_Reason'] = access_reason[0] if access_reason else "Toegang verleend"
                    # Voeg kleurcodering toe op basis van afdeling en behandelaar
                    cliënt['colors'] = get_color_for_client(cliënt.get('AfdelingID'), cliënt.get('BehandelaarID'))
                    filtered_cliënten.append(cliënt)
            
            return filtered_cliënten
        finally:
            cursor.close()
    
    async def get_collega_s(self, afdeling_id: Optional[int], exclude_gebruiker_id: int) -> List[Dict[str, Any]]:
        """Haal collega's op in dezelfde afdeling"""
        if not afdeling_id:
            return []
        
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                SELECT 
                    g.GebruikerID,
                    g.Voornaam,
                    g.Achternaam,
                    g.Email,
                    g.Rol,
                    g.AfdelingID,
                    a.AfdelingNaam
                FROM Gebruikers g
                LEFT JOIN Afdelingen a ON g.AfdelingID = a.AfdelingID
                WHERE g.AfdelingID = ? 
                AND g.GebruikerID != ?
                AND g.Actief = 1
                ORDER BY g.Rol, g.Voornaam
            """, (afdeling_id, exclude_gebruiker_id))
            
            columns = [column[0] for column in cursor.description]
            results = []
            for row in cursor.fetchall():
                result = dict(zip(columns, row))
                result["VolledigeNaam"] = f"{result['Voornaam']} {result['Achternaam']}"
                results.append(result)
            
            return results
        finally:
            cursor.close()
    
    async def get_organogram_data(self) -> Dict[str, Any]:
        """Haal organisatiestructuur op voor organogram"""
        cursor = self.conn.cursor()
        try:
            # Haal Vestigings Manager op
            cursor.execute("""
                SELECT GebruikerID, Voornaam, Achternaam, Rol
                FROM Gebruikers
                WHERE Rol = 'Vestigings Manager' AND Actief = 1
            """)
            vestigings_manager_row = cursor.fetchone()
            vestigings_manager = None
            if vestigings_manager_row:
                vestigings_manager = {
                    "GebruikerID": vestigings_manager_row[0],
                    "Voornaam": vestigings_manager_row[1],
                    "Achternaam": vestigings_manager_row[2],
                    "Rol": vestigings_manager_row[3],
                    "VolledigeNaam": f"{vestigings_manager_row[1]} {vestigings_manager_row[2]}"
                }
            
            # Haal alle afdelingen op met managers
            cursor.execute("""
                SELECT 
                    a.AfdelingID,
                    a.AfdelingNaam,
                    a.Gebied,
                    a.ManagerID,
                    m.Voornaam || ' ' || m.Achternaam AS ManagerNaam,
                    m.GebruikerID AS ManagerGebruikerID
                FROM Afdelingen a
                LEFT JOIN Gebruikers m ON a.ManagerID = m.GebruikerID
                WHERE a.Actief = 1
                ORDER BY a.AfdelingID
            """)
            
            afdelingen = []
            for row in cursor.fetchall():
                afdeling_id = row[0]
                afdeling_naam = row[1]
                gebied = row[2]
                manager_id = row[3]
                manager_naam = row[4]
                manager_gebruiker_id = row[5]
                
                # Haal behandelaren op voor deze afdeling
                cursor.execute("""
                    SELECT 
                        g.GebruikerID,
                        g.Voornaam,
                        g.Achternaam,
                        COUNT(c.CliëntID) AS AantalCliënten
                    FROM Gebruikers g
                    LEFT JOIN Cliënten c ON g.GebruikerID = c.BehandelaarID AND c.Actief = 1
                    WHERE g.AfdelingID = ? 
                    AND g.Rol = 'Behandelaar'
                    AND g.Actief = 1
                    GROUP BY g.GebruikerID, g.Voornaam, g.Achternaam
                    ORDER BY g.Voornaam
                """, (afdeling_id,))
                
                behandelaren = []
                for beh_row in cursor.fetchall():
                    behandelaren.append({
                        "GebruikerID": beh_row[0],
                        "Voornaam": beh_row[1],
                        "Achternaam": beh_row[2],
                        "AantalCliënten": beh_row[3],
                        "VolledigeNaam": f"{beh_row[1]} {beh_row[2]}"
                    })
                
                # Haal totaal aantal cliënten in afdeling
                cursor.execute("""
                    SELECT COUNT(*) FROM Cliënten
                    WHERE AfdelingID = ? AND Actief = 1
                """, (afdeling_id,))
                totaal_cliënten = cursor.fetchone()[0]
                
                afdelingen.append({
                    "AfdelingID": afdeling_id,
                    "AfdelingNaam": afdeling_naam,
                    "Gebied": gebied,
                    "ManagerID": manager_id,
                    "ManagerNaam": manager_naam,
                    "ManagerGebruikerID": manager_gebruiker_id,
                    "Behandelaren": behandelaren,
                    "TotaalCliënten": totaal_cliënten
                })
            
            return {
                "VestigingsManager": vestigings_manager,
                "Afdelingen": afdelingen
            }
        finally:
            cursor.close()

