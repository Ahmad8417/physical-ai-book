---
sidebar_position: 3
title: "Navigation and SLAM"
---

# Robot Navigation: Finding Your Way

## Introduction

**Navigation** is the ability of a robot to move from point A to point B autonomously. It requires:
- **Localization**: Knowing where you are
- **Mapping**: Understanding the environment
- **Path Planning**: Finding a route
- **Obstacle Avoidance**: Not crashing into things

In this chapter, we'll explore:
- Visual SLAM (Simultaneous Localization and Mapping)
- Nav2 navigation stack
- Path planning algorithms
- Obstacle avoidance for humanoid robots

## The Navigation Problem

```
┌─────────────────────────────────────────────────────┐
│            Robot Navigation Pipeline                │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Sensors → SLAM → Localization → Path Planning     │
│  (Camera,   (Map)   (Pose)        (Trajectory)     │
│   LiDAR)                                            │
│                         ↓                           │
│                  Control → Actuators                │
│                  (Velocity)  (Motors)               │
│                                                     │
└─────────────────────────────────────────────────────┘
```

## Visual SLAM (VSLAM)

**SLAM** = Simultaneous Localization and Mapping

The robot must:
1. Build a map of the environment
2. Localize itself within that map
3. Do both at the same time (chicken-and-egg problem!)

### Types of SLAM

| Type | Sensors | Pros | Cons |
|------|---------|------|------|
| **Visual SLAM** | Cameras | Rich features, cheap | Lighting sensitive |
| **LiDAR SLAM** | LiDAR | Accurate, robust | Expensive, heavy |
| **RGB-D SLAM** | Depth camera | 3D mapping | Limited range |
| **Visual-Inertial** | Camera + IMU | Robust, fast | Complex fusion |

## Isaac ROS Visual SLAM

NVIDIA provides GPU-accelerated VSLAM for ROS 2.

### Installing Isaac ROS

```bash
# Install dependencies
sudo apt install -y \
    ros-humble-isaac-ros-visual-slam \
    ros-humble-isaac-ros-nvblox

# Or build from source
mkdir -p ~/isaac_ros_ws/src
cd ~/isaac_ros_ws/src

git clone https://github.com/NVIDIA-ISAAC-ROS/isaac_ros_visual_slam.git
git clone https://github.com/NVIDIA-ISAAC-ROS/isaac_ros_common.git

cd ~/isaac_ros_ws
colcon build --symlink-install
source install/setup.bash
```

### Running Visual SLAM

```bash
# Launch Isaac ROS Visual SLAM
ros2 launch isaac_ros_visual_slam isaac_ros_visual_slam.launch.py

# In another terminal, play a rosbag with camera data
ros2 bag play my_robot_data.bag
```

### Visual SLAM Node Configuration

```python
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, CameraInfo
from nav_msgs.msg import Odometry
from geometry_msgs.msg import PoseStamped


class VisualSLAMNode(Node):
    """Interface with Isaac ROS Visual SLAM."""
    
    def __init__(self):
        super().__init__('visual_slam_interface')
        
        # Subscribe to SLAM outputs
        self.pose_sub = self.create_subscription(
            PoseStamped,
            '/visual_slam/tracking/vo_pose',
            self.pose_callback,
            10
        )
        
        self.odom_sub = self.create_subscription(
            Odometry,
            '/visual_slam/tracking/odometry',
            self.odom_callback,
            10
        )
        
        # Current pose
        self.current_pose = None
        
        self.get_logger().info('Visual SLAM interface started')
        
    def pose_callback(self, msg):
        """Receive robot pose from SLAM."""
        self.current_pose = msg.pose
        
        self.get_logger().debug(
            f'Pose: x={msg.pose.position.x:.2f}, '
            f'y={msg.pose.position.y:.2f}, '
            f'z={msg.pose.position.z:.2f}'
        )
    
    def odom_callback(self, msg):
        """Receive odometry from SLAM."""
        linear_vel = msg.twist.twist.linear
        angular_vel = msg.twist.twist.angular
        
        self.get_logger().debug(
            f'Velocity: linear={linear_vel.x:.2f} m/s, '
            f'angular={angular_vel.z:.2f} rad/s'
        )
    
    def get_current_position(self):
        """Get current robot position."""
        if self.current_pose:
            return (
                self.current_pose.position.x,
                self.current_pose.position.y,
                self.current_pose.position.z
            )
        return None


def main(args=None):
    rclpy.init(args=args)
    node = VisualSLAMNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
```

