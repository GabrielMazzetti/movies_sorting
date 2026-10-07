CREATE TABLE filmes (
    tconst TEXT PRIMARY KEY,
    titleType TEXT,
    primaryTitle TEXT,
    originalTitle TEXT,
    startYear INTEGER,
    genres TEXT
);

CREATE TABLE ratings (
    tconst TEXT PRIMARY KEY REFERENCES filmes(tconst),
    averageRating REAL,
    numVotes INTEGER
);

CREATE TABLE new_cache_paises (
    tconst TEXT REFERENCES filmes(tconst),
    country TEXT,
    countryLabel TEXT,
    fonte TEXT,
    PRIMARY KEY (tconst, country)
);