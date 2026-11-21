# tsplat-service

TripoSplat (`VAST-AI-Research/TripoSplat d8db9e0`) image → 3D Gaussian splat PLY, as an authenticated async network service any samcloud seat can call. Design: samcloud doc 683, plan task 1401.

## Through the asset registry (task 1411)
With `registry_pool` configured, the service is also the worker for the registry's `image-to-splat` transform. Anyone signed in to the registry runs it on an image in one of their own groups. The registry handles sign-in, groups and permissions, the PLY lands in that group as a `splat-ply` with a measured `splatFrame`, and the registry's chain makes the headset bundle. The worker claims jobs with the pool's bearer, reads inputs from presigned URLs and returns the PLY through a presigned PUT; it holds no S3 keys. If the token file is missing, the pool stays off.

## Try it in a browser
Open `https://tsplat-obelisk.samtg.xyz/` and paste your samcloud token. It's kept in that tab's session storage and sent only to this service. Then drop an image, or give a file id. The page uploads the image to the files plane as you (`POST /v1/upload`), runs the job, and shows what TripoSplat saw, the beauty shot and the 4-view sheet (read as you through `GET /v1/files/{id}/raw`), plus a PLY download and the registry state if you published.

## Call it
Every route needs your samcloud bearer, including `/health`, and you must be in `work` or `services`. **Outputs are delivered through `reply_to`.** The service uploads them to its sink group and links each one to that task or ticket, so anyone who can read the object can read the files. The service also has to be able to read it, so pick an object in `work` or `projects`. Both checks happen at submit, and a failure returns 403.

```
# submit (202 + job; the same Idempotency-Key returns the same job)
curl -s -H @"$HOME/.samcloud/token.hdr" -H "Idempotency-Key: eot-3367-a" -H "Content-Type: application/json" \
  -d '{"file_id": 3367, "matte": "auto", "reply_to": {"kind": "task", "id": 1399}}' $BASE/v1/splat
# wait (up to 120 s per call; repeat until state is done or failed)
curl -s -H @"$HOME/.samcloud/token.hdr" "$BASE/v1/jobs/<id>/wait?timeout_s=120"
```

| field | |
|---|---|
| `file_id` | a files-plane image **you** can read. The service fetches it with your bearer. |
| `matte` | `auto` (BiRefNet; whole frame if it finds no subject), `opaque` (whole frame as a relief), `rgba` (your alpha) |
| `num_gaussians` | 16384–262144, default 262144 |
| `publish` | optional `{}` or `{name}`. The PLY becomes a draft headset bundle in the registry's **tsplat drafts** group (the only group the service can write to). `result.registry` goes `converting` → `published` (with `bundle`) or `failed`, and the outcome is also posted on `reply_to`. Conversion runs on wafer's splat pool and can take minutes. The follower lives in memory, so if the service restarts mid-conversion, `converting` stays as it is. The bundle may still have been made: look in *tsplat drafts*. Moving a draft into a real collection is for Sam or claude-wafer-services. |
| `render` | default true: a 1024 px three-quarter beauty shot and a 4-view sheet |
| `reply_to` | **required.** `{kind: task|ticket, id}`. All outputs are linked there (`result.links`), and a short comment with the PLY and beauty shot is posted. |

The result has `ply_file_id`, `prepared_file_id` (what TripoSplat actually saw), `beauty_file_id`, `sheet_file_id`, `matte_used`, timings, and `frame` (up `0,-1,0`, view `-1,0,0`: use these when registering).

**What to expect:** TripoSplat is single-object. Scenes become front-facing dioramas, a design sheet with N views becomes N objects, and a clean single view on a plain background gives the best asset.

## Run it
`python -m tsplat_service --config service.json` (see `deploy/service.example.json`). It refuses to start unless its token verifies as `principal.expected_username`. It holds one `gpu-metal` lease of `memory_mb` while the model is loaded and releases it after `idle_release_s` without work. Deployment is samclaude-admin's: immutable releases under `~/var/obelisk-services/tsplat-service/releases/<sha>` from a merged commit, LaunchAgent from `deploy/`. Tests: `uv run --with pytest --with pillow --with numpy python -m pytest tests`; real model: `tests/real_pipeline.py` under a GPU claim.