## Nav2 Navigation Stack

**Nav2** is the ROS 2 navigation framework. It provides:
- Global path planning
- Local trajectory planning
- Costmap generation
- Recovery behaviors
- Waypoint following

### Nav2 Architecture

```
┌─────────────────────────────────────────────────────┐
│              Nav2 Architecture                      │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Goal → Planner Server → Controller Server → Robot │
│           (Global path)    (Local trajectory)       │
│                ↑                  ↑                 │
│         Costmap 2D         Costmap 2D              │
│         (Global)           (Local)                  │
│                ↑                  ↑                 │
│         Sensor Data (LiDAR, Camera, etc.)          │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Installing Nav2

```bash
# Install Nav2
sudo apt install ros-humble-navigation2 ros-humble-nav2-bringup

# Install visualization tools
sudo apt install ros-humble-rviz2
```

### Nav2 Configuration

Create `nav2_params.yaml`:

```yaml
bt_navigator:
  ros__parameters:
    use_sim_time: True
    global_frame: map
    robot_base_frame: base_link
    odom_topic: /odom
    bt_loop_duration: 10
    default_server_timeout: 20

controller_server:
  ros__parameters:
    use_sim_time: True
    controller_frequency: 20.0
    min_x_velocity_threshold: 0.001
    min_y_velocity_threshold: 0.5
    min_theta_velocity_threshold: 0.001
    progress_checker_plugin: "progress_checker"
    goal_checker_plugins: ["general_goal_checker"]
    controller_plugins: ["FollowPath"]
    
    FollowPath:
      plugin: "dwb_core::DWBLocalPlanner"
      min_vel_x: 0.0
      min_vel_y: 0.0
      max_vel_x: 0.5
      max_vel_y: 0.0
      max_vel_theta: 1.0
      min_speed_xy: 0.0
      max_speed_xy: 0.5
      min_speed_theta: 0.0
      acc_lim_x: 2.5
      acc_lim_y: 0.0
      acc_lim_theta: 3.2
      decel_lim_x: -2.5
      decel_lim_y: 0.0
      decel_lim_theta: -3.2

planner_server:
  ros__parameters:
    use_sim_time: True
    planner_plugins: ["GridBased"]
    GridBased:
      plugin: "nav2_navfn_planner/NavfnPlanner"
      tolerance: 0.5
      use_astar: false
      allow_unknown: true

local_costmap:
  local_costmap:
    ros__parameters:
      update_frequency: 5.0
      publish_frequency: 2.0
      global_frame: odom
      robot_base_frame: base_link
      use_sim_time: True
      rolling_window: true
      width: 3
      height: 3
      resolution: 0.05

global_costmap:
  global_costmap:
    ros__parameters:
      update_frequency: 1.0
      publish_frequency: 1.0
      global_frame: map
      robot_base_frame: base_link
      use_sim_time: True
      robot_radius: 0.3
      resolution: 0.05
      track_unknown_space: true
```

### Launching Nav2

```bash
# Launch Nav2 with your configuration
ros2 launch nav2_bringup navigation_launch.py \
  params_file:=/path/to/nav2_params.yaml
```

### Sending Navigation Goals

```python
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator
import math


