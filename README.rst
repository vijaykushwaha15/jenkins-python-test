===================
jenkins-python-test
===================

Python project to test Jenkins and SonarQube.

SonarQube Project Setup
-----------------------
1. Open ``http://localhost:9000``.
2. Login with user: ``admin``, password: ``admin``.
3. Click ``Create new project`` link.
4. Set ``Project key`` to ``jenkins-python-test``.
5. Click ``Set Up`` button.
6. Set token name to ``jenkins-token``.
7. Click ``Generate`` button.
8. Copy token and store somewhere secure.
9. Click ``Continue`` button.
10. Click ``Other`` button.
11. Click ``Linux`` button.
12. Copy ``sonar-scanner`` code and store somewhere secure.

Jenkins Project Setup
---------------------
1. Click ``create new jobs`` link.
2. Fill in ``Enter an item name`` with ``jenkins-python-test``.
3. Click ``Freesytle project``.
4. Click ``OK`` button.
5. Click ``Git`` for Source Code Management.
6. Enter ``https://github.com/Algoritics/jenkins-python-test.git``.
7. Click ``Build`` -> ``Add build step`` button.
8. Select ``Execute shell``.
9. Enter ``make coverage`` in ``Command`` textbox.
10. Click ``Build`` -> ``Add build step`` button.
11. Select ``Execute SonarQube Scanner``.
12. Enter ``sonar-project.properties`` in ``Path to project properties`` textbox.
13. Enter project key and login in ``Analysis properties`` textbox. Example:

``
sonar.projectKey=jenkins-python-test
sonar.login=ba7a9af4518eea0acb77a6b7fc19ea01a13d2f7e
``

14. Click ``Save`` button.
15. Click ``Build now`` button to verify working.

Free software: MIT license
Documentation: https://jenkins-python-test.readthedocs.io.
