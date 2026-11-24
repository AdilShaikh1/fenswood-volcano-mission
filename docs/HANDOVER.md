# Handover: Fenswood Volcano Mission

Author: Adil Shaikh · Last verified: 2026-11-20, with the code as on `main` at 7a47456

This note is for the next engineer who picks the project up. It assumes you know ROS 2 and Docker but not this
stack. Read the [README](../README.md) first for what the mission does and how to run it. This note covers what the
README leaves out. It explains how the parts connect, what changed since 2022 and why, which pins keep it working,
and which traps cost time.

## Current state

- The full outbound mission flies in simulation on ROS 2 Foxy with Gazebo Classic and ArduPilot SITL. It arms on
  the operator's `take off`, climbs to 20 m, flies four corridor waypoints, tilts the camera down over the survey
  area, moves clear of the red zones and lands outside the red and yellow zones.
- Four verification runs in November 2026 landed within about 2 m of each other, at about 51.42213, -2.66816.
- There are no automated tests. The check is a full simulated mission plus `tools/viewer/topic_rates.py`, as the
  README's Tests section describes.
- A port to ROS 2 Jazzy and Gazebo Harmonic is planned and not started.

## How the stack fits together

`fenswood_volcano_template/docker-compose-finite-state.yml` starts five containers on one Docker network. The
corridor waypoints come from `PathPlan2.py`, which builds a visibility graph around polygons written as coordinates in
its own code, as the README's What it does section describes.

| Container | Image | Role | Host port |
| --- | --- | --- | --- |
| `simhost` | `starling-sim-iris-ap-fenswood:v0.0.2` | Gazebo Classic world with the drone, plus the gzweb browser view | 8080 (gzweb) |
| `sitl` | `starling-sim-ardupilot-copter:v0.0.8` | ArduPilot copter SITL, flying the Gazebo drone | none |
| `mavros` | `starling-mavros:v0.1.0` | MAVROS connected to SITL on `tcp://sitl:5760`, topics under `/vehicle_1/mavros/` | 5761 (ground station) |
| `rosbridge-suite` | `rosbridge-suite:v0.1.0` | rosbridge WebSocket for browser tools | 9090 |
| `controller` | built from `fenswood_drone_controller/` | the three mission nodes | none |

The controller image's launch file, `controller_finite_state.launch.xml`, starts three nodes. They talk to each other
and to MAVROS over these topics.

- **`image_processor`** reads the camera on `/vehicle_1/camera/image_raw` (Image). It publishes `/red_zone_alert`
  and `/yellow_zone_alert` (String, about 20 Hz) for the controller, and the red-zone mask on `/video_frames`
  (Image) for debugging.
- **`failsafe`** publishes a picture of the current mode on `/status_frames` (Image, 1 Hz) for debugging.
- **`/failsafe_md`** (String) carries the operator mode. The operator, `failsafe` and `controller_finite_state`
  publish on it, and `controller_finite_state` and `failsafe` read it.
- **`controller_finite_state`** tilts the camera on `/vehicle_1/gimbal_tilt_cmd` (Float32, radians). It reads
  MAVROS's `state`, `global_position/global` and `local_position/pose`, and it commands the drone through
  `setpoint_position/global` and `setpoint_velocity/cmd_vel_unstamped`. All MAVROS topics sit under
  `/vehicle_1/mavros/`.

An alert reads `<where to go> <where the zone is>`, for example `left 1`. The second field is the band of the 640 px
image that holds the zone's centre. The first word says which way to move away from it.

| Band | Where in the image | Alert |
| --- | --- | --- |
| `-2` | outer quarter, left edge | `safe -2` |
| `-1` | inner quarter, left of centre | `right -1` |
| `1` | inner quarter, right of centre | `left 1` |
| `2` | outer quarter, right edge | `safe 2` |

