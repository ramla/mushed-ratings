# Pylint report

```
************* Module query
query.py:5:0: R0903: Too few public methods (1/2) (too-few-public-methods)
query.py:286:0: R0912: Too many branches (17/12) (too-many-branches)

------------------------------------------------------------------
Your code has been rated at 9.97/10 (previous run: 9.95/10, +0.02)
```

I enabled pylint in VSCode early on during this project due to interest and while my initial reaction to some of the messages was mild irritation each of the recommended practices did make sense and I embraced running pylint live in the IDE.

My .pylintrc already has C0114, C0115, C0116 disabled as I deemed module, class and function docstrings not necessary for this project.

R0903 'too few public methods' is interesting, maybe I could just as well pass the search query data around as just a dictionary if I am not going to implement more methods, but the advanced search feature is pretty much incomplete as is and more methods could follow.

For the R0912 'too many branches' in the advanced search sql query assembly function probably the branching and especially concats could be reduced but for now it shall be left as is.

There is also a message that appears live but not in the generated report on app.py:9:0:
```
third party import "settings" should be placed before first party imports "db", "config", "crud", "query" Pylint(C0411:wrong-import-order)
```
This might be due to me naming the file with constants as settings.py, a name which could be used by another module.