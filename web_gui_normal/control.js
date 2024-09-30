// Publishing to Topic for Stance Control
// ------------------
var interval;

var command_input = new ROSLIB.Topic({
    ros : ros,
    name : '/kelpie/command_input',
    messageType : 'kelpie/commands'
});


function mouse_down(button) {
  let desired_movement = {
    gait_toggle : false,
    hop_toggle : false,
    calibration_toggle : false,
    joystick_toggle : false,
    pid_toggle : false,
    x : 0,
    y : 0,
    roll_movement : 0,
    pitch : 0,
    yaw_rate : 0,
    height_movement : 0
  }

  switch(button) {
    case 'height up':
      desired_movement.height_movement = 1
      break;
    case "height down":
      desired_movement.height_movement = -1
      break;
    case "pitch up":
      desired_movement.pitch = 1
      break;
    case "pitch down":
      desired_movement.pitch = -1
      break;
    case "roll left":
      desired_movement.roll_movement = 1
      break;
    case "roll right":
      desired_movement.roll_movement = -1
      break;
    case "yaw left":
      desired_movement.yaw_rate = 1
      break;
    case "yaw right":
      desired_movement.yaw_rate = -1
      break;
    default:
      break;
  }

  var command = new ROSLIB.Message(desired_movement);
  // console.log(command);
  command_input.publish(command);
}


function mouse_down(button) {
  document.getElementById("status").innerText = button + " button clicked";
  interval = setInterval(update, 50);
}


function mouse_up(button) {
  document.getElementById("status").innerText = button + " button released";
  clearInterval(interval);

  var command = new ROSLIB.Message({
    gait_toggle : false,
    hop_toggle : false,
    calibration_toggle : false,
    joystick_toggle : false,
    pid_toggle : false,
    x : 0,
    y : 0,
    roll_movement : 0,
    pitch : 0,
    yaw_rate : 0,
    height_movement : 0
  })

  // console.log(command)
  command_input.publish(command);
}