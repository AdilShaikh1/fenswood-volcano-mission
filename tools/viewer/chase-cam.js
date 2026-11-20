// Paste into the browser console on http://localhost:8080 (gzweb) once the drone shows in the world. Highlights the
// drone and keeps the camera on it, while orbit and zoom still work. Paste again to re-centre;
// clearInterval(window.__droneChase) stops it. It hides gzweb's menu panels and toolbar so the drone isn't behind
// them; reload the page to get them back.
(() => {
  const DRONE_MODEL_NAME = "iris_demo";
  // starting camera offset from the drone, Gazebo world frame, metres
  const CAMERA_BACK_X_M = 3.5;
  const CAMERA_BACK_Y_M = 3.5;
  const CAMERA_UP_M = 2.5;
  const FOLLOW_PERIOD_MS = 100;

  const drone = scene.getByName(DRONE_MODEL_NAME);
  if (!drone) {
    console.warn(`${DRONE_MODEL_NAME} isn't loaded yet; paste again once the drone shows in the world.`);
    return;
  }
  scene.selectEntity(drone);
  $(".leftPanels").hide();
  $("#leftPanel, .tab, #toolbar, .gzGUI").not("#container, canvas").hide();
  scene.camera.position.set(
    drone.position.x - CAMERA_BACK_X_M,
    drone.position.y - CAMERA_BACK_Y_M,
    drone.position.z + CAMERA_UP_M);

  clearInterval(window.__droneChase);
  let lastDronePosition = drone.position.clone();
  // each tick moves the camera by the drone's displacement, so the viewing offset stays fixed while orbit still works
  window.__droneChase = setInterval(() => {
    scene.camera.position.add(drone.position.clone().sub(lastDronePosition));
    scene.controls.target.copy(drone.position);
    scene.camera.lookAt(drone.position);
    lastDronePosition = drone.position.clone();
  }, FOLLOW_PERIOD_MS);
})();
