# Sprint 1 backlog and work-item links (Part 2, Task 2)

The brief requires every Sprint 1 work item (tasks **and tests**) to be linked to code in the repository, and the description in Azure DevOps to match the code.

## 1. Import the work items

`docs/azure-boards-sprint1.csv` holds **7 features, 12 user stories and 48 tasks** (9 of them test tasks). They are placed under the four Part 2 epics already on the board (IDs 18–21). The four epic rows keep their current titles and sprint, so the import doesn't change them.

*Boards → Work items → Import work items → Choose file* → check the preview → **Import**.

After importing:

1. Set **Assigned To** on each task. Split them so each member owns frontend, backend and test work.
2. Check every item has *Iteration = Pest Monitoring\Sprint 1*.
3. Delete or merge any items the group doesn't want.

## 2. Link each task to its code

Use any of these (one is enough, two is better):

* **Commit message:** `git commit -m "AB#123 Add details step"` (needs *Commit mention linking*, see BRANCHING.md).
* **Branch name:** `feature/AB123-report-form`, then *Development → Create branch* on the work item.
* **Pull request:** linking the work item in the PR (automatic from `AB#`) adds it to the *Development* section.

## 3. Work items ↔ code ↔ tests

| Work item | Code | Tests |
|---|---|---|
| US-01 User authentication | `backend/domain/identity.py`, `backend/accounts/authentication.py`, `backend/accounts/models.py`, `backend/accounts/views.py` | `tests/domain/test_identity.py`, `tests/api/test_auth_api.py` |
| US-02 Submit pest report | `backend/domain/validation.py`, `backend/sightings/{models,repositories,services,serializers,views}.py`, `frontend/src/app/features/report/` | `tests/domain/test_validation.py`, `tests/api/test_sightings_api.py`, `report-sighting.spec.ts` |
| US-03 Attach a photo | `backend/domain/images.py`, `services.attach_photo`, `SightingPhotoView`, photo picker in `report-sighting.html` | `tests/domain/test_images.py`, photo tests in `test_sightings_api.py`, `report-rules.spec.ts` |
| Worker review | `services.review_sighting`, `SightingReviewView`, `AllSightingsView` | review tests in `test_sightings_api.py` |
| US-04 View pest map | `backend/domain/geo.py`, `services.map_features`, `MapView`, `frontend/src/app/features/map/`, `core/azure-maps.ts` | `tests/domain/test_geo.py`, `tests/api/test_map_api.py`, `pest-map.spec.ts` |
| US-05 Filter pest map | `MapQuerySerializer`, `repositories.map_rows`, map filter bar | filter tests in `test_map_api.py`, `api.service.spec.ts` |
| US-06 Receive pest alert | `backend/domain/alerts.py`, `backend/domain/notification_hub.py`, `backend/alerts/` | `tests/domain/test_alerts.py`, `test_notification_hub.py`, `tests/api/test_alerts_api.py`, `test_senders_and_seed.py` |
| Resident dashboard | `GET /api/sightings/mine/`, `frontend/src/app/features/my-reports/` | `my-reports.spec.ts`, `test_my_sightings_*` |
| Reference data | `backend/reference/` (`seed_reference_data` command) | `test_seed_command_is_repeatable`, `test_tag_and_district_lists` |
| Code quality (Task 3) | `backend/pyproject.toml`, `frontend/eslint.config.js` | Pipeline steps |
| CI pipeline (Task 4) | `azure-pipelines.yml` | Pipeline runs |

## 4. Keep Part 1 work items in line with the code

The Part 1 wiki and work items were written before the code. Check these:

* **Video and audio:** Task 1 (1.1, 1.6, 1.14), Task 8.2 and Task 9 (US-03, "Advanced media") still mention them. The code and Tasks 5–7 support images only.
* **Roles:** the code uses `User`, `Worker`, `PestControlExpert`, `Surveyor`, `Admin` (Task 5). Task 4.3 lists only User and Administrator.
* **Monitoring (Task 3.7):** the code sends telemetry to Application Insights when `APPLICATIONINSIGHTS_CONNECTION_STRING` is set.
* **Alert threshold:** the default is 10 sightings in 30 days (`ALERT_THRESHOLD`). The group still needs to agree the real value (Task 9.8).

## 5. Left for Sprint 2

* MSAL Angular sign-in in the frontend (the backend already checks Entra ID tokens)
* Alerts screen and worker screens (Reports list, review, analytics) in Angular
* Ecological surveys, pest-control experts, contracts and chat (Task 5 "Extended" tables)
* Deployment to Azure: ACR push, AKS manifests, CronJob for `check_pest_levels`, Key Vault