class NavigationCommander(Node):
    """Send navigation goals to Nav2."""
    
    def __init__(self):
        super().__init__('navigation_commander')
        
        # Create navigator
        self.navigator = BasicNavigator()
        
        # Wait for Nav2 to be ready
        self.navigator.waitUntilNav2Active()
        
        self.get_logger().info('Nav2 is active!')
        
    def create_pose(self, x, y, theta):
        """Create a PoseStamped message."""
        pose = PoseStamped()
        pose.header.frame_id = 'map'
        pose.header.stamp = self.navigator.get_clock().now().to_msg()
        
        pose.pose.position.x = x
        pose.pose.position.y = y
        pose.pose.position.z = 0.0
        
        # Convert theta to quaternion
        pose.pose.orientation.z = math.sin(theta / 2.0)
        pose.pose.orientation.w = math.cos(theta / 2.0)
        
        return pose
    
    def go_to_pose(self, x, y, theta):
        """Navigate to a specific pose."""
        goal_pose = self.create_pose(x, y, theta)
        
        self.get_logger().info(f'Navigating to: x={x}, y={y}, theta={theta}')
        
        # Send goal
        self.navigator.goToPose(goal_pose)
        
        # Wait for completion
        while not self.navigator.isTaskComplete():
            feedback = self.navigator.getFeedback()
            if feedback:
                distance = feedback.distance_remaining
                self.get_logger().info(f'Distance remaining: {distance:.2f}m')
            
            rclpy.spin_once(self, timeout_sec=0.1)
        
        # Check result
        result = self.navigator.getResult()
        if result == BasicNavigator.TaskResult.SUCCEEDED:
            self.get_logger().info('Goal reached!')
            return True
        else:
            self.get_logger().warn('Navigation failed!')
            return False
    
    def follow_waypoints(self, waypoints):
        """Follow a sequence of waypoints."""
        poses = [self.create_pose(x, y, theta) for x, y, theta in waypoints]
        
        self.get_logger().info(f'Following {len(poses)} waypoints')
        
        self.navigator.followWaypoints(poses)
        
        while not self.navigator.isTaskComplete():
            feedback = self.navigator.getFeedback()
            if feedback:
                current_waypoint = feedback.current_waypoint
                self.get_logger().info(
                    f'Waypoint {current_waypoint}/{len(poses)}'
                )
            
            rclpy.spin_once(self, timeout_sec=0.1)
        
        result = self.navigator.getResult()
        return result == BasicNavigator.TaskResult.SUCCEEDED


def main(args=None):
    rclpy.init(args=args)
    commander = NavigationCommander()
    
    # Example: Navigate to kitchen
    commander.go_to_pose(x=5.0, y=3.0, theta=0.0)
    
    # Example: Patrol waypoints
    waypoints = [
        (2.0, 2.0, 0.0),
        (5.0, 2.0, 1.57),
        (5.0, 5.0, 3.14),
        (2.0, 5.0, -1.57)
    ]
    commander.follow_waypoints(waypoints)
    
    commander.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
```

## Path Planning Algorithms

### A* (A-Star) Algorithm

Classic grid-based path planning:

```python
import heapq
import numpy as np


class AStarPlanner:
    """A* path planning algorithm."""
    
    def __init__(self, grid, start, goal):
        """
        Args:
            grid: 2D numpy array (0=free, 1=obstacle)
            start: (x, y) tuple
            goal: (x, y) tuple
        """
        self.grid = grid
        self.start = start
        self.goal = goal
        self.height, self.width = grid.shape
        
    def heuristic(self, pos):
        """Euclidean distance heuristic."""
        return np.sqrt(
            (pos[0] - self.goal[0])**2 +
            (pos[1] - self.goal[1])**2
        )
    
    def get_neighbors(self, pos):
        """Get valid neighboring cells."""
        x, y = pos
        neighbors = []
        
        # 8-connected grid
        for dx, dy in [(-1,-1), (-1,0), (-1,1), (0,-1), 
                       (0,1), (1,-1), (1,0), (1,1)]:
            nx, ny = x + dx, y + dy
            
            # Check bounds
            if 0 <= nx < self.width and 0 <= ny < self.height:
                # Check if free
                if self.grid[ny, nx] == 0:
                    neighbors.append((nx, ny))
        
        return neighbors
    
    def plan(self):
        """Find path from start to goal."""
        # Priority queue: (f_score, g_score, position)
        open_set = [(self.heuristic(self.start), 0, self.start)]
        came_from = {}
        g_score = {self.start: 0}
        
        while open_set:
            _, current_g, current = heapq.heappop(open_set)
            
            # Goal reached
            if current == self.goal:
                return self.reconstruct_path(came_from, current)
            
            # Explore neighbors
            for neighbor in self.get_neighbors(current):
                tentative_g = current_g + 1
                
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score = tentative_g + self.heuristic(neighbor)
                    heapq.heappush(open_set, (f_score, tentative_g, neighbor))
        
        # No path found
        return None
    
    def reconstruct_path(self, came_from, current):
        """Reconstruct path from goal to start."""
        path = [current]
        while current in came_from:
            current = came_from[current]
            path.append(current)
        path.reverse()
        return path


