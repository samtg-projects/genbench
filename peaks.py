import json, os, sys
root = os.path.expanduser("~/.local/state/samcloud/compute-jobs")
for d in sorted(os.listdir(root)):
    s = os.path.join(root, d, "exec", "samples.jsonl")
    if not os.path.exists(s): continue
    r = [json.loads(l) for l in open(s) if l.strip()]
    pk = max((x.get("footprint_peak_mb") or 0) for x in r) if r else 0
    fr = [x["free_pct"] for x in r if x.get("free_pct") is not None]
    rcf = os.path.join(root, d, "exec", "rc")
    rc = open(rcf).read().strip() if os.path.exists(rcf) else "-"
    print(f"{d:50s} rc={rc:3s} peak_gb={pk/1024:5.1f} minfree={min(fr) if fr else '-'} {r[0]['t'] if r else ''} -> {r[-1]['t'] if r else ''}")
