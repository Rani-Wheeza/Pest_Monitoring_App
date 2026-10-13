The Pest Monitoring App is a crowdsourced application designed to help users identify, report and monitor rodent and avian pest activity. The primary focus is on rodent pests due to their potential impact on infrastructure, food storage and health. Users can submit pest sightings containing geographical information, timestamps and species classification, with optional image, video and audio evidence.

The collected information will be processed and stored to provide users with an interactive representation of pest activity. Azure Maps will be used to generate heat maps that can be filtered according to pest species and broader classifications. The system will also support notifications when pest activity reaches potentially dangerous levels.

The project will use Microsoft Azure and Azure DevOps as the primary cloud and DevOps environment. The proposed architecture includes Azure App Service, Azure Kubernetes Service, Azure SQL Database, Azure Maps and Azure Notification Hubs. Docker containers and Azure Container Registry will support backend deployment.

**Project Objectives**
The project aims to:

Allow users to submit pest sightings.
Capture relevant information about sightings.
Validate and securely process submitted data.
Store sighting and user data.
Display pest activity geographically.
Generate interactive heat maps.
Allow pest activity to be filtered by species/classification.
Alert users when pest activity reaches significant levels.
Develop the application using an Agile approach.
Use Azure DevOps to manage development, work items and project collaboration.

**Proposed System**

Users

Azure App Service

Azure Kubernetes Service

Azure SQL Database

Azure Maps

Heat Maps

Notification Hubs

Alerts

The project is expected to result in a functioning, containerised application capable of scaling with user activity, providing interactive pest information through maps and alerts.

## Version Control Workflow

Git and GitHub are used to manage the source code and maintain a history of changes to the Pest Monitoring application.

- **Main branch:** Holds the primary project code.
- **Feature and documentation branches:** Allow changes to be developed separately from the main branch.
- **Commits:** Record changes with meaningful messages.
- **Remote synchronisation:** Fetch and pull remote changes before pushing local changes when necessary.
- **Pull requests:** Support code review and controlled integration of changes.
- **Continuous integration:** Azure Pipelines automatically runs code-quality checks, tests, coverage reporting and build verification.

Changes should be tested before integration. Where team workflow and repository permissions allow, pull requests should be reviewed before being merged into `main`.
