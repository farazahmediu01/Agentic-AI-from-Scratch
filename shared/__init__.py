"""
Shared infrastructure for every chapter of the curriculum.

Nothing in here teaches an agent concept. This package exists only to hold the
plumbing that would otherwise be copy-pasted into every chapter's `with_sdk/`
folder — chiefly the model factory in `shared.models`.

Rule of thumb for what belongs here: if a student would learn something by
writing it themselves, it does NOT go in `shared/`. It goes in the chapter.
"""
