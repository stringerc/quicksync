# Lawbot — common tasks (optional; same as scripts/*.sh)
.PHONY: preflight launch test ci-quality verify-apis security

preflight:
	bash scripts/preflight_launch.sh

launch:
	bash scripts/launch.sh

# Server only (skip preflight) — same as SKIP_PREFLIGHT=1 bash scripts/launch.sh
serve:
	SKIP_PREFLIGHT=1 bash scripts/launch.sh

test:
	python -m unittest discover -s tests -p 'test_*.py' -q

ci-quality:
	bash scripts/ci_quality.sh

# Ruff + Bandit (same as CI); dev-only, not part of the running server
security:
	bash scripts/security_scan.sh

verify-apis:
	python scripts/verify_apis.py
