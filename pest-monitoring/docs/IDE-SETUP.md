# IDE set-up and daily Git routine (Part 2, Task 1)

## 1. Map the IDE to the Azure Repos repository

### VS Code (recommended: the team uses VS Code)

1. Install **Git**, **Python 3.12** and **Node 22 LTS**.
2. In Azure DevOps open *Repos → Files → Clone → Clone in VS Code*, or run:
   ```bash
   git clone https://dev.azure.com/FallingCats/Pest%20Monitoring/_git/Pest%20Monitoring
   ```
3. Sign in with your MTU account when Git Credential Manager asks.
4. Open the folder in VS Code and accept the **recommended extensions** (`.vscode/extensions.json`): Python, Pylance, Ruff, Angular Language Service, ESLint, Azure Pipelines.
5. Select the interpreter `backend/.venv` (*Python: Select Interpreter*). The Testing panel then finds the pytest tests.

### PyCharm (alternative)

*File → New → Project from Version Control*, paste the clone URL, sign in. Set the project interpreter to `backend/.venv` and the test runner to **pytest** (*Settings → Tools → Python Integrated Tools*).

## 2. Daily routine: pull, branch, commit, push, pull request

```bash
# start of the day: get the latest integration branch
git switch develop
git pull

# start a work item (e.g. Task 25 on Azure Boards)
git switch -c feature/AB25-report-form

# work, then commit often; AB#25 links the commit to the work item
git add .
git commit -m "AB#25 Add details step to the report form"

# share your branch
git push -u origin feature/AB25-report-form
```

Then in Azure DevOps: *Repos → Pull requests → New pull request* from your branch into `develop`.

* Add a reviewer, link the work item (it's added automatically from `AB#25`) and wait for the build to pass.
* Fix review comments with new commits on the same branch. The pull request updates itself.
* After approval: **Complete** with *squash merge* and *delete source branch*.

Keep your branch up to date while you work:

```bash
git switch develop && git pull
git switch feature/AB25-report-form
git merge develop          # resolve any conflicts, run the tests, commit
```

## 3. Switching between branches

```bash
git status                 # commit or stash changes first
git stash                  # park unfinished work
git switch develop
git switch feature/AB25-report-form
git stash pop              # bring the parked work back
```

## 4. Commit message rules

* Start with the work item: `AB#25 Add details step`
* Present tense, short first line (max ~70 characters)
* One logical change per commit
