<!--
Thank you for contributing! Please make sure your PR targets the `dev` branch (not `main`)
and covers ONE concern only. See CONTRIBUTING.md for the full workflow.
-->

## What

<!-- One paragraph: what does this PR do? -->

## Why

<!-- Link the related issue. Use "Closes #<id>" so the issue is closed automatically on merge. -->

Closes #

## Type of change

<!-- Check all that apply. -->

- [ ] 🐛 Bug fix
- [ ] ✨ New feature
- [ ] 🧩 Plugin (new or updated)
- [ ] 📖 Documentation
- [ ] ♻️ Refactor (no behaviour change)
- [ ] 🔧 Tooling / CI / dependencies

## Breaking change

<!--
Does this PR break the configuration format, the CLI, or the plugin interfaces?
If yes, describe the impact and the migration path, and mark the commit with `!`
(e.g. `feat(config)!: ...`). Keep "None" otherwise.
-->

None

## How to test

<!--
Steps a reviewer can follow to verify the change.

⚠️ Plugins and the Excel/PDF reporting adapters are exempt from unit tests, so review
is the ONLY validation they get: if your PR touches them, include evidence of a manual
run (`check` / `sync` / `audit` output, or a screenshot of the generated report),
with credentials and internal hostnames redacted.
-->

1.

## Release (optional)

<!--
If you believe this change warrants a release, say so here and suggest the version
bump (patch / minor / major). The final decision belongs to the maintainers.
-->

## Checklist

- [ ] The PR targets the `dev` branch and covers a single concern.
- [ ] The branch follows the naming convention (`<type>/<issue-ref>/<short-description>`).
- [ ] Commits follow [Conventional Commits](https://www.conventionalcommits.org/).
- [ ] Core changes ship with unit tests and coverage stays at **100 %** (see the exemptions in CONTRIBUTING.md).
- [ ] Public classes/methods/functions have Google-style docstrings.
- [ ] Documentation is updated if behaviour or configuration changed.
- [ ] No new runtime dependency, or its addition is justified in the description.
- [ ] No credential, token, or internal hostname in code, fixtures, logs, or screenshots.
- [ ] All CI checks are green.
