# Releasing

Maintainer notes for shipping `superbooks` to PyPI. Nothing here is needed to
*use* the SDK.

## How publishing is wired

PyPI trusted publishing (OIDC) — there is no API token stored in this repo, in
GitHub secrets, or anywhere else. PyPI is configured to trust:

| Setting     | Value                            |
| ----------- | -------------------------------- |
| Repository  | `DevinoSolutions/superbooks-python` |
| Workflow    | `release.yml`                    |
| Environment | `(Any)` — see below              |

**Renaming `.github/workflows/release.yml` breaks publishing.** The filename is
part of what PyPI verifies. If it ever has to change, update the PyPI trusted
publisher config first.

## One-time setup (repo admin)

### 1. Create the `pypi` GitHub environment — required

`release.yml`'s publish job declares `environment: pypi`. Until that environment
exists, the publish job cannot run.

Settings → Environments → **New environment** → name it `pypi`, then:

- Enable **Required reviewers** and add the people allowed to approve a release.
  This is the point of the environment: it puts a human between "someone pushed
  a tag" and "a package went to PyPI", so a compromised or mistaken tag push
  cannot ship on its own.
- Optionally restrict **Deployment branches and tags** to the `v*` tag pattern.

### 2. Optionally pin the environment in PyPI — recommended, not required

The PyPI trusted-publisher config currently has Environment set to `(Any)`,
which works as-is. Setting it to `pypi` on PyPI adds a second, independent
check: PyPI itself would then reject an OIDC token minted from any other
environment, so removing the GitHub environment would break publishing loudly
rather than silently dropping the human approval step.

Do this on PyPI → the `superbooks` project → Publishing → edit the trusted
publisher → Environment name: `pypi`. Safe to do at any time; `(Any)` stays
compatible until you change it.

## Cutting a release

1. Update `version` in `pyproject.toml` and `__version__` in
   `src/superbooks/_version.py` — they must match.
2. Move the `CHANGELOG.md` `[Unreleased]` entries under a new version heading
   with the date, and update the link refs at the bottom.
3. Land those on `main` and confirm CI is green.
4. Tag and push:

   ```bash
   git tag v0.1.0
   git push origin v0.1.0
   ```

5. The `Release` workflow runs `test` and `build` in parallel. `build` refuses
   to proceed unless the tag matches the version in `pyproject.toml`.
6. Approve the `pypi` environment when GitHub prompts. The `publish` job then
   uploads to PyPI.

Tags are the only trigger — there is no `workflow_dispatch`. A manual run would
carry `github.ref = refs/heads/main`, which has no tag for the version guard to
check, so allowing one would mean publishing whatever version `pyproject.toml`
happened to hold. The guard also fails closed on any non-tag ref, so re-adding
a manual trigger later cannot silently reopen that hole.

## The leak scan

`scripts/leak_scan.py` fails the build if implementation vocabulary reaches
published output. It runs in CI after the build, and again in `release.yml`
before the upload step — the release run is the one that matters, because it
scans the exact artifacts headed for PyPI and a published version cannot be
unpublished.

It scans **built artifacts as well as source**. Python compiles docstrings into
`.pyc` bytecode and the wheel copies source verbatim, so a clean `grep` over
`src/` does not by itself mean a clean wheel.

The source pass walks **every git-tracked file**, not just `src/`. Publishing
this repository exposes the tests, both workflows, `pyproject.toml`, and the
scripts as surely as it exposes the package.

It also warns when `dist/` is older than the sources it was built from, since a
scan of stale artifacts reports on something other than the current tree.
**Rebuild before trusting a local scan.**

Patterns are generic classes — SQL and full-text-search vocabulary, storage
vendor names, license identifiers, local filesystem shapes, credential shapes.
Each carries an invented sample, and `tests/test_leak_scan.py` derives its
coverage from the pattern list itself, so a pattern cannot be added without
demonstrating that it detects something, and one that stops matching is caught
rather than passing forever.

If it fires on something legitimate, **tighten the pattern or reword the text;
do not delete the pattern** — and prefer rewording over excluding a whole file,
so the file stays covered. Two patterns carry boundary conditions explained in
comments beside them: the index-type check stays word-bounded and
case-sensitive because those letters appear inside ordinary words, and the
query-syntax check requires a word character before the colon and rejects a
doubled asterisk after it, because the naive form matches markdown bold labels.

## If a release goes wrong

PyPI does not allow re-uploading a version, even after deleting it. Bump to the
next patch version and release again — do not try to reuse the number.
