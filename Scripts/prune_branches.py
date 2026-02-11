import subprocess

KEEP = {'master', 'develop'}

def run(cmd):
    print('RUN:', cmd)
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if res.stdout:
        print(res.stdout.strip())
    if res.stderr:
        print(res.stderr.strip())
    return res

# local branches
res = run("git for-each-ref --format='%(refname:short)' refs/heads")
locals = [b.strip().strip("'") for b in res.stdout.splitlines() if b.strip()]
for b in locals:
    if b not in KEEP:
        print(f"Deleting local branch: {b}")
        run(f"git branch -D {b}")

# remote branches
res = run("git for-each-ref --format='%(refname:short)' refs/remotes")
remotes = [r.strip().strip("'") for r in res.stdout.splitlines() if r.strip()]
for r in remotes:
    if r.startswith('origin/'):
        name = r.split('/',1)[1]
        if name not in KEEP and name != 'HEAD':
            print(f"Deleting remote branch: {name}")
            run(f"git push origin --delete {name}")

print('Done')
