Git-Collector
==============

The Git data collector service allow save data from git and use properly for other apps.

This repository is the base to support SmartDeveloperHub SCM Collectors.

**PyCharm Usage**

1. Import project at PyCharm
2. Install dependencies or execute `python setup.py develop`
3. Configure settings.py
4. Run project

**API Usage**

*Content-type: application/json is required*

==============

|HTTP Method|Path|Status|
|:---------|:----------|:----------|
|*|/api/*|401|

If GC_USE_PASSWORD (settings.py), put X-GC-PWD header at requests *

**Response (401):**

```{"Error": "Password is not valid."}```

==============

|HTTP Method|Path|Status|
|:---------|:----------|:----------|
|GET|/|200|
|GET|/api|200|

**Response (200):**

```{"Version": "GC_VERSION", "Name": "Git Collector", "Password": GC_USE_PASSWORD}```

Where GC_VERSION is API version and GC_USE_PASSWORD is True or False

==============

|HTTP Method|Path|Status|
|:---------|:----------|:----------|
|GET|/api/repositories|200|
|POST|/api/repositories|201 or 422|

**POST Request:**

|Fields|Value|Required|
|:---------|:----------|:----------:|
|url|repository url + .git|YES|
|user|valid git username|NO|
|password|any string|NO|
|state|'active' or 'nonactive'|NO|

**Response (200):**

```[{"url": "...", "state": "...", "id": "repository_id", "user": "..."}, ...]```

Note: Repository password is not returned at any case by security.

**Response (201):**

```{"URL": "...", "Status": "Added", "ID": "repository_id"}```

**Response (422):**

```{"Error": "Repository exists. Please update or remove it."}```

```{"Error": "JSON at request body is bad format."}```

==============

|HTTP Method|Path|Status|
|:---------|:----------|:----------|
|GET|/api/repositories/repository_id|200 or 404|
|PUT|/api/repositories/repository_id|200 or 422 or 404|

**PUT Request:**

|Fields|Value|
|:---------|:----------|
|url|repository url + .git|
|user|valid git username|
|password|any string|

**Response (200):**

```{"url": "...", "state": "...", "id": "repository_id", "user": "..."}```

Note: Repository password is not returned by security.

```{"ID": "repository_id", "Status": "Updated"}```

**Response (404):**

```{"Error": "Repository does not exist."}```

**Response (422):**

```{"Error": "JSON at request body is bad format."}```

==============

|HTTP Method|Path|Status|
|:---------|:----------|:----------|
|POST|/api/repositories/repository_id/state|200 or 404 or 422|

**POST Request:**

|Fields|Value|
|:---------|:----------|
|state|'active' or 'nonactive'|

**Response (200):**

```{"ID": "repository_id", "Status": "Activated"}```

```{"ID": "repository_id", "Status": "Deactivated"}```

**Response (404):**

```{"Error": "Repository does not exist."}```

**Response (422):**

```{"Error": "JSON at request body is bad format."}```

==============

|HTTP Method|Path|Status|
|:---------|:----------|:----------|
|GET|/api/repositories/repository_id/branches|200 or 404|
|GET|/api/repositories/repository_id/commits|200 or 404|

**Response (200):**

```["branch_id", ...]```

```["commit_id", ...]```

**Response (404):**

```{"Error": "Repository does not exist."}```

==============

|HTTP Method|Path|Status|
|:---------|:----------|:----------|
|GET|/api/repositories/repository_id/branches/branch_id|200 or 404|

**Response (200):**

```{"name": "...", "contributors": ["contributor_id", ...]}```

**Response (404):**

```{"Error": "Repository does not exist."}```

```{"Error": "Branch does not exist."}```

==============

|HTTP Method|Path|Status|
|:---------|:----------|:----------|
|GET|/api/repositories/repository_id/commits/commit_id|200 or 404|

**Response (200):**

```{"sha": "...", "author": "contributor_id", "title": "...", "time": long, "email": "...", "lines_removed": int, "lines_added": int, "files_changed": int}```

**Response (404):**

```{"Error": "Repository does not exist."}```

```{"Error": "Commit does not exist."}```

==============

|HTTP Method|Path|Status|
|:---------|:----------|:----------|
|GET|/api/repositories/repository_id/branches/branch_id/commits|200 or 404|

**Response (200):**

```["commit_id", ...]```

**Response (404):**

```{"Error": "Repository does not exist."}```

```{"Error": "Branch does not exist."}```

==============

Git-Collector is distributed under the Apache License, version 2.0.
