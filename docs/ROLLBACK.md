# Rollback

## Before publication

No external rollback is necessary because this work does not push or upload. Restore the verified sibling backup
`release_1.0.10_backup_before_modelscope_canary_20260804` to a new working directory; do not overwrite it in place.

## After PyPI publication

PyPI files are immutable. Do not overwrite or silently replace the canary version. If the package is defective,
yank that exact release with an operator-approved reason, preserve its artifacts and logs, fix forward with a new
patch version, and re-run the complete clean build.

## After ModelScope deployment

Stop or disable the new canary service. Create a separate service configuration that selects a previously verified
PyPI version, or restore the prior service if its transport/configuration is unchanged. Verify the returned
health/tool surface before redirecting clients. Do not claim rollback completion until the website shows the old
service is active and the new service is no longer receiving requests.
