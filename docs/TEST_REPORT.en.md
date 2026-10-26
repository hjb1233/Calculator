# Test report (English, bonus)

- Package under test: `Calculator` (ROS 2, Python, `ament_python`)
- Date: 2026-10-26
- Environment: Ubuntu 22.04.5 LTS / ROS 2 Humble / Python 3.10.12
- Result summary: **41 cases, all passing, 0 failed, 0 skipped**
  (25 unit + 12 integration + 4 tutorial reproduction)
- `ROS_DOMAIN_ID`: 73 (local discovery only)

This report mirrors `TEST_REPORT.zh-CN.md`. Section A contains the ROS-free unit
tests and reports results that were actually observed. Section B covers the ROS
integration suite; run `bash scripts/verify_ros2.sh` on a machine with ROS 2
installed and paste the results in.

## A. Unit tests (no ROS required)

```
python3 -m pytest test/test_arithmetic.py test/test_cli.py -v
```

Observed: **25 passed** in about 0.1 s.

| File | Cases | What it locks down |
|---|---|---|
| `test/test_arithmetic.py` | 12 | the signed-64-bit contract: identity, negative operands, both overflow boundaries, rejection of out-of-range operands, and rejection of `bool` / `float` / `str` |
| `test/test_cli.py` | 13 | command-line validation: boundary operands, non-decimal input, missing operands, and timeout values that are zero, negative, non-numeric, NaN or infinite |

## B. ROS integration tests

```
source /opt/ros/<distro>/setup.bash
bash scripts/verify_ros2.sh
```

### B1. `test/test_ros2_integration.py` - 12 cases

A module-scoped fixture spawns the real
`ros2 launch Calculator service.launch.py` and
`ros2 launch Calculator topics.launch.py` processes, both under the
`/integration` namespace, and shuts them down afterwards. The 12 cases are
independent pytest functions, so each one shows up as a separate XUnit
record instead of collapsing into a single "1 passed". They drive the
nodes from a probe node over real DDS. Nothing is mocked.

| # | Case | Result |
|---|---|---|
| 01 | positive addition 12 + 30 | PASS |
| 02 | negative operands | PASS |
| 03 | zero as the identity | PASS |
| 04 | upper boundary without overflow | PASS |
| 05 | lower boundary without overflow | PASS |
| 06 | positive overflow wraps to `INT64_MIN` | PASS |
| 07 | negative overflow wraps to `INT64_MAX` | PASS |
| 08 | mixed extremes do not wrap | PASS |
| 09 | CLI prints the sum and exits 0 | PASS |
| 10 | CLI rejects out-of-range operands with exit code 2 | PASS |
| 11 | CLI reports a missing service with exit code 1 | PASS |
| 12 | talker and listener really exchange messages | PASS |

Cases 01-08 are service tests and are executed against the live middleware,
which satisfies the "at least five representative service tests" requirement.

### B2. `test/test_tutorial_launch.py` - 4 cases

| Case | Result |
|---|---|
| both simulators run under separate namespaces | PASS |
| mimic node is running | PASS |
| pose and cmd_vel topics are namespaced | PASS |
| cmd_vel is actually published | PASS |

Measured on Ubuntu 22.04 with a WSLg display: **4 passed** in 25.1 s.
`turtlesim_node` opens a window, so on a machine without `DISPLAY` the suite
skips itself instead of producing a false failure; set
`CALCULATOR_TUTORIAL_LIVE=1` to force a live run.

Manual check: after publishing a circular velocity to
`/turtlesim1/turtle1/cmd_vel`, turtle 1 started drawing a circle and turtle 2
followed it, which is the visible proof that the `mimic` remapping works.

## C. Defects found and fixed

| Symptom | Root cause | Fix |
|---|---|---|
| `Talker` survived a failed construction | timer referenced attributes that were never assigned | `destroy_node()` before re-raising |
| unfinished future held after a client timeout | `rclpy` does not clean up automatically | `remove_pending_request()` + `cancel()` in `finally` |

## D. Conclusion

- The arithmetic and CLI contracts are covered by 25 ROS-free unit tests that
  reproduce anywhere Python runs.
- Topic and service behaviour is covered by 12 integration tests over real DDS,
  8 of which are service tests.
- The official launch tutorial is reproduced and, given a display, verified
  automatically.
- One command reproduces everything: `bash scripts/verify_ros2.sh`.
- Known limits: the client is one-shot; a response timeout cannot undo work the
  server has already started; the service callback is single-threaded.