`safe` is the code's name for a zone off to the side. An empty alert means no zone of that colour is large enough to
count. Only the red alert steers the drone. The controller reads the yellow alert but doesn't act on it.

- While a red zone sits in an inner quarter, the controller moves the drone sideways.
- Once one sits in an outer quarter, it stops the sideways move and backs away from the survey area until the drone
  is 35 m out, then lands.

## Run and verify

Follow the README's Install and Usage sections. The README's "It's working if" section lists the log lines, the landing
spot and the topic rates of a good run.

To watch a run, open <http://localhost:8080> for the world, paste `tools/viewer/chase-cam.js` into its console once
the drone shows, and open `tools/viewer/drone-cam.html` for the onboard camera.

## What changed since 2022

The code comes from the team's May 2022 workspace. Five pull requests imported and fixed it, and a sixth added the
documentation. PR #1 was checked by comparing the files byte for byte with the workspace copies, and PR #2 by building
the image and importing every module. PRs #3 to #5 were each checked with a full simulated mission. Each PR
description says how it was verified.

| PR | Change | Why |
| --- | --- | --- |
| #1 | Imported the mission code from the May 2022 workspace, including `PathPlan2.py` | `controller_finite_state.py`, `controller_modular.py` and `controller_old_school.py` import `PathPlan2.py`, but it never reached GitHub in 2022. |
| #2 | Rebuilt the controller image: pinned ROS apt key, uv-locked Python packages, package files | The image no longer built. The base image trusts an expired ROS key, and unpinned packages pull pandas 2, which removed `GeoDataFrame.append` that `PathPlan2.py` uses. |
| #3 | Pinned the simulator to v0.0.2, added `restart: on-failure`, made `wait_for_new_status` wait for a new MAVROS state on the wall clock, tilted the camera down for the search, fixed the yellow colour range, and let the corridor start while `/failsafe_md` still reads `take off` | The latest simulator image fails ArduPilot's pre-arm check. `simhost` and `sitl` crash at start. The old status wait counted every 20 Hz alert as a step, so timeouts ran about 30 times too fast. The forward camera never saw the red zones as large enough. With the faster steps, the failsafe node's `take off` republish could land right after the climb and stop the mission. |
| #4 | Created the image processor's timers once, and gave the yaw step a 3 s wall-clock duration | A new timer per camera frame flooded the alert topics at about 860 messages a second. After the PR #3 fix, the yaw loop hovered for about 100 s. |
| #5 | Created the failsafe node's timers once | The same per-message timer pattern as PR #4. |
| #6 | README, demo animation, NOTICE, the LICENSE copyright line and viewer tools | Public documentation. |

## Decisions and pins

| What | Pinned to | Why |
| --- | --- | --- |
| Simulator image | `v0.0.2` by tag and digest | The current `latest` image (December 2022) fails pre-arm with `Gyros not calibrated`, most likely because of the sensor payload added in late 2022. Images between v0.0.2 and `latest` weren't tested. v0.0.2 (April 2022) is most likely what the 2022 flight used. Neither cause nor that last point is verified. |
| `simhost`, `sitl` restart | `on-failure` | Each resolves the other by name once at start and exits if the other isn't up. An exited container leaves Docker's DNS, so a plain start order can't fix it. |
| Python packages | uv lock with `exclude-newer` 2022-05-06, Python 3.8 | It keeps the 2022 APIs, such as `GeoDataFrame.append`. The lock is Linux x86_64 only. |
| ROS apt key | re-signed copy at a fixed rosdistro commit, with a checksum | The base image's copy expired. |
| uv binary | `ghcr.io/astral-sh/uv:0.10.4` by digest | Reproducible builds. |
| Other stack images | `sitl`, `mavros` and `rosbridge-suite` by tag only | Tags can be re-pushed. Only the simulator has a digest. |
| Base images | `starling-controller-base:latest` and the ROS apt packages are not pinned | A rebuild may pick up changes. |

## Gotchas

