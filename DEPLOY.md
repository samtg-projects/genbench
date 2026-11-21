# Deploying the tsplat service

The service runs as a launchd agent on the services host (the account that
runs image-service), owned by that account. This doc is the release, deploy,
rollback and identity reference.

## 1. Release

The release bundle is a `git archive` of a merged commit of this
`service/tsplat/` directory, shipped as a base64 bundle embedded in a deploy
script with a sha256 check. On the host it unpacks to `releases/<sha>` where
`<sha>` is the git commit the archive was built from.

The TripoSplat repo is cloned from
`https://github.com/VAST-AI-Research/TripoSplat` pinned at `d8db9e0`
(the pin is in `tsplat.sh:7`). Its `ckpts/` and `assets/` are git-ignored
in genbench and pulled on the host by the deploy script.

```sh
# On the build machine: archive a merged commit, embed as base64 in the deploy script
SHA=$(git rev-parse --short=12 HEAD)                       # e.g. 24949f65d966
git archive --format=tar.gz --prefix=tsplat-service/ "$SHA" service/tsplat \
  | base64 > bundle.b64
echo "$(shasum -a 256 bundle.b64 | awk '{print $1}')" > bundle.sha256
# ... the deploy script carries $BUNDLE_B64 = "$(cat bundle.b64)" and verifies it:
echo "$SHA256  bundle.b64" | shasum -a 256 -c -
```

## 2. Deploy

On the host, as the services account. The gateway hop never passes stdin EOF,
so every step runs with `< /dev/null`:

```sh
# 1. Unpack the release
mkdir -p releases/<sha>
base64 -d <<< "$BUNDLE_B64" | tar -xzf - -C releases/<sha>/tsplat-service/ --strip-components=1

# 2. Write service.json from the example, with deploy-time values.
#    The example has six placeholders; two of them share a prefix:
#      REPLACE-WITH-YOUR-REGISTRY      (the registry url)
#      REPLACE-WITH-YOUR-REGISTRY-GROUP (the registry group name)
#    The URL placeholder is a prefix of the GROUP placeholder, so substitute
#    the LONGER pattern first — otherwise the URL sub swallows the start of
#    the GROUP placeholder and the result is <registry_url>-GROUP.
sed -e "s|REPLACE-WITH-YOUR-REGISTRY-GROUP|<registry_group>|g" \
    -e "s|REPLACE-WITH-YOUR-SERVICE-USERNAME|<username>|g" \
    -e "s|REPLACE-WITH-YOUR-USER-ID|<user_id>|g" \
    -e "s|REPLACE-WITH-YOUR-RESOURCE|<resource>|g" \
    -e "s|REPLACE-WITH-YOUR-SERVICE-ID|<service_id>|g" \
    -e "s|REPLACE-WITH-YOUR-REGISTRY|<registry_url>|g" \
  service/tsplat/deploy/service.example.json > releases/<sha>/service.json

# 3. Record the source manifest
echo "$sha" > releases/<sha>/source-manifest.txt
echo "$sha  $(shasum -a 256 releases/<sha>/bundle.tar.gz 2>/dev/null | awk '{print $1}')" \
  >> releases/<sha>/source-manifest.txt

# 4. Preflight: the service must verify its own identity before we load it.
#    `tsplat_service.__main__` has no --preflight flag, so the real check is
#    a one-liner that constructs the Principal and calls .check():
PYTHONPATH="releases/<sha>" "$(which python3)" -B -c \
  "import json; from tsplat_service import plane; \
   plane.Principal(json.load(open('releases/<sha>/service.json'))).check(); \
   print('preflight ok')"
# must print: preflight ok
# (equivalently: PYTHONPATH="releases/<sha>" python3 -B -m tsplat_service \
#    --config releases/<sha>/service.json < /dev/null &  # then grep the log for
#    "listening on … as <principal>"; but the one-liner above is the non-blocking check.)

# 5. Render the plist and bootstrap
sed -e "s|@VENV@|$(python3 -c 'import sys; print(sys.prefix)')|g" \
    -e "s|@RELEASE@|$PWD/releases/<sha>|g" \
    -e "s|@HOME@|$HOME|g" \
  service/tsplat/deploy/com.samcloud.tsplat-service.plist.template \
    > ~/Library/LaunchAgents/com.samcloud.tsplat-service.plist

launchctl bootout user/$(id -u)/com.samcloud.tsplat-service 2>/dev/null < /dev/null || true
launchctl bootstrap user/$(id -u) ~/Library/LaunchAgents/com.samcloud.tsplat-service.plist < /dev/null

# 6. Verify: listening, and the GPU resource is settled
grep "listening on" ~/local/var/tsplat-service/logs/service.log
# expect: listening on 0.0.0.0:<port> as <principal>

# Check the GPU resource: unsettled must be empty (alongside active and queued).
# An orphaned lease once held Obelisk's queue for ~5.5 h (1136 c14918–c14920,
# fixed by PR #10 / 24949f6): a load that fails must give the lease back, not
# renew it forever.
TOKEN=$(cat ~/.local/var/tsplat-service/token)
curl -sS -H "Authorization: Bearer $TOKEN" \
  "https://tsplat-obelisk.samtg.xyz/v1/resources/gpu-0" | python3 -m json.tool
# expect: "unsettled": []   (active and queued may be non-empty; that's fine)
```