# Example usage
grid = np.zeros((100, 100))
grid[40:60, 40:60] = 1  # Obstacle

planner = AStarPlanner(grid, start=(10, 10), goal=(90, 90))
path = planner.plan()

if path:
    print(f"Path found with {len(path)} waypoints")
else:
    print("No path found")
```

### RRT (Rapidly-exploring Random Tree)

For high-dimensional spaces:

```python
import numpy as np
import random


class RRTPlanner:
    """RRT path planning algorithm."""
    
    def __init__(self, start, goal, obstacles, bounds, step_size=0.5):
        self.start = np.array(start)
        self.goal = np.array(goal)
        self.obstacles = obstacles  # List of (center, radius) tuples
        self.bounds = bounds  # (min_x, max_x, min_y, max_y)
        self.step_size = step_size
        
        self.tree = {tuple(self.start): None}
        
    def sample_random_point(self):
        """Sample a random point in the space."""
        # 10% chance to sample goal (goal bias)
        if random.random() < 0.1:
            return self.goal
        
        x = random.uniform(self.bounds[0], self.bounds[1])
        y = random.uniform(self.bounds[2], self.bounds[3])
        return np.array([x, y])
    
    def nearest_node(self, point):
        """Find nearest node in tree to point."""
        min_dist = float('inf')
        nearest = None
        
        for node in self.tree.keys():
            dist = np.linalg.norm(np.array(node) - point)
            if dist < min_dist:
                min_dist = dist
                nearest = node
        
        return np.array(nearest)
    
    def steer(self, from_node, to_point):
        """Steer from node towards point by step_size."""
        direction = to_point - from_node
        distance = np.linalg.norm(direction)
        
        if distance < self.step_size:
            return to_point
        
        direction = direction / distance
        return from_node + direction * self.step_size
    
    def is_collision_free(self, from_point, to_point):
        """Check if path segment is collision-free."""
        # Check multiple points along the segment
        num_checks = int(np.linalg.norm(to_point - from_point) / 0.1)
        
        for i in range(num_checks + 1):
            t = i / max(num_checks, 1)
            point = from_point + t * (to_point - from_point)
            
            # Check against obstacles
            for obs_center, obs_radius in self.obstacles:
                if np.linalg.norm(point - obs_center) < obs_radius:
                    return False
        
        return True
    
    def plan(self, max_iterations=5000):
        """Find path using RRT."""
        for i in range(max_iterations):
            # Sample random point
            random_point = self.sample_random_point()
            
            # Find nearest node
            nearest = self.nearest_node(random_point)
            
            # Steer towards random point
            new_point = self.steer(nearest, random_point)
            
            # Check collision
            if self.is_collision_free(nearest, new_point):
                # Add to tree
                self.tree[tuple(new_point)] = tuple(nearest)
                
                # Check if goal reached
                if np.linalg.norm(new_point - self.goal) < self.step_size:
                    self.tree[tuple(self.goal)] = tuple(new_point)
                    return self.extract_path()
        
        return None
    
    def extract_path(self):
        """Extract path from tree."""
        path = [self.goal]
        current = tuple(self.goal)
        
        while current is not None:
            path.append(np.array(current))
            current = self.tree[current]
        
        path.reverse()
        return path


