# MushEd, a Mushroom Edibility Ratings App

* Create your sampler account and log in
* Report a sampled mushroom's identifiers, modify a previous report or delete it
* Make a secondary report of experienced symptoms related to a mushroom you sampled
* Select predetermined category and identifier tags to a reported mushroom
* View sample reports from yourself and other users
* Search for sample reports from yourself and other users by their identifiers
* View profile pages of other samplers and their reports with statistics

Primary data entity is the sampling report and the secondary data entity are the symptom reports

## How to install

Install `flask`-library:

```
$ pip install flask
```

Create secret key:
```
python3 make_secret.py
```

Start server:

```
$ flask run
```

You should now be able to view the app at https://localhost:5000/