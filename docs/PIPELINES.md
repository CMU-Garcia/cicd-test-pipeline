# Pipeline setup

The two pipeline files implement the same release process and call the same Python
scripts. You can teach either platform independently or compare their run histories.
They target GitHub.com and Azure DevOps Services with hosted Ubuntu 24.04 agents.

## GitHub Actions

1. Create or fork a GitHub repository containing this project. Keep its default branch
   named `main`, or update the branch names in both pipeline files.
2. Push the files, including `.github/workflows/ci-cd.yml`. Ensure Actions is enabled
   for the repository. Organization policy must permit the referenced official actions.
3. Open **Actions → Wheel CI/CD** and inspect the first run. You can also use
   **Run workflow** for a manual run once the workflow is on the default branch.
4. Open **Settings → Environments**, create `staging`, and optionally restrict
   deployment branches to `main`. The workflow can create an unprotected environment
   on its first run, but explicit setup makes its policy visible to learners.
5. For the approval lab, add required reviewers to `staging` if your repository and
   plan support them. Without reviewers, the staging sandbox deploys automatically.
6. After a successful run, download **wheel-release** from its artifact list. Unzip it
   into a directory and pass that directory to `scripts/release.py deploy`.

The workflow checks every pushed branch and PRs targeting `main`. A branch with an
open PR can therefore produce both a push run and a PR run. Only a main-branch push
or manual main-branch run reaches staging. All deployment artifacts come from that
same run, not from a mutable “latest release” lookup.

The workflow token has `contents: read`; no cloud secrets are needed. Official actions
are pinned to commit SHAs with version comments. Updating an action means verifying
its new release and replacing both its SHA and comment. The starting actions use
Node 24; if you later use your own runners, follow the actions' runner prerequisites.

Make CI a merge requirement in **Settings → Rules → Rulesets** (or the available
branch protection settings). Require the **Test and package** status check on `main`;
GitHub lists it after its first run. Requiring this check is a repository policy;
putting tests in YAML alone does not block a merge.

## Azure DevOps

1. Create an Azure DevOps project. Connect this GitHub repository, or import the
   project into Azure Repos. Your account needs pipeline creation permissions and
   access to a hosted agent pool with available parallel-job capacity.
2. Open **Pipelines → Environments → New environment**. Create `staging` with resource
   type **None**. This is a logical approval/deployment record; it does not create a server.
   In its pipeline permissions, authorize the pipeline you create below.
3. Open **Pipelines → New pipeline**, select the repository source, and choose
   **Existing Azure Pipelines YAML file → /azure-pipelines.yml**. Save and run.
4. For GitHub repositories, authorize the GitHub connection during setup. YAML `pr`
   triggers validate PRs targeting `main`.
5. For Azure Repos, open **Repos → Branches → main → Branch policies → Build
   validation**. Add this pipeline, choose an automatic trigger, and make the policy
   required. Azure Repos does **not** use YAML `pr` triggers; this policy is necessary.
6. Inspect the **Tests**, **Code Coverage**, stages, and artifacts in the run summary.
   Download **wheel-release** to install the package locally.
7. For the approval lab, open **staging → Approvals and checks**, add an approval,
   and select a reviewer. Approval rules belong to the environment configuration,
   not to this repository's YAML.

All pushed branches run CI. Successful main-branch runs deploy to the staging
sandbox; PR builds do not. `PublishTestResults` saves test results even when pytest
fails. `UseDotNet` supplies the prerequisite runtime for Azure's coverage publishing
task; the application itself remains Python.

The default pipeline uses Pipeline Artifacts, which are intended here for Azure
DevOps Services. Azure DevOps Server installations need compatible artifact tasks
and agent setup instead of assuming this hosted configuration will work unchanged.

## Compare the concepts

| Concept | GitHub Actions | Azure DevOps |
| --- | --- | --- |
| Pipeline definition | `.github/workflows/ci-cd.yml` | `azure-pipelines.yml` |
| Start a run | `on` events | `trigger`, `pr`, or UI run |
| Execution host | `runs-on` | `pool.vmImage` |
| Dependency between phases | `needs: ci` | `dependsOn: CI` |
| Install Python | `actions/setup-python` | `UsePythonVersion@0` |
| Save release artifact | `actions/upload-artifact` | `PublishPipelineArtifact@1` |
| Retrieve same-run artifact | `actions/download-artifact` | `download: current` |
| Staging deployment | Job with `environment: staging` | Deployment job with `environment: staging` |
| Approval gate | Environment required reviewers | Environment approvals and checks |
| Prevent merging failing changes | Required status check | Required build validation policy |

## What deployment means in this starter

The pipeline installs the wheel into a **fresh virtual environment on its hosted
agent** and starts it only for smoke testing. It records a successful staging receipt
with the same version, commit, and checksum as the build manifest. No durable host
is provisioned and no public URL is created. Optional approvals demonstrate the
release decision even though this target is a temporary sandbox.

For a durable deployment, add a job that downloads the same wheel and installs it
on an actual host, or builds the supplied Dockerfile and deploys the resulting image.
That extension needs a chosen host, credentials or workload identity, and a way to
start/restart the service. Keep the wheel as the promoted artifact; avoid rebuilding
application source in each environment. Adding PyPI publication is a separate exercise,
not a requirement for installing or deploying a wheel.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| GitHub workflow does not appear | Workflow committed to the repository; Actions enabled; organization policy permits actions |
| Azure run stays queued | Hosted parallel-job capacity and pool permissions; some organizations must request or purchase capacity |
| Azure PR does not trigger | Azure Repos needs a build validation branch policy; GitHub needs an authorized connection |
| Azure staging environment is missing or unauthorized | Pre-create `staging` and authorize this pipeline in its environment permissions |
| Staging is skipped | Expected for branches and PRs; it requires a successful main-branch build |
| Staging is waiting | Inspect configured environment approvals and checks |
| A format check fails | Run your development Python with `-m ruff format .`, inspect the changes, and commit them |
| A target already exists | Choose a new deployment directory; a previous attempt may have left it behind |
| Wheel checksum fails | Restore the original artifact and manifest from the same run; do not conceal the mismatch by editing the checksum |
| No reports were published | An earlier installation or lint step may have failed before tests could generate reports |
| Docker cannot connect | Start a Docker engine with Linux containers enabled |

## Official references

- [GitHub: building and testing Python](https://docs.github.com/en/actions/tutorials/build-and-test-code/python)
- [GitHub: managing environments](https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments)
- [GitHub: workflow artifacts](https://docs.github.com/en/actions/concepts/workflows-and-actions/workflow-artifacts)
- [Azure: Python pipelines](https://learn.microsoft.com/en-us/azure/devops/pipelines/ecosystems/python?view=azure-devops)
- [Azure: PR triggers and Azure Repos branch policies](https://learn.microsoft.com/en-us/azure/devops/pipelines/yaml-schema/pr?view=azure-pipelines)
- [Azure: coverage publisher prerequisites](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/publish-code-coverage-results-v2?view=azure-pipelines)
- [Python Packaging: packaging projects](https://packaging.python.org/en/latest/tutorials/packaging-projects/)