- **`ros2 topic echo` and `ros2 topic hz` through `docker exec` are unreliable here.** They printed nothing for
  topics that rosbridge received at 20 Hz. `ros2 topic pub` works. Measure with `topic_rates.py` inside a container,
  or subscribe through rosbridge. `tools/viewer/drone-cam.html` is a working rosbridge subscriber to copy from.
- **rosbridge v0.1.0 has two quirks.** It sends `uint8[]` fields as a JSON number array, not base64. It also sends
  nothing for a subscription that sets `throttle_rate` or `queue_length`.
- **Subscribing too early gets nothing.** A rosbridge subscription made before its topic exists stays silent, and a
  gzweb page opened before `simhost` serves stays on an error page. Reload once the stack is up.
- **The controller node stops after 600 steps.** `run()` counts them from the controller's start. A step is about
  1 s, but the corridor and the survey each run inside a single step, which took 84 s and 11 s in one timed run. So in
  a flown mission the node stops roughly 12 minutes after it starts. That figure comes from the code and the step
  times and hasn't been timed end to end. `/failsafe_md` then drops to the failsafe node's 0.1 Hz.
- **The arming window is about 400 steps, roughly 6.7 minutes.** It counts inside the same 600-step budget. Send
  `take off` within that time, or the controller logs `Failed to arm` and the mission ends. The node keeps stepping
  in state `None` until step 600. Restart the controller to try again. After take-off the mission needs fewer than 20
  steps, because the corridor and the survey count as one step each. A late take-off still has steps to spare, as long as start-up is short (about 10
  steps in testing).
- **`restart: on-failure` retries forever.** A real fault in `simhost` or `sitl` shows up as a restart loop in
  `docker compose ps`, not as an exit.
- **`up` reuses the existing controller image.** The node code is copied into the image at build time, so after you
  change a node, the Python lock or the Dockerfile, run `up --build`.

## Known limits

The README lists the mission's known limits. These are the extra ones a maintainer needs:

- If the drone doesn't get within about 1 m of a waypoint in 60 status updates (about a minute), the controller
  moves on to the next waypoint without logging an error.
- `land` and `rth` only act during the climb. The controller keeps the last mode it received, though. A `land` sent
  on the corridor or over the survey area changes nothing, because the mission lands at its own point anyway. An
  `rth` sent there turns that landing into a return-to-launch on the next step. This comes from reading the code and
  hasn't been flown.
- The controller subscribes to the velocity setpoint as `TwistStamped` but publishes it as `Twist`.
- `fenswood_volcano_template/tutorial/` and the template's other compose files describe the original course
  template, not this mission's fixes. The other compose files still use the unpinned simulator image.

## Where things live

Under `fenswood_volcano_template/`:

- `docker-compose-finite-state.yml` is the mission stack.
- `fenswood_drone_controller/` is the ROS package. Its inner Python folder of the same name holds the mission nodes
  `controller_finite_state.py`, `image_processor.py` and `failsafe.py`, and `PathPlan2.py`. The other controllers and `FSMtemplate.py` come from
  the course template and the team's 2022 experiments, and the stack doesn't launch them.
- `fenswood_drone_controller/python-deps/` holds `pyproject.toml` and `uv.lock` for the controller image.
- `fenswood_drone_controller/launch/` holds the launch files. The stack uses `controller_finite_state.launch.xml`.

At the repository root:

- `tools/viewer/` holds `drone-cam.html`, `chase-cam.js` and `topic_rates.py`.
- `docs/media/demo.webp` is the README demo, cut from one November 2026 run at 4× speed.
- [Pull requests #1 to #6](https://github.com/AdilShaikh1/fenswood-volcano-mission/pulls?q=is%3Apr+is%3Amerged)
  hold the change history, each with how it was verified.

## What's next

The planned next step is a port to ROS 2 Jazzy and Gazebo Harmonic with current Python packages. It hasn't started.
