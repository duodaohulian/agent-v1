# Rollback 1.0.12

The immutable blocked baseline is preserved at:

`<TORCH_REFERENCE_ROOT>`

The previous distribution files are separately preserved at:

`<BACKUP_ROOT>\release_1.0.12_torch_runtime_blocked_dist`

If the lightweight canary fails, disable the affected instance and preserve its logs and artifacts. Restore by copying the blocked backup into a new working directory; never overwrite the backup in place. The former Torch wheel is diagnostic evidence only and must not be published as the final 1.0.12 artifact because its Linux cold install did not pass the release gate.

For deployment rollback, return traffic to the previously validated 1.0.11 canary shell. That shell does not provide the restored six medical tools, so the capability reduction must be disclosed. Do not switch transport to HTTP, restore the five-model ensemble, change the threshold, or silently substitute a different model.
