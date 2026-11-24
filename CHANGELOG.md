# Changelog

All notable changes to this project are listed here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow
[Semantic Versioning](https://semver.org/).

## [1.0.0] - 2026-11-24

The 2022 mission flies again in simulation, from the operator's take-off to a landing outside the red and yellow
zones. The release includes a real-time demo video of one full run (`fenswood-demo.mp4`).

### Added

- The mission code from the team's May 2022 workspace, including `PathPlan2.py`, which never reached GitHub in 2022
  (#1).
- A camera tilt command at the start of the zone search, so the camera looks down on the zones (#3).
- The README with a demo animation, a NOTICE for the course template, and three viewer tools in `tools/viewer/` (#6).
- `docs/HANDOVER.md` for the next maintainer (#7).

### Fixed

- The controller image builds again. The build drops the base image's expired ROS apt key, pins the re-signed key by
  checksum and locks the Python packages with uv to the versions available in May 2022 (#2).
- The simulator is pinned to v0.0.2, because the current image fails ArduPilot's pre-arm check (#3).
- `simhost` and `sitl` restart on failure, because each exits if the other isn't up at start (#3).
- The controller waits for a new MAVROS state on the wall clock, so its timeouts run at the intended speed (#3).
- The yellow mask uses its intended lower bound, so it finds yellow. In 2022 it matched nothing (#3).
- The corridor starts even when `/failsafe_md` still reads `take off` after the climb (#3).
- The image processor creates its timers once, which stops the alert flood of about 860 messages a second (#4).
- The yaw step lasts 3 s instead of hovering for about 100 s (#4).
- The failsafe node creates its timers once (#5).

### Known limits

See the README's [Known limits](https://github.com/AdilShaikh1/fenswood-volcano-mission#known-limits) section and
[docs/HANDOVER.md](https://github.com/AdilShaikh1/fenswood-volcano-mission/blob/main/docs/HANDOVER.md). The mission
ends at the landing, and `rth` flies a straight line home.

[1.0.0]: https://github.com/AdilShaikh1/fenswood-volcano-mission/releases/tag/v1.0.0
