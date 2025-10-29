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

## How to install

Install `flask`-library:

```
$ pip install flask
```

Initialise database:

```
$ sqlite3 database.db < schema.sql
$ sqlite3 database.db < init.sql
```

Create secret key:
```
python3 make_secret.py
```

Start server:

```
$ flask run
```

You should now be able to view app at https://localhost:5000/