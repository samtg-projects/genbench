# tsplat-service

TripoSplat (`VAST-AI-Research/TripoSplat`) image → 3D Gaussian splat PLY, as an authenticated async network service any samcloud seat can call. Landed in genbench as `service/tsplat/`; see `DEPLOY.md` for the Obelisk release recipe and the service handover.

## Call it
Every route needs your samcloud bearer, including `/health`, and you must be in `work` or `services`. **Outputs are delivered through `reply_to`.** The service uploads them to its sink group and links each one to that task or ticket, so anyone who can read the object can read the files. The service also has to be able to read it, so pick an object in `work` or `projects`. Both checks happen at submit, and a failure returns 403.

```
# submit (202 + job; the same Idempotency-Key returns the same job)
curl -s -H @"$HOME/.samcloud/token.hdr" -H "Idempotency-Key: eot-12345" -H "Content-Type: application/json" \
  -d '{"file_id": <FILE_ID>, "matte": "auto", "reply_to": {"kind": "task", "id": <TASK_ID>}}' $BASE/v1/splat
# wait (up to 120 s per call; repeat until state is done or failed)
curl -s -H @"$HOME/.samcloud/token.hdr" "$BASE/v1/jobs/<id>/wait?timeout_s=120"
```

| field | |
|---|---|
| `file_id` | a files-plane image **you** can read. The service fetches it with your bearer. |
| `matte` | `auto` (BiRefNet; whole frame if it finds no subject), `opaque` (whole frame as a relief), `rgba` (your alpha) |
| `num_gaussians` | 16384–262144, default 262144 |
| `publish` | optional `{}` or `{name}`. The PLY becomes a draft headset bundle in the registry group set by `registry_group` (the only group the service can write to). `result.registry` goes `converting` → `published` (with `bundle`) or `failed`, and the outcome is also posted on `reply_to`. Conversion runs on the host's splat pool and can take minutes. The follower lives in memory, so if the service restarts mid-conversion, `converting` stays as it is. The bundle may still have been made: look in that group. Moving a draft into a real collection is a person's call. |
| `render` | default true: a 1024 px three-quarter beauty shot and a 4-view sheet |
| `reply_to` | **required.** `{kind: task|ticket, id}`. All outputs are linked there (`result.links`), and a short comment with the PLY and beauty shot is posted. |

The result has `ply_file_id`, `prepared_file_id` (what TripoSplat actually saw), `beauty_file_id`, `sheet_file_id`, `matte_used`, timings, and `frame` (up `0,-1,0`, view `-1,0,0`: use these when registering).

**What to expect:** TripoSplat is single-object. Scenes become front-facing dioramas, a design sheet with N views becomes N objects, and a clean single view on a plain background gives the best asset.

## Run it
`python -m tsplat_service --config service.json` (see `deploy/service.example.json`). It refuses to start unless its token verifies as `principal.expected_username`. It holds one `gpu-metal` lease of `memory_mb` while the model is loaded and releases it after `idle_release_s` without work. Deploy with the `deploy/` LaunchAgent and a `service.json` built from `deploy/service.example.json` (see `DEPLOY.md`). Tests: `uv run --with pytest --with pillow --with numpy python -m pytest tests`; real model: `tests/real_pipeline.py` under a GPU claim.
