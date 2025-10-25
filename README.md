# MushEd, a Mushroom Edibility Ratings App

* Create your sampler account and log in
* Report a sampled mushroom's identifiers or modify a previous report
* Make a secondary report of experienced symptoms related to a mushroom you sampled
* Select predetermined culinary category tags to a reported mushroom
* View sample reports from yourself and other users
* Search for sample reports from yourself and other users by their identifiers
* View profile pages of other samplers and their reports with statistics
* Comment on reports, delete comments

Primary data entity is the sampling report and the secondary data entity are the symptom reports

## Sovelluksen asennus

Asenna `flask`-kirjasto:

```
$ pip install flask
```

Luo tietokannan taulut ja lisää alkutiedot:

```
$ sqlite3 database.db < schema.sql
$ sqlite3 database.db < init.sql
```

Voit käynnistää sovelluksen näin:

```
$ flask run
```