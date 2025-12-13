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

On the home page you can read some instructions and tips as well as some inspirational user stats. It also currently functions as the login page. When not logged in, it contains the link to sign up. When logged in, you can click your user name to view your stats.

The menu bar has links to the home page, the sample report form, listing of all reports and the searches, plus the logout button.

After reporting a sample the report view opens up. At the bottom of it you have links to submit a symptom report or edit or delete the sample report. Editing or deleting a sample report appropriately assigns the report to a possible another user who has reported their symptoms after eating the mushroom with same identifiers and deletes or moves the current user's sample reports.

The quick search is a keyword search from relevant text fields while the advanced search is more detailed, but at the time of writing unpolished.

Other users' user pages can be accessed by finding a sample report submitted by them.