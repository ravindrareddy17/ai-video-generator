import urllib.request, json
url = 'https://api.github.com/repos/ravindrareddy17/ai-video-generator/actions/runs?per_page=10'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
data = json.loads(urllib.request.urlopen(req).read())
run143 = next(r for r in data['workflow_runs'] if r['run_number'] == 143)
jobs_url = run143['jobs_url']
req2 = urllib.request.Request(jobs_url, headers={'User-Agent': 'Mozilla/5.0'})
jobs = json.loads(urllib.request.urlopen(req2).read())['jobs']
for job in jobs:
    print(f"Job: {job['name']} | Status: {job['status']}")
    for step in job['steps']:
        print(f"  - {step['name']}: {step['status']}")
