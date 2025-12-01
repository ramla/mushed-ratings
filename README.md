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

## Usage

On the home page you can read some instructions and tips. It also currently functions as the login page. When not logged in, it also contains the link to sign up. When logged in, you can click your user name to view your stats.

The menu bar has links to the home page, the sample report form, listing of all reports and the search, plus the logout button.

After reporting a sample report view opens up. At the bottom of it you have links to submit the symptom report or edit or delete the sample report. Currently editing the sample report does not (re)move symptom reports added by other users who identified and sampled the original submission.

Other users' user pages can be accessed by finding a sample report submitted by them.