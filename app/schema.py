"""
Schema en testdata voor de Identity Propagation demo.
Alles staat in Python; geen extern SQL-bestand of handmatige database-setup nodig.
"""
import secrets


def get_schema_sql() -> str:
    """
    Retourneert het volledige SQL-script (tabellen + testdata).
    Azure AD Object IDs worden per run gegenereerd voor demo-doeleinden.
    """
    # Zeven gebruikers: 3 managers, 3 behandelaren, 1 vestigings manager
    azure_ids = [secrets.token_hex(16) for _ in range(7)]

    return f"""
CREATE TABLE IF NOT EXISTS Gebruikers (
    GebruikerID INTEGER PRIMARY KEY AUTOINCREMENT,
    Voornaam TEXT NOT NULL,
    Achternaam TEXT NOT NULL,
    Email TEXT NOT NULL UNIQUE,
    Rol TEXT NOT NULL CHECK (Rol IN ('Manager', 'Behandelaar', 'Vestigings Manager')),
    AfdelingID INTEGER,
    AzureADObjectID TEXT,
    Actief INTEGER DEFAULT 1,
    AangemaaktOp DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS Afdelingen (
    AfdelingID INTEGER PRIMARY KEY AUTOINCREMENT,
    AfdelingNaam TEXT NOT NULL,
    Gebied TEXT NOT NULL,
    ManagerID INTEGER,
    Actief INTEGER DEFAULT 1,
    FOREIGN KEY (ManagerID) REFERENCES Gebruikers(GebruikerID)
);

CREATE TABLE IF NOT EXISTS Cliënten (
    CliëntID INTEGER PRIMARY KEY AUTOINCREMENT,
    Voornaam TEXT NOT NULL,
    Achternaam TEXT NOT NULL,
    Geboortedatum DATE,
    AfdelingID INTEGER NOT NULL,
    BehandelaarID INTEGER,
    Actief INTEGER DEFAULT 1,
    AangemaaktOp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (AfdelingID) REFERENCES Afdelingen(AfdelingID),
    FOREIGN KEY (BehandelaarID) REFERENCES Gebruikers(GebruikerID)
);

CREATE TABLE IF NOT EXISTS Toegangsrechten (
    ToegangsrechtID INTEGER PRIMARY KEY AUTOINCREMENT,
    GebruikerID INTEGER NOT NULL,
    CliëntID INTEGER,
    AfdelingID INTEGER,
    ToegangType TEXT NOT NULL CHECK (ToegangType IN ('Direct', 'ViaManager', 'ViaAfdeling')),
    Actief INTEGER DEFAULT 1,
    AangemaaktOp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (GebruikerID) REFERENCES Gebruikers(GebruikerID),
    FOREIGN KEY (CliëntID) REFERENCES Cliënten(CliëntID),
    FOREIGN KEY (AfdelingID) REFERENCES Afdelingen(AfdelingID)
);

INSERT OR IGNORE INTO Afdelingen (AfdelingID, AfdelingNaam, Gebied) VALUES
(1, 'Afdeling X', 'Gebied Noord'),
(2, 'Afdeling Y', 'Gebied Zuid'),
(3, 'Afdeling Z', 'Gebied Oost');

INSERT OR IGNORE INTO Gebruikers (GebruikerID, Voornaam, Achternaam, Email, Rol, AfdelingID, AzureADObjectID) VALUES
(1, 'Ruud', 'Manager', 'ruud.manager@cordaan.nl', 'Manager', 1, '{azure_ids[0]}'),
(2, 'Bertram', 'Manager', 'bertram.manager@cordaan.nl', 'Manager', 2, '{azure_ids[1]}'),
(3, 'Marc', 'Manager', 'marc.manager@cordaan.nl', 'Manager', 3, '{azure_ids[2]}'),
(4, 'Ralph', 'Behandelaar', 'ralph.behandelaar@cordaan.nl', 'Behandelaar', 1, '{azure_ids[3]}'),
(5, 'Bart', 'Behandelaar', 'bart.behandelaar@cordaan.nl', 'Behandelaar', 1, '{azure_ids[4]}'),
(6, 'Vincent', 'Behandelaar', 'vincent.behandelaar@cordaan.nl', 'Behandelaar', 2, '{azure_ids[5]}'),
(7, 'Jimmy', 'Vestigings Manager', 'jimmy.vestigingsmanager@cordaan.nl', 'Vestigings Manager', NULL, '{azure_ids[6]}');

UPDATE Afdelingen SET ManagerID = 1 WHERE AfdelingID = 1;
UPDATE Afdelingen SET ManagerID = 2 WHERE AfdelingID = 2;
UPDATE Afdelingen SET ManagerID = 3 WHERE AfdelingID = 3;

INSERT OR IGNORE INTO Cliënten (Voornaam, Achternaam, Geboortedatum, AfdelingID, BehandelaarID) VALUES
('Jan', 'Jansen', '1950-03-15', 1, 4),
('Piet', 'Pietersen', '1945-07-22', 1, 4),
('Klaas', 'Klaassen', '1960-11-08', 1, 5),
('Marie', 'Marissen', '1955-09-30', 1, 5),
('Henk', 'Hendriksen', '1948-12-05', 1, 4),
('Willem', 'Willemsen', '1952-08-20', 1, 4),
('Emma', 'Emmerik', '1947-11-12', 1, 5),
('Dirk', 'Dirkse', '1958-02-28', 1, 5),
('Sara', 'Sanders', '1953-06-15', 1, 4),
('Anna', 'Andersen', '1952-04-18', 2, 6),
('Erik', 'Eriksen', '1947-06-25', 2, 6),
('Sophie', 'Smit', '1958-08-12', 2, 6),
('Lucas', 'Lubbers', '1951-09-05', 2, 6),
('Mia', 'Meijer', '1949-12-30', 2, 6),
('Noah', 'Nijland', '1955-03-22', 2, 6),
('Olivia', 'Oosterhuis', '1957-07-18', 2, 6),
('Lisa', 'Larsen', '1953-02-14', 3, NULL),
('Tom', 'Thomassen', '1949-10-20', 3, NULL),
('Iris', 'Ivens', '1954-05-08', 3, NULL),
('Finn', 'Fransen', '1951-01-25', 3, NULL);

INSERT OR IGNORE INTO Toegangsrechten (GebruikerID, AfdelingID, ToegangType) VALUES
(1, 1, 'ViaManager'),
(2, 2, 'ViaManager'),
(3, 3, 'ViaManager');

INSERT OR IGNORE INTO Toegangsrechten (GebruikerID, CliëntID, ToegangType)
SELECT BehandelaarID, CliëntID, 'Direct'
FROM Cliënten
WHERE BehandelaarID IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_gebruikers_afdeling ON Gebruikers(AfdelingID);
CREATE INDEX IF NOT EXISTS idx_gebruikers_azuread ON Gebruikers(AzureADObjectID);
CREATE INDEX IF NOT EXISTS idx_cliënten_afdeling ON Cliënten(AfdelingID);
CREATE INDEX IF NOT EXISTS idx_cliënten_behandelaar ON Cliënten(BehandelaarID);
CREATE INDEX IF NOT EXISTS idx_toegangsrechten_gebruiker ON Toegangsrechten(GebruikerID);
CREATE INDEX IF NOT EXISTS idx_toegangsrechten_cliënt ON Toegangsrechten(CliëntID);
CREATE INDEX IF NOT EXISTS idx_toegangsrechten_afdeling ON Toegangsrechten(AfdelingID);
"""

