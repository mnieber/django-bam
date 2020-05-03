# django-bam

Adds a "backup after migrate" command to solve "db vs migrations" incompatibilities during development

## Introduction

The "manage.py bam" command creates a backup of the db and stores it under the hash that identifies the set of migrations for the current branch.

- python manage.py bam: backups up the db with a hash based on the set of current migrations
- python manage.py bam --restore: restores backup of the db corresponding to the set of current migrations

This allows you:

- to try new migrations and restore the previous db if you throw these migrations away.
- to switch the database when you switch branches (each branch can have its own compatible database).
