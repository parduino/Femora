import subprocess
import sys
def get_requirements():
    try:
        # Run pip-compile and capture output
        result = subprocess.run(
            [sys.executable, "-m", "piptools", "compile", "--no-header", "--no-annotate", 
             "--no-emit-index-url", "--output-file", "-", "requirements.in"],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Parse the output
        requirements = []
        for line in result.stdout.splitlines():
            line = line.strip()
            if line and not line.startswith('#'):
                requirements.append(line)
        flexible_requirements = []
        for req in requirements:
            # Keep any complex requirements (with [extras])
            if '[' in req and ']' in req:
                flexible_requirements.append(req)
            else:
                # Replace == with >= for simple requirements
                flexible_req = req.replace('==', '>=')
                flexible_requirements.append(flexible_req)
        return flexible_requirements
        
    except Exception as e:
        print(f"Error running pip-compile: {e}")
        # Fallback to reading requirements.in
        with open('requirements.in') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]

reqs =  get_requirements()
# save tot requirements.txt
with open('requirements.txt', 'w') as f:
    for i, req in enumerate(reqs):
        if i < len(reqs) - 1:
            f.write(req + '\n')
        else:
            f.write(req)