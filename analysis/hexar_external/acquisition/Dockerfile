# Official ROS Humble Ubuntu Jammy base, content-pinned.
FROM ros@sha256:d2bbb43b75b4b73b0552fcedf0aa195d8e9bdd21fe50c02e5c0a791951a55f8e
ENV DEBIAN_FRONTEND=noninteractive RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
RUN apt-get update && apt-get install -y --no-install-recommends xvfb libgl1-mesa-dri mesa-utils build-essential git python3-vcstool python3-rosdep python3-colcon-common-extensions ros-humble-rmw-cyclonedds-cpp ros-humble-rosbag2 ros-humble-rosbag2-storage-default-plugins ros-humble-navigation2 ros-humble-nav2-bringup ros-humble-gazebo-ros-pkgs ros-humble-gazebo-ros2-control ros-humble-xacro ros-humble-ros2-control ros-humble-ros2-controllers ros-humble-robot-state-publisher ros-humble-joint-state-publisher
WORKDIR /ws
COPY tiago_public.lock.repos /acquisition/tiago_public.lock.repos
RUN mkdir src && vcs import --input /acquisition/tiago_public.lock.repos src
COPY gazebo_classic_sick571.patch /acquisition/gazebo_classic_sick571.patch
RUN cd /ws/src/pal_urdf_utils && git apply /acquisition/gazebo_classic_sick571.patch
RUN rosdep init 2>/dev/null || true
RUN rosdep update && rosdep install --from-paths src -y --ignore-src --rosdistro humble
COPY prepare_world.py /acquisition/prepare_world.py
RUN python3 /acquisition/prepare_world.py
RUN . /opt/ros/humble/setup.sh && colcon build --parallel-workers 2 --cmake-args -DBUILD_TESTING=OFF
# Archive resolved binary dependencies; final image digest is required for a freeze.
RUN dpkg-query -W > /ws/binary-packages.lock
COPY . /acquisition
CMD ["bash"]
