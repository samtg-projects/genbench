# Deploying the tsplat service

The service runs as a launchd agent on the services host (the account that
runs image-service), owned by that account. This doc is the release, deploy,
rollback and identity reference.

## 1. Release

The release bundle is a `git archive` of a merged commit of this
`service/tsplat/` directory, shipped as a base64 bundle embedded in a
deploy script with a sha256 check. On the host it unpacks to
`releases/<sha>` where `<sha>` is the git commit the archive was built from.

The TripoSplat repo is cloned from
`https://github.com/VAST-AI-Research/TripoSplat` pinned at `d8db9e0`
(the pin is in `tsplat.sh:7`). Its `ckpts/` and `assets/` are git-ignored
in genbench and pulled on the host by the deploy script.

```sh
# On the build machine: archive a merged commit, embed as base64 in the deploy script
git archive --format=tar.gz --prefix=tsplat-service/ <sha> service/tsplat | base64 > bundle.b64
echo "$(shasum -a 256 bundle.b64 | awk '{print $1}')" > bundle.sha256
```

## 2. Deploy

On the host, as the services account. The gateway hop never passes stdin EOF,
so every step runs with `< /dev/null`:

```sh
# 1. Unpack the release
mkdir -p releases/<sha>
base64 -d <<< "$BUNDLE_B64" | tar -xzf - -C releases/<sha>/tsplat-service/ --strip-components=1

# 2. Write service.json from the example, with deploy-time values
sed -e "s|REPLACE-WITH-YOUR-SERVICE-USERNAME|<username>|g" \
     -e "s|REPLACE-WITH-YOUR-USER-ID|<user_id>|g" \
     -e "s|REPLACE-WITH-YOUR-RESOURCE|<resource>|g" \
     -e "s|REPLACE-WITH-YOUR-SERVICE-ID|<service_id>|g" \
     -e "s|REPLACE-WITH-YOUR-REGISTRY|<registry_url>|g" \
     -e "s|REPLACE-WITH-YOUR-REGISTRY-GROUP|<registry_group>|g" \
    service/tsplat/deploy/service.example.json > releases/<sha>/service.json

# 3. Record the source manifest
echo "$sha" > releases/<sha>/source-manifest.txt
echo "$sha  $(shasum -a 256 releases/<sha>/bundle.tar.gz | awk '{print $1}')" >> releases/<sha>/source-manifest.txt

# 4. Preflight: the service must verify its own identity before we load it
python3 -m tsplat_service --config releases/<sha>/service.json --preflight < /dev/null
# must print: preflight ok

# 5. Render the plist and bootstrap
sed -e "s|@VENV@|$(python3 -c 'import sys; print(sys.prefix)')|g" \
     -e "s|@RELEASE@|$PWD/releases/<sha>|g" \
     -e "s|@HOME@|$HOME|g" \
    service/tsplat/deploy/com.samcloud.tsplat-service.plist.template \
     > ~/Library/LaunchAgents/com.samcloud.tsplat-service.plist

launchctl bootout user/$(id -u)/com.samcloud.tsplat-service 2>/dev/null < /dev/null || true
launchctl bootstrap user/$(id -u) ~/Library/LaunchAgents/com.samcloud.tsplat-service.plist < /dev/null

# 6. Verify
grep "listening on" ~/local/var/tsplat-service/logs/service.log
# expect: listening on 0.0.0.0:<port> as <principal>
```

The launch agent gives the process a GPU lease via the resource in
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
| the registry group | The group id for published bundles. |

The service's group_scope is the union of its groups (e.g. `work` and
`services`), so it can read any input a caller in either group can read.
Outputs land in `service-tsplat-sink` and are linked to the caller's task or
ticket, so the caller can open them.

## 5. Registry publish

The `publish` endpoint (off by default, on in production) registers the
output bundle in the registry under the service's group. To enable it, set
`publish_enabled`, `registry_url` and `registry_group` in
`deploy/service.json` and restart the agent.
