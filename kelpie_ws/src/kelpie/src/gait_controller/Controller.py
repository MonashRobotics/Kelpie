import time
from math import degrees

import numpy as np
import rospy
from simple_pid import PID
from gait_controller.Gaits import GaitController
from gait_controller.StanceController import StanceController
from gait_controller.State import BehaviorState
from gait_controller.SwingLegController import SwingController
from kelpie_common.Utilities import clipped_first_order_filter
from geometry_msgs.msg import Point
from std_msgs.msg import Header
from transforms3d.euler import euler2mat
from kelpie_common.Config import ServoIndex as s_idx
from dataclasses import dataclass
import math
from kelpie_common.Utilities import RollingAverage

def yaw_clip(angle):
    if angle > 0:
        if angle > math.pi:
            return angle - 2*math.pi
    else:
        if angle < -math.pi:
            return angle + 2*math.pi
    return angle


@dataclass
class DesiredState:
    roll = 0
    pitch = 0
    yaw = 0
    height = -0.20
    smoothed_yaw = 0
    yaw_rate = 0


class Controller:
    """Controller and planner object
    """

    def __init__(
            self,
            config,
            inverse_kinematics,
            imu,
            offsets
    ):
        self.config = config

        ################# ROS PUBLISHER FOR TASK SPACE GOALS ##############
        # self.task_space_pub = rospy.Publisher('task_space_goals', TaskSpace, queue_size=10)
        # self.joint_space_pub = rospy.Publisher('joint_space_goals', JointSpace, queue_size=10)

        self.smoothed_yaw = 0.0  # for REST mode only
        self.inverse_kinematics = inverse_kinematics

        self.contact_modes = np.zeros(4)
        self.gait_controller = GaitController(self.config)
        self.swing_controller = SwingController(self.config)
        self.stance_controller = StanceController(self.config)

        self.hop_transition_mapping = {BehaviorState.REST: BehaviorState.HOP,
                                       BehaviorState.HOP: BehaviorState.FINISHHOP,
                                       BehaviorState.FINISHHOP: BehaviorState.REST,
                                       BehaviorState.TROT: BehaviorState.HOP}
        self.trot_transition_mapping = {BehaviorState.REST: BehaviorState.TROT, BehaviorState.TROT: BehaviorState.REST,
                                        BehaviorState.HOP: BehaviorState.TROT,
                                        BehaviorState.FINISHHOP: BehaviorState.TROT}
        self.activate_transition_mapping = {BehaviorState.DEACTIVATED: BehaviorState.REST,
                                            BehaviorState.REST: BehaviorState.DEACTIVATED}
        self.imu = imu
        self.rolling_avg_roll = RollingAverage(window=20, initial=0)
        self.rolling_avg_pitch = RollingAverage(window=20, initial=0)
        self.rolling_avg_yaw = RollingAverage(window=20, initial=0)

        self.imu_offsets = offsets

        # Potentially move these values to be set in the config.
        self._controller_roll = PID(4, 0.5, 0,
                                    setpoint=0,
                                    sample_time=0.02,
                                    output_limits=(-self.config.roll_speed, self.config.roll_speed))

        self._controller_pitch = PID(4, 0.5, 0,
                                     setpoint=0,
                                     sample_time=0.02,
                                     output_limits=(-self.config.max_pitch, self.config.max_pitch))

        self._controller_yaw = PID(0.1, 0, 0,
                                   setpoint=0,
                                   sample_time=0.02,
                                   output_limits=(-self.config.max_yaw_rate, self.config.max_yaw_rate))
        
        # self._controller_yaw.error_map = yaw_clip
        
        self._controller_roll(0)
        self._controller_pitch(0)
        self._controller_yaw(0)

        # Roll, yaw
        self._prev_imu = [0, 0]
        self._pid_control = False

        self._prev_time = time.monotonic()
        self.d_state = DesiredState()
        self.pid_control = False


    def step_gait(self, state, yaw_rate, command):
        """Calculate the desired foot locations for the next timestep

        Returns
        -------
        Numpy array (3, 4)
            Matrix of new foot locations.
        """
        contact_modes = self.gait_controller.contacts(state.ticks)
        new_foot_locations = np.zeros((3, 4))
        for leg_index in range(4):
            contact_mode = contact_modes[leg_index]
            foot_location = state.foot_locations[:, leg_index]
            if contact_mode == 1:
                new_location = self.stance_controller.next_foot_location(leg_index, state, yaw_rate, command)
            else:
                swing_proportion = (
                        self.gait_controller.subphase_ticks(state.ticks) / self.config.swing_ticks
                )
                new_location = self.swing_controller.next_foot_location(
                    swing_proportion,
                    leg_index,
                    state,
                    command
                )
            new_foot_locations[:, leg_index] = new_location
        return new_foot_locations, contact_modes

    def handle_commands(self, command, dt):
        if command.pid_control:
            self.toggle_pid_control()

        roll_rate = -np.round(command.roll_command, 2) * self.config.roll_speed
        self.d_state.yaw_rate = np.round(command.yaw_command, 2) * self.config.max_yaw_rate  # rx
        height_rate = np.round(command.height_command, 2) * self.config.z_speed

        self.d_state.height -= height_rate * dt  # Use config next time
        self.d_state.roll += roll_rate * dt
        self.d_state.yaw += self.d_state.yaw_rate * dt

        self.d_state.height = np.clip(self.d_state.height, -0.27, -0.08)
        self.d_state.roll = np.clip(self.d_state.roll, -0.2, 0.2)
        self.d_state.pitch = np.clip(command.pitch_command, -self.config.max_pitch, self.config.max_pitch)
        #self.d_state.yaw = yaw_clip(self.d_state.yaw)

        if command.roll_command:
            self._prev_imu[0] = self.imu.roll
        if command.yaw_command:
            self._prev_imu[1] = self.imu.yaw
        
        if not command.roll_command:
            self.d_state.roll = self._prev_imu[0]
        if not command.yaw_command:
            self.d_state.yaw = self._prev_imu[1]

    def toggle_pid_control(self):
        self.pid_control = not self.pid_control

    @property
    def pid_control(self):
        return self._pid_control

    @pid_control.setter
    def pid_control(self, state):
        if state and not self._pid_control:
            # If setting to true and previous disabled
            self._enable_pid()
        if not state:
            self._disable_pid()
        else:
            pass

    def _disable_pid(self):
        self._controller_roll.auto_mode = False
        self._controller_pitch.auto_mode = False
        self._controller_yaw.auto_mode = False
        self._pid_control = False

    def _enable_pid(self):
        self._controller_roll.set_auto_mode(True, self._controller_roll(0))
        self._controller_pitch.set_auto_mode(True, self._controller_pitch(0))
        self._controller_yaw.set_auto_mode(True, self._controller_yaw(0))
        self._pid_control = True

    def run(self, state, command):

        """Steps the controller forward one timestep

        Parameters
        ----------
        controller : Controller
            Robot controller object.
        """
        dt = time.monotonic() - self._prev_time
        self.handle_commands(command, dt)

        self._controller_roll.setpoint = self.d_state.roll
        self._controller_pitch.setpoint = self.d_state.pitch
        self._controller_yaw.setpoint = self.d_state.yaw
        self.rolling_avg_roll.append(self.imu.roll)
        self.rolling_avg_pitch.append(self.imu.pitch)
        self.rolling_avg_yaw.append(self.imu.yaw)

        if self.pid_control:
            roll_rate = self._controller_roll(self.rolling_avg_roll.average)
            pitch_rate = self._controller_pitch(self.rolling_avg_pitch.average)
            yaw_rate = self._controller_yaw(self.rolling_avg_yaw.average)

            roll = state.roll + roll_rate * dt
            pitch = state.pitch + pitch_rate * dt
            yaw = state.yaw + yaw_rate * dt

            print(f"Roll: {roll_rate:2.4f}-{self.rolling_avg_roll.average:2.4f}-{self.d_state.roll:2.4f}, "
                  f"Pitch: {pitch_rate:2.4f}-{self.rolling_avg_pitch.average:2.4f}-{self.d_state.pitch:2.4f}, "
                  f"Yaw: {yaw_rate:2.4f}-{self.rolling_avg_yaw.average:2.4f}-{self.d_state.yaw:2.4f}", end="\r")

        else:
            roll = self.d_state.roll
            pitch = self.d_state.pitch
            yaw = self.d_state.yaw
            yaw_rate = self.d_state.yaw_rate
            # print(yaw, yaw_rate)
        state.ticks += 1


        previous_state = state.behavior_state

        ########## Update operating state based on command ######
        if command.joystick_control_event:
            state.behavior_state = self.activate_transition_mapping[state.behavior_state]
        elif command.trot_event:
            state.behavior_state = self.trot_transition_mapping[state.behavior_state]
        elif command.hop_event:
            state.behavior_state = self.hop_transition_mapping[state.behavior_state]

        if previous_state != state.behavior_state:
            rospy.loginfo("State changed from %s to %s", str(previous_state), str(state.behavior_state))

        if state.behavior_state == BehaviorState.TROT:
            state.foot_locations, contact_modes = self.step_gait(
                state,
                yaw_rate,
                command,
            )

            # Apply the desired body rotation
            rotated_foot_locations = (
                    euler2mat(
                        self.d_state.roll, self.d_state.pitch, 0.0
                    )
                    @ state.foot_locations
            )

            # Construct foot rotation matrix to compensate for body tilt
            # yaw, pitch, roll = self.imu.yaw, self.imu.pitch, self.imu.roll
            # # print('Yaw: ',np.round(yaw),'Pitch: ',np.round(pitch),'Roll: ',np.round(roll))
            # correction_factor = 0.8
            # max_tilt = 0.4
            # roll_compensation = correction_factor * np.clip(roll, -max_tilt, max_tilt)
            # pitch_compensation = correction_factor * np.clip(pitch, -max_tilt, max_tilt)
            # rmat = euler2mat(roll_compensation, pitch_compensation, 0)

            # rotated_foot_locations = rmat.T @ rotated_foot_locations

            state.joint_angles = self.inverse_kinematics(
                rotated_foot_locations, self.config
            )

            state.rotated_foot_locations = rotated_foot_locations

        elif state.behavior_state == BehaviorState.REST:

            # Set the foot locations to the default stance plus the standard height
            state.foot_locations = (
                    self.config.default_stance
                    + np.array([0, 0, self.d_state.height])[:, np.newaxis]
            )

            self.smoothed_yaw += (
                    self.config.dt *
                    clipped_first_order_filter(
                        self.smoothed_yaw,
                        self.d_state.yaw_rate * -self.config.max_stance_yaw,
                        self.config.max_stance_yaw_rate,
                        self.config.yaw_time_constant,
                    )
            )

            # Apply the desired body rotation
            rotated_foot_locations = (
                    euler2mat(
                        roll,
                        pitch,
                        self.smoothed_yaw,
                    )
                    @ state.foot_locations
            )

            # Construct foot rotation matrix to compensate for body tilt
            # rotated_foot_locations = self.stabilise_with_IMU(rotated_foot_locations)
            # self.stabilise_with_IMU()
            state.joint_angles = self.inverse_kinematics(
                rotated_foot_locations, self.config
            )
            state.rotated_foot_locations = rotated_foot_locations

        state.height = self.d_state.height
        state.roll = roll
        state.pitch = pitch
        state.yaw = yaw

        self._prev_time = time.monotonic()

    def set_pose_to_default(self, state):
        state.foot_locations = (
                self.config.default_stance
                + np.array([0, 0, self.config.default_z_ref])[:, np.newaxis]
        )
        print(state.foot_locations)
        state.joint_angles = self.inverse_kinematics(
            state.foot_locations, self.config
        )
        return state.joint_angles

    def stabilise_with_IMUv2(self):
        # Get imu_stuff from IMU and joint manipulation
        imu_stuff = np.zeros((3, 4))
        self.imu_offsets += imu_stuff

        """
        # PSEUDO CODE:
        Step 1: Get IMU data (roll and pitch)
        Step 2: If pitching up, lower front legs, raise rear legs
        Step 3: If pitching down, raise front legs, lower rear legs
        Step 4: If rolling left, raise left legs, lower right legs
        Step 5: If rolling right, lower left legs, raise right legs
        
        """

    def _adjust_height(self, leg, height_offset):
        # TODO: Adjust height of each leg such that TPU feet is perpendicular to ground.
        upper, lower = self._calc_offsets(leg, height_offset)
        self.imu_offsets[s_idx[leg + "_U"].value] += upper
        self.imu_offsets[s_idx[leg + "_L"].value] += lower
        pass

    def publish_task_space_command(self, rotated_foot_locations):
        pass
        # task_space_message = TaskSpace()
        # task_space_message.FR_foot = Point(rotated_foot_locations[0, 0] - self.config.LEG_ORIGINS[0, 0],
        #                                    rotated_foot_locations[1, 0] - self.config.LEG_ORIGINS[1, 0],
        #                                    rotated_foot_locations[2, 0] - self.config.LEG_ORIGINS[2, 0])
        # task_space_message.FL_foot = Point(rotated_foot_locations[0, 1] - self.config.LEG_ORIGINS[0, 1],
        #                                    rotated_foot_locations[1, 1] - self.config.LEG_ORIGINS[1, 1],
        #                                    rotated_foot_locations[2, 1] - self.config.LEG_ORIGINS[2, 1])
        # task_space_message.RR_foot = Point(rotated_foot_locations[0, 2] - self.config.LEG_ORIGINS[0, 2],
        #                                    rotated_foot_locations[1, 2] - self.config.LEG_ORIGINS[1, 2],
        #                                    rotated_foot_locations[2, 2] - self.config.LEG_ORIGINS[2, 2])
        # task_space_message.RL_foot = Point(rotated_foot_locations[0, 3] - self.config.LEG_ORIGINS[0, 3],
        #                                    rotated_foot_locations[1, 3] - self.config.LEG_ORIGINS[1, 3],
        #                                    rotated_foot_locations[2, 3] - self.config.LEG_ORIGINS[2, 3])
        # task_space_message.header = Header(stamp=rospy.Time.now())
        # self.task_space_pub.publish(task_space_message)

    def publish_joint_space_command(self, angle_matrix):
        pass
        # joint_space_message = JointSpace()
        # joint_space_message.FR_foot = Angle(degrees(angle_matrix[0, 0]), degrees(angle_matrix[1, 0]),
        #                                     degrees(angle_matrix[2, 0]))
        # joint_space_message.FL_foot = Angle(degrees(angle_matrix[0, 1]), degrees(angle_matrix[1, 1]),
        #                                     degrees(angle_matrix[2, 1]))
        # joint_space_message.RR_foot = Angle(degrees(angle_matrix[0, 2]), degrees(angle_matrix[1, 2]),
        #                                     degrees(angle_matrix[2, 2]))
        # joint_space_message.RL_foot = Angle(degrees(angle_matrix[0, 3]), degrees(angle_matrix[1, 3]),
        #                                     degrees(angle_matrix[2, 3]))
        # joint_space_message.header = Header(stamp=rospy.Time.now())
        # self.joint_space_pub.publish(joint_space_message)
