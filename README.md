<<<<<<< HEAD
# donation-tracker [![Build Status](https://travis-ci.org/TipoftheHats/donation-tracker.svg?branch=master)](https://travis-ci.org/TipoftheHats/donation-tracker)

TotH's fork of the GDQ donation tracker. See [donation-tracker-toplevel](https://github.com/TipoftheHats/donation-tracker-toplevel) for setup instructions.
=======
See setup instructions in the top level repository: https://github.com/GamesDoneQuick/donation-tracker-toplevel

## Contributing

### `pre-commit`

This project uses [`pre-commit`](https://pre-commit.com/) to run linters and other checks before every commit.

`pre-commit` has been added as part of `requirements.txt`, so new installs should automatically get it, but if not, you can get it manually with pip:

```
pip install pre-commit
```

Then, run `pre-commit install` in this repository to add the git hooks, and now every time you `git commit` the checks will run!

_Note:_ You _can_ bypass these checks by adding `--no-verify` when you commit, though this is highly discouraged in most cases. In the future, CI tests may fail if any of these checks are not satisfied.
>>>>>>> 817791ba952c233d68946fbae69dd150fefcd03c