# Example usage
obstacles = [
    (np.array([5, 5]), 1.0),
    (np.array([7, 3]), 0.8),
    (np.array([3, 7]), 1.2)
]

planner = RRTPlanner(
    start=[0, 0],
    goal=[10, 10],
    obstacles=obstacles,
    bounds=(0, 10, 0, 10)
)

path = planner.plan()
if path:
    print(f"Path found with {len(path)} waypoints")
```

## Obstacle Avoidance

### Dynamic Window Approach (DWA)

Real-time local obstacle avoidance:

```python
import numpy as np


class DWAPlanner:
    """Dynamic Window Approach for local planning."""
    
    def __init__(self, config):
        self.max_speed = config['max_speed']
        self.min_speed = config['min_speed']
        self.max_yaw_rate = config['max_yaw_rate']
        self.max_accel = config['max_accel']
        self.max_delta_yaw_rate = config['max_delta_yaw_rate']
        self.v_resolution = config['v_resolution']
        self.yaw_rate_resolution = config['yaw_rate_resolution']
        self.dt = config['dt']
        self.predict_time = config['predict_time']
        self.robot_radius = config['robot_radius']
        
    def calc_dynamic_window(self, current_v, current_yaw_rate):
        """Calculate dynamic window based on current velocity."""
        # Velocity limits
        vs = [
            self.min_speed,
            self.max_speed,
            -self.max_yaw_rate,
            self.max_yaw_rate
        ]
        
        # Dynamic window based on acceleration limits
        vd = [
            current_v - self.max_accel * self.dt,
            current_v + self.max_accel * self.dt,
            current_yaw_rate - self.max_delta_yaw_rate * self.dt,
            current_yaw_rate + self.max_delta_yaw_rate * self.dt
        ]
        
        # Intersection
        dw = [
            max(vs[0], vd[0]),
            min(vs[1], vd[1]),
            max(vs[2], vd[2]),
            min(vs[3], vd[3])
        ]
        
        return dw
    
    def predict_trajectory(self, x, y, theta, v, yaw_rate):
        """Predict robot trajectory."""
        trajectory = [[x, y, theta, v, yaw_rate]]
        time = 0
        
        while time <= self.predict_time:
            x += v * np.cos(theta) * self.dt
            y += v * np.sin(theta) * self.dt
            theta += yaw_rate * self.dt
            time += self.dt
            
            trajectory.append([x, y, theta, v, yaw_rate])
        
        return np.array(trajectory)
    
    def calc_obstacle_cost(self, trajectory, obstacles):
        """Calculate cost based on obstacles."""
        min_dist = float('inf')
        
        for point in trajectory:
            for obs in obstacles:
                dist = np.linalg.norm(point[:2] - obs[:2]) - self.robot_radius
                if dist < min_dist:
                    min_dist = dist
        
        # Collision
        if min_dist < 0:
            return float('inf')
        
        # Cost inversely proportional to distance
        return 1.0 / min_dist
    
    def calc_to_goal_cost(self, trajectory, goal):
        """Calculate cost to reach goal."""
        final_pos = trajectory[-1][:2]
        return np.linalg.norm(final_pos - goal)
    
    def plan(self, state, goal, obstacles):
        """
        Plan velocity command.
        
        Args:
            state: [x, y, theta, v, yaw_rate]
            goal: [x, y]
            obstacles: List of [x, y, radius]
        
        Returns:
            [v, yaw_rate]: Velocity command
        """
        x, y, theta, v, yaw_rate = state
        
        dw = self.calc_dynamic_window(v, yaw_rate)
        
        best_v = 0
        best_yaw_rate = 0
        min_cost = float('inf')
        
        # Sample velocities in dynamic window
        for sample_v in np.arange(dw[0], dw[1], self.v_resolution):
            for sample_yaw_rate in np.arange(dw[2], dw[3], self.yaw_rate_resolution):
                # Predict trajectory
                trajectory = self.predict_trajectory(
                    x, y, theta, sample_v, sample_yaw_rate
                )
                
                # Calculate costs
                obs_cost = self.calc_obstacle_cost(trajectory, obstacles)
                goal_cost = self.calc_to_goal_cost(trajectory, goal)
                
                # Total cost
                total_cost = obs_cost + goal_cost
                
                # Update best
                if total_cost < min_cost:
                    min_cost = total_cost
                    best_v = sample_v
                    best_yaw_rate = sample_yaw_rate
        
        return [best_v, best_yaw_rate]


