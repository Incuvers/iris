# Continuous Integration and Deployment Pipeline
Updated: 2020-09

## Navigation
1. [Lessons Learned](#lesssons-learned)
2. [Incuvers CI/CD Phases](#pipeline-phases)
3. [Deployment Cycle](#software-deployment-cycle)
4. [Future Plans](#future-plans)

## Lesssons Learned
Incuvers has come a long way in a short span with regards to testing and deploying software. At the time of shipping our first IRIS system in June 2020, none of the engineering team had any devops experience. As a result we greatly underestimated the time and resources we required to successfully deploy our system the way we had originally intended.

Through an unprecedented number of workarounds we managed to deploy a very complex system through the use of a `.bashrc` script, automated login services, and ssh credentials to a custom built github repository for software version control and updates.

While the deployment succeeded it cost the team alot of time in maintaining the unit for the client. Furthermore it cost us a significant amount of stress due to the uncertainty involved since the client was situated in Australia. We quickly realized how important it is to have a full-scale CI/CD system in place to enforce quality control, scalability and insure our systems are easy to maintain in the future.

At the time of the beta IRIS unit, the RPi team had a single set of lackluster unittests providing approximately 55% code coverage and subscribed to single AWS CodeBuild service. Since then, we have added linting build jobs using `flake8` and `shellcheck` for our python and `bash` code respectively, python package building jobs, and significantly improved areas of our unittest suite to increase code coverage. And now we have designed a front-to-back automated deployment pipeline as an addon which will ensure our applications are built, maintained and deployed continously and keep us on track for deployment deadlines.

## Pipeline Phases
The server systems we use in our custom pipeline is defined by 3 distinct services. First AWS CodeBuild for our rapid feature development, second a custom self-hosted Github Action for building, installing, and deploying the `iris` snap to `edge` for integration testing. Next, we subscribe a production system to `edge` and hook onto the automatic update using the Snap Store. Finally, we deploy the snap to `stable` for global updates.

### Phase 1 Unit Testing - AWS CodeBuild
AWS is an expensive service but provides the team with fast build times for fast paced feature development. We use AWS for build processes that are quick and can be done in a standalone VM with minimal configuration. Our snap is configured to be deployed on `core20` however AWS CodeBuild servers only support Ubuntu 18.04 images at the time of writing. As a result we want to leverage this to seperate concerns of feature development and deployment. 18.04 source code should always be compatible with 20.04 code however this is not the case for deployment.

AWS CodeBuild is responsible for the following build jobs:
1. **Linting** - Code sanity check.
2. **Unittest Suite** - Execution of our entire unittest suite.
3. **Coverage** - Execution of our custom coverage tests.
4. **Documentation** - Execution of our `Sphinx` documentation build.
5. **Python package build and installation** - Building the `iris` python package and installing it locally.

### Phase 2 Integration Testing - Github Actions / snapd update
Phase 2 is divided into 2 sections.

#### Phase 2a Snap Build Server - Self-Hosted Github Actions
We use Github Actions to self define a build service as a webhook from a set of custom events. This buildspec is defined in the repository under `.github/workflows/iris.yml`. Everytime a specified event occurs (such as a PR change or PR merge etc...), the build server latches on the webhook from github and commences the build. This allows us to circumvent the stringent build requirments of the snap application by using a remote RPi build server. We can locally validate the snap build result by a set of rigourous integration tests aligning with our customers user stories.

Finally, after local installation is complete the buildspec will execute a publish to the `edge` channel.

#### Phase 2b Live Production Demo - snapd update
After the snap is built locally and tested, we want to be able to test the snap on a live production system. The system can also double as an interactive demo for any audience. The requirements for the production demo system are listed below:
1. OS is stable on `core20`
2. `iris` snap is installed and subscribed to the `edge` channel 
3. Platform is RPi 4 1 GB model
4. RPi 4 is powered by IRIS motherboard
5. Peripherals are connected to the IRIS motherboard and are active.

Upon publishing the new snap to the `edge` channel on the snap store the production demo will update the current snap automatically. The timing of the update may be unpredictable as a result of snap review by Canonical and internal `snapd` update timing. We have reason to believe the update will not be executed by same day so this must be considered during our planning.

### Phase 3 Deployment - Github Actions / snapd update
In Phase 3 we are deploying our snap to the `stable` channel for global production deployment. This will be performed by a Github Action instructed to latch onto a merge to our `master` branch in our repository (more details on this in the [next section](#software-deployment-cycle)). The action will simply be to publish the active snap on the `edge` channel to `stable`.

## Software Deployment Cycle

### Github Branches and Rules
Here we discuss the pertenant branches involved in our custom CI/CD pipeline for the Incuvers/monitor
repository.

#### `monitor:develop`
This branch uses AWS CodeBuild for fast-paced feature development. We do not want to 
concern ourself with deployment details at this stage as it would greatly slow our development cycle.
Once a feature sprint is completed for deployment we will tag and merge the codebase into the CI/CD
pipeline to begin the deployment cycle.

#### `monitor:snapcraft`
This branch uses Github Actions to host a 4 phase build pipeline from a standalone RPi server:
1. Build - builds the snap using codebase from develop
2. Dev Install - installs the built snap locally using `--devmode` to ensure successful daemon initialization
3. Edge Deploy - deploys the proposed snap to `edge` 
4. Edge Install - a production RPi with a production `core20` image subscribes to the `edge`
channel and installs the snap.

> **RULE**: `snapcraft` can only be updated by a pull request from `develop`

#### `monitor:master`
The `master` branch hosts the code which is continuously deployed to the snap store through the `stable` channel

> **RULE**: `master` can only be updated by a pull request from `snapcraft` once Phase 4 passes the required validation checks

### Example of Proposed Outcome
This example will outline the new CI architecture as a new feature undergoes development and passes through all 3 phases of our pipeline.

1. A new pull request is opened for some production feature to be merged into develop `develop <- rt21-some-feature`
2. AWS CodeBuild employs its 5 build jobs when the pull request is opened and updated.
3. Once the pull request has been completed, reviewed and passes AWS CodeBuild it is merged into `develop`
4. `snapcraft` can only be updated by a pull request from `develop` which triggers our self-hosted Github Action and starts the snap build on a remote RPi Server.
5. The snap will be installed locally on the remote RPi Server and deploy to `edge` on the RPi server.
6. Developers will validate the snap as a local installation.
7. Meanwhile a second production system will be subscribed to the `edge` channel and receive the update.
8. Developers will again perform a more rigourous set of user story validation and quality control checks on the production system
9. Once satisfied, `snapcraft` is merged into `master` and a new Github Action publishes the snap on the `edge` channel to `stable` for the global update.

## Future Plans
 - [ ] Replace standard RPi build server with a blade server Turing Pi so builds can leverage more compute cores making our build times significantly faster
 - [ ] Create an LQN (Layered Queueing Network) of build servers to allow for build parrellelism
 - [ ] Automate the QA/QC processes for integration testing of user stories.