The launch agent gives the process a GPU lease via the `resource_id` in
`service.json` (the same GPU device image-service uses). The claim queue is
first-come-first-served with no deadline.

The launchd domain is `user/<uid>`, not `gui/`: the plist carries
`LimitLoadToSessionType Background` because a gateway session can't bootstrap
into `gui` (doc 658, "operating notes").

The token is a raw token in `principal.token_file`
(`~/.local/var/tsplat-service/token`), not a header file.

## 3. Rollback

Re-point the plist at the previous `releases/<sha>` and bootstrap again:

```sh
sed -i.bak "s|@RELEASE@|$PWD/releases/<prev_sha>|g" \
    ~/Library/LaunchAgents/com.samcloud.tsplat-service.plist
launchctl bootout user/$(id -u)/com.samcloud.tsplat-service 2>/dev/null < /dev/null || true
launchctl bootstrap user/$(id -u) ~/Library/LaunchAgents/com.samcloud.tsplat-service.plist < /dev/null
```

## 4. Identities

| Identity | Role |
|---|---|
| the services account | Device owner of the launch agent. Holds the raw service token in `principal.token_file` (`~/.local/var/tsplat-service/token`). |
| `service-tsplat` | The service's principal: the `user` in `deploy/service.json`. It is a member of the `work` and `services` groups so it can read caller inputs and write outputs. |
| the registry group | The group name for published bundles (e.g. `tsplat drafts`). |

The service's group_scope is the union of its groups (e.g. `work` and
`services`), so it can read any input a caller in either group can read.
Outputs land in the sink group and are linked to the caller's task or
ticket, so the caller can open them.

## 5. Registry publish

The `publish` endpoint (off by default, on in production) registers the
output bundle in the registry under the service's group. To enable it, set
`publish_enabled`, `registry_url` and `registry_group` in
`deploy/service.json` and restart the agent.

## 6. Test page (PR #9)

`GET /` serves `tsplat_service/ui.html`, a static page that holds no data:
it keeps the caller's token in the tab's session storage and every call it
makes is authenticated. `POST /v1/upload` stores an image under the caller's
own identity (group `work`); `GET /v1/files/{id}/raw` proxies only the
caller's own job outputs, and only as `image/png`, `image/jpeg` or
`image/webp` (a PLY is served as `application/octet-stream` with a
`Content-Disposition: attachment` so the browser can't sniff it as HTML).
`frame-ancestors 'none'` blocks the page from being framed.