# Example usage
config = {
    'max_speed': 1.0,
    'min_speed': 0.0,
    'max_yaw_rate': 1.0,
    'max_accel': 0.5,
    'max_delta_yaw_rate': 1.0,
    'v_resolution': 0.1,
    'yaw_rate_resolution': 0.1,
    'dt': 0.1,
    'predict_time': 3.0,
    'robot_radius': 0.3
}

planner = DWAPlanner(config)

# Current state: [x, y, theta, v, yaw_rate]
state = [0, 0, 0, 0.5, 0]
goal = [10, 10]
obstacles = [[5, 5, 1.0], [7, 3, 0.8]]

cmd = planner.plan(state, goal, obstacles)
print(f"Command: v={cmd[0]:.2f} m/s, yaw_rate={cmd[1]:.2f} rad/s")
```

## Humanoid-Specific Navigation

Humanoid robots have unique challenges:
- **Bipedal locomotion**: Balance and stability
- **Footstep planning**: Where to place feet
- **Whole-body motion**: Coordinating arms and legs

### Footstep Planner

```python
class FootstepPlanner:
    """Plan footsteps for humanoid robot."""
    
    def __init__(self, step_length=0.3, step_width=0.2):
        self.step_length = step_length
        self.step_width = step_width
        
    def plan_footsteps(self, start_pose, goal_pose):
        """
        Plan sequence of footsteps.
        
        Args:
            start_pose: [x, y, theta]
            goal_pose: [x, y, theta]
        
        Returns:
            List of footsteps: [(x, y, theta, foot), ...]
            foot: 'left' or 'right'
        """
        footsteps = []
        
        current_x, current_y, current_theta = start_pose
        goal_x, goal_y, goal_theta = goal_pose
        
        # Calculate distance to goal
        distance = np.sqrt(
            (goal_x - current_x)**2 +
            (goal_y - current_y)**2
        )
        
        # Calculate direction to goal
        direction = np.arctan2(
            goal_y - current_y,
            goal_x - current_x
        )
        
        # Number of steps needed
        num_steps = int(distance / self.step_length) + 1
        
        # Alternate feet
        foot = 'left'
        
        for i in range(num_steps):
            # Calculate step position
            step_x = current_x + i * self.step_length * np.cos(direction)
            step_y = current_y + i * self.step_length * np.sin(direction)
            
            # Offset for left/right foot
            offset = self.step_width / 2 if foot == 'left' else -self.step_width / 2
            step_y += offset * np.cos(direction + np.pi/2)
            step_x += offset * np.sin(direction + np.pi/2)
            
            footsteps.append((step_x, step_y, direction, foot))
            
            # Alternate foot
            foot = 'right' if foot == 'left' else 'left'
        
        return footsteps
```

## Summary

- **Visual SLAM** enables robots to map and localize simultaneously
- **Isaac ROS** provides GPU-accelerated SLAM and perception
- **Nav2** is the standard ROS 2 navigation stack
- **A*** and **RRT** are common path planning algorithms
- **DWA** enables real-time obstacle avoidance
- **Humanoid navigation** requires footstep planning and balance control

## Next Steps

In Module 4, we'll integrate Vision-Language-Action models to enable natural language control of robots.

## Resources

- [Nav2 Documentation](https://navigation.ros.org/)
- [Isaac ROS Visual SLAM](https://nvidia-isaac-ros.github.io/repositories_and_packages/isaac_ros_visual_slam/)
- [ORB-SLAM3](https://github.com/UZ-SLAMLab/ORB_SLAM3)
- [Path Planning Algorithms](https://github.com/zhm-real/PathPlanning)
