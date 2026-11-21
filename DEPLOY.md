# Deploying the tsplat service

The service runs as a launchd agent on the Obelisk host, owned by the
the services device (the account that runs image-service). This
doc is the release, deploy, rollback and identity reference.

## 1. Release

The release bundle is built from this repository. A bundle is a
`tar.gz` of this `service/tsplat/` directory plus the TripoSplat repo
(`git clone https://github.com/Victor074/TRIPoSPLAT.git`, its `ckpts/`
and `assets/` are git-ignored here but are pulled by the deploy script on
the host). The bundle is published to the registry under a
`a registry group the service publishes to.

```sh
# Build the deploy bundle
tar -czf /tmp/tsplat-release.tar.gz -C service/tsplat .

# Ship it to the Obelisk host and unpack
scp /tmp/tsplat-release.tar.gz services-host@<host>:~/var/tsplat-service/
ssh services-host@<host> 'rm -rf ~/var/tsplat-service/release && \
  mkdir -p ~/var/tsplat-service/release && \
  tar -xzf ~/var/tsplat-service/tsplat-release.tar.gz -C ~/var/tsplat-service/release'
```

The service reads its config from a copy of
`deploy/service.example.json`). The example is de-obelisk-ized: `@BASE@`
is substituted to the plane API base (e.g. `https://cloud.samtg.xyz`),
`@HOME@` to the running user's home, and `@PORT@` to the bind port.

## 2. Deploy

On the host, as the services account:

```sh
# Render the plist (substitute @BASE@, @HOME@, @PORT@, @GPU@)
sed -e "s|@BASE@|https://cloud.samtg.xyz|g" \
    -e "s|@HOME@|$HOME|g" \
    -e "s|@PORT@|8812|g" \
    -e "s|@GPU@|$(echo ${GPU:-gpu-0})|g" \
    service/tsplat/deploy/com.samcloud.tsplat-service.plist.template \
    > ~/Library/LaunchAgents/com.samcloud.tsplat-service.plist

# Install the release
rm -rf ~/var/tsplat-service/release-prev && \
  mv ~/var/tsplat-service/release ~/var/tsplat-service/release-prev && \
  mv ~/var/tsplat-service/release-new ~/var/tsplat-service/release

# Reload the launch agent
launchctl bootout gui/$(id -u)/com.samcloud.tsplat-service 2>/dev/null || true
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.samcloud.tsplat-service.plist

# Verify
curl -sf https://tsplat-obelisk.samtg.xyz/health
```

The launch agent gives the process a GPU lease via
`TSPLAT_GPU=<gpu>` (the same GPU device image-service uses). The claim
queue is first-come-first-served with no deadline.

## 3. Rollback

The previous release is kept at `~/var/tsplat-service/release-prev`:

```sh
launchctl bootout gui/$(id -u)/com.samcloud.tsplat-service 2>/dev/null || true
rm -rf ~/var/tsplat-service/release
mv ~/var/tsplat-service/release-prev ~/var/tsplat-service/release
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.samcloud.tsplat-service.plist
curl -sf https://tsplat-obelisk.samtg.xyz/health
```

## 4. Identities

| Identity | Role |
|---|---|
| the services account | Device owner of the launch agent; holds the `~/.samcloud/token.hdr` that authenticates the service. |
| `service-tsplat` | The service's principal: the `user` in `deploy/service.json`. It is a member of the `work` and `services` groups so it can read caller inputs and write outputs. |
| the registry group | The group id for published bundles. |

The service's group_scope is the union of its groups (e.g. `work` and `services`), so it
can read any input a caller in either group can read. Outputs land in
`service-tsplat-sink` and are linked to the caller's task or ticket, so
the caller can open them.

## 5. Registry publish

The `publish` endpoint (off by default, on in production) registers the
output bundle in the registry under the service's group. To enable it,
set `publish.group_id` and `publish.bundle_name` in `deploy/service.json`
and restart the agent.
