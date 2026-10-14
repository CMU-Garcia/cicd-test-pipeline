# Instructor guide

A suggested 75–90 minute session for learners comfortable editing a small program
and committing changes. They do not need prior pipeline experience.

## Before the session

- Prepare a GitHub repository or Azure DevOps project with these files on `main`.
- Run the chosen pipeline successfully once and check available hosted-runner capacity.
- Create and authorize `staging`; decide whether to enable approvals during the session.
- Configure a required merge check so the failed-PR example demonstrates enforcement.
- Have learners install Python 3.13 and Git. Docker is optional for the core labs.
- Give each learner a fork, their own repository, or a separate branch in a shared
  repository. Shared main-branch runs can cancel older GitHub runs because of concurrency.
- Keep a successful release artifact available for the installation and rollback labs.

## Suggested session

| Time | Activity | Checkpoint |
| --- | --- | --- |
| 0–10 min | Run the app, inspect the business rule, discuss manual release risks | Learners can query the API |
| 10–20 min | Read one successful pipeline and its wheel artifact | Learners identify checks, packaging, artifact storage, and deployment |
| 20–40 min | Shipping-boundary regression lab | Learners find the failing assertion and repair the PR |
| 40–55 min | Missing-resource lab | Learners explain why the source test passes but the wheel fails |
| 55–70 min | Approval and same-wheel staging lab | Learners compare manifest and deployment receipt |
| 70–85 min | Two-release rollback lab | Learners run a previous release without rebuilding |
| Final 5 min | Choose an extension and discuss limitations | Learners distinguish temporary staging from durable hosting |

For a shorter session, teach the successful run and regression labs first. The feature
lab is useful as a follow-up assignment. Pick one CI platform for hands-on work and
use the comparison table to map the concepts to the other.

## Discussion prompts

- Which manual mistakes did this pipeline remove? Which ones can still happen?
- Does a green test suite prove the wheel includes every required file?
- What identifies the code we deployed: the branch, version, commit, or wheel checksum?
- Why download the existing wheel instead of rebuilding it in staging?
- What happens if tests fail, approvals are rejected, or a smoke test fails?
- What prevents merging bad changes, and how is that different from blocking deployment?
- Why does a hosted agent's virtual environment disappear after the job?
- What would a persistent deployment need: a host, service lifecycle, credentials,
  health monitoring, and a rollback plan?

## Completion criteria

A learner can introduce and fix a failing PR, locate test reports, explain what is
inside a wheel, install a downloaded artifact, compare its release identity with the
staging receipt, and run an earlier release. They can distinguish CI, continuous
delivery, and continuous deployment, and name a practical benefit of each.

The app has no database, production HTTP stack, secret store, package registry,
or persistent cloud target. Those are extensions once learners understand the flow.
The development requirements pin direct tools; dependency locking and supply-chain
provenance are further lessons rather than claims this starter already solves.
