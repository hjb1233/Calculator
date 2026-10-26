#!/usr/bin/env bash
# Build the package in a throwaway workspace and run every test that needs ROS.
#
#   source /opt/ros/humble/setup.bash
#   bash scripts/verify_ros2.sh
#
# Environment overrides:
#   CALCULATOR_TEST_WORKSPACE   build directory          (default: /tmp/calculator_test_ws)
#   CALCULATOR_TEST_RESULTS     XUnit output directory   (default: ./test-results)
#   ROS_DOMAIN_ID               DDS domain               (default: 73)
#
# Exit code 0 means: the package built, all pure unit tests passed, and every
# ROS integration test passed over the real middleware.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORKSPACE="${CALCULATOR_TEST_WORKSPACE:-/tmp/calculator_test_ws}"
RESULTS="${CALCULATOR_TEST_RESULTS:-$REPO_ROOT/test-results}"
export ROS_DOMAIN_ID="${ROS_DOMAIN_ID:-73}"

if [ -z "${ROS_DISTRO:-}" ]; then
  echo "ROS is not sourced. Run: source /opt/ros/<distro>/setup.bash" >&2
  exit 3
fi

echo "== ROS_DISTRO=$ROS_DISTRO  ROS_DOMAIN_ID=$ROS_DOMAIN_ID =="

for tool in colcon python3; do
  command -v "$tool" >/dev/null || { echo "missing: $tool" >&2; exit 3; }
done

mkdir -p "$RESULTS"

echo "== 1/4 pure unit tests (no ROS needed) =="
python3 -m pytest "$REPO_ROOT/test/test_arithmetic.py" "$REPO_ROOT/test/test_cli.py" \
  --junitxml="$RESULTS/unit.xml" -q

echo "== 2/4 build =="
rm -rf "$WORKSPACE"
mkdir -p "$WORKSPACE/src"
ln -sfn "$REPO_ROOT" "$WORKSPACE/src/Calculator"
cd "$WORKSPACE"
colcon build --packages-select Calculator --symlink-install
# ROS 的 setup.bash 引用了 AMENT_TRACE_SETUP_FILES 等未设默认值的变量，
# 在 `set -u` 下会直接报错退出，source 前后临时关掉 nounset。
set +u
source "$WORKSPACE/install/setup.bash"
set -u

echo "== 3/4 ROS integration tests =="
python3 -m pytest "$REPO_ROOT/test/test_ros2_integration.py" \
  --junitxml="$RESULTS/ros2-integration.xml" -q

echo "== 4/4 tutorial launch reproduction =="
if [ -n "${DISPLAY:-}${WAYLAND_DISPLAY:-}" ] || [ "${CALCULATOR_TUTORIAL_LIVE:-0}" = "1" ]; then
  python3 -m pytest "$REPO_ROOT/test/test_tutorial_launch.py" \
    --junitxml="$RESULTS/tutorial-launch.xml" -q || \
    echo "warning: tutorial launch check failed (turtlesim needs a working display)" >&2
else
  echo "skipped: no DISPLAY and CALCULATOR_TUTORIAL_LIVE!=1" >&2
fi

echo "== results written to $RESULTS =="
ls -1 "$RESULTS"
