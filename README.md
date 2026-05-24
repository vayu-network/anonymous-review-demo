# Anonymous Review Demo

Test repo demonstrating ZK-attested anonymous code review via Longfellow.
Pull requests cannot merge until N anonymous reviewers approve through the
issuer UI at <http://localhost:8000>.

## Modules

| Module | Description |
|---|---|
| `src.rate_limiter` | Token-bucket rate limiter. Tests in `tests/test_rate_limiter.py`. |
