FROM uobflightlabstarling/starling-controller-base:latest

# The base image trusts an expired copy of the ROS apt key; drop it and trust the re-signed copy (pinned commit).
RUN apt-key del F42ED6FBAB17C654
ADD --chmod=644 --checksum=sha256:4a91c49af0d6f0016108b93698782b596c27ccd836937e18e0e36c3347dc602f https://raw.githubusercontent.com/ros/rosdistro/eb71c289f4495a0327cd03a29205a2c411cd8129/ros.key /etc/apt/trusted.gpg.d/ros.gpg

RUN apt-get update \
    && apt-get install -y ros-foxy-vision-opencv \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies are locked with uv (Python 3.8, dated 2022-05) and installed into /ros_ws/.venv; the nodes reach them through PYTHONPATH below.
COPY --from=ghcr.io/astral-sh/uv:0.10.4@sha256:4cac394b6b72846f8a85a7a0e577c6d61d4e17fe2ccee65d9451a8b3c9efb4ac /uv /usr/local/bin/uv
ENV UV_PROJECT_ENVIRONMENT=/ros_ws/.venv
COPY python-deps /tmp/python-deps
# colcon must not scan the venv for packages.
RUN uv venv --python /usr/bin/python3 --system-site-packages /ros_ws/.venv \
    && touch /ros_ws/.venv/COLCON_IGNORE \
    && UV_NO_CACHE=1 uv sync --frozen --project /tmp/python-deps

COPY . /ros_ws/src/fenswood_drone_controller

# colcon runs under the system python (venv setuptools 62 installs node scripts to bin/, where ros2 does not look).
# The nodes then find the locked packages through PYTHONPATH.
ENV PYTHONPATH=/ros_ws/.venv/lib/python3.8/site-packages
RUN . /ros_ws/install/setup.sh \
    && PYTHONPATH= colcon build

CMD [ "ros2", "launch", "fenswood_drone_controller", "controller.launch.xml" ]
