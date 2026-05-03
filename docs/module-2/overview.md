---
sidebar_position: 1
title: "Simulation Overview"
---

# Module 2: The Digital Twin (Gazebo & Unity)

## Introduction to Robot Simulation

Before deploying a robot in the real world, we test it in **simulation**—a virtual environment that mimics physics, sensors, and actuators. This is called creating a **digital twin** of your robot.

**Why simulate?**
- **Safety**: Test dangerous scenarios without risk
- **Cost**: No hardware damage or wear
- **Speed**: Run faster than real-time, test thousands of scenarios
- **Reproducibility**: Exact same conditions every time
- **Early Development**: Start coding before hardware arrives

## The Simulation Stack

```
┌─────────────────────────────────────────────────────┐
│              Robot Development Pipeline             │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Design (CAD) → Simulation → Real Robot            │
│       ↓              ↓              ↓               │
│   URDF/SDF      Gazebo/Unity    Hardware            │
│                                                     │
└─────────────────────────────────────────────────────┘
```

## Gazebo vs Unity: Which to Choose?

### Gazebo

**Gazebo** is the industry-standard robot simulator, tightly integrated with ROS 2.

**Pros**:
- Native ROS 2 integration
- Accurate physics (ODE, Bullet, Simbody engines)
- Large library of robot models
- Free and open-source
- Standard in robotics research

**Cons**:
- Graphics not as polished as Unity
- Steeper learning curve
- Linux-focused (limited Windows support)

**Best for**: Research robots, ROS 2 projects, academic work

### Unity

**Unity** is a game engine adapted for robotics simulation.

**Pros**:
- Photorealistic graphics
- Excellent for computer vision training
- Cross-platform (Windows, Mac, Linux)
- Large asset store
- Easier to learn for beginners

**Cons**:
- ROS 2 integration requires extra setup
- Physics less accurate than Gazebo
- Commercial license for large projects

**Best for**: Vision-based AI, synthetic data generation, demos

### Comparison Table

| Feature | Gazebo | Unity |
|---------|--------|-------|
| **ROS 2 Integration** | Native | Via Unity Robotics Hub |
| **Physics Accuracy** | Excellent | Good |
| **Graphics Quality** | Good | Excellent |
| **Learning Curve** | Steep | Moderate |
| **Cost** | Free | Free (with limits) |
| **Platform** | Linux (primary) | Cross-platform |
| **Use Case** | Research, testing | Vision AI, demos |

## What is Gazebo?

**Gazebo** (also called **Gazebo Classic** or **Ignition Gazebo**) is a 3D robot simulator that provides:

1. **Physics Simulation**: Gravity, collisions, friction, inertia
2. **Sensor Simulation**: Cameras, LiDAR, IMU, GPS
3. **Actuator Simulation**: Motors, servos, grippers
4. **Environment Modeling**: Buildings, terrain, obstacles
5. **ROS 2 Integration**: Seamless communication with ROS 2 nodes

### Gazebo Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Gazebo Simulator                   │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌──────────────┐         ┌──────────────┐        │
│  │   Physics    │◄───────►│   Sensors    │        │
│  │   Engine     │         │   (Camera,   │        │
│  │   (ODE)      │         │   LiDAR)     │        │
│  └──────────────┘         └──────────────┘        │
│         ↕                         ↕                 │
│  ┌──────────────┐         ┌──────────────┐        │
│  │   World      │◄───────►│  Rendering   │        │
│  │   (SDF)      │         │   Engine     │        │
│  └──────────────┘         └──────────────┘        │
│         ↕                         ↕                 │
│  ┌─────────────────────────────────────┐          │
│  │        ROS 2 Bridge (gz_ros2)       │          │
│  └─────────────────────────────────────┘          │
│                     ↕                               │
│              ROS 2 Ecosystem                        │
│                                                     │
└─────────────────────────────────────────────────────┘
```

## Installing Gazebo on Ubuntu 22.04

### Prerequisites

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y \
    wget \
    lsb-release \
    gnupg \
    curl
```

### Install Gazebo Fortress (Recommended for ROS 2 Humble)

```bash
# Add Gazebo repository
sudo wget https://packages.osrfoundation.org/gazebo.gpg \
    -O /usr/share/keyrings/pkgs-osrf-archive-keyring.gpg

echo "deb [arch=$(dpkg --print-architecture) \
    signed-by=/usr/share/keyrings/pkgs-osrf-archive-keyring.gpg] \
    http://packages.osrfoundation.org/gazebo/ubuntu-stable \
    $(lsb_release -cs) main" \
    | sudo tee /etc/apt/sources.list.d/gazebo-stable.list > /dev/null

# Update and install
sudo apt update
sudo apt install -y gz-fortress
```

### Install ROS 2 Gazebo Bridge

```bash
# Install ros_gz packages for ROS 2 Humble
sudo apt install -y \
    ros-humble-ros-gz-bridge \
    ros-humble-ros-gz-sim \
    ros-humble-ros-gz-image
```

### Verify Installation

```bash
# Launch Gazebo
gz sim

# In another terminal, check ROS 2 bridge
ros2 topic list
```

## Your First Gazebo Simulation

### Step 1: Launch Empty World

```bash
# Launch Gazebo with empty world
gz sim empty.sdf
```

You should see an empty 3D environment with a ground plane.

### Step 2: Add a Simple Robot

Create a file `simple_robot.sdf`:

```xml
<?xml version="1.0" ?>
<sdf version="1.8">
  <world name="simple_world">
    
    <!-- Physics -->
    <physics name="1ms" type="ignored">
      <max_step_size>0.001</max_step_size>
      <real_time_factor>1.0</real_time_factor>
    </physics>
    
    <!-- Lighting -->
    <light type="directional" name="sun">
      <cast_shadows>true</cast_shadows>
      <pose>0 0 10 0 0 0</pose>
      <diffuse>0.8 0.8 0.8 1</diffuse>
      <specular>0.2 0.2 0.2 1</specular>
      <direction>-0.5 0.1 -0.9</direction>
    </light>
    
    <!-- Ground plane -->
    <model name="ground_plane">
      <static>true</static>
      <link name="link">
        <collision name="collision">
          <geometry>
            <plane>
              <normal>0 0 1</normal>
            </plane>
          </geometry>
        </collision>
        <visual name="visual">
          <geometry>
            <plane>
              <normal>0 0 1</normal>
              <size>100 100</size>
            </plane>
          </geometry>
          <material>
            <ambient>0.8 0.8 0.8 1</ambient>
            <diffuse>0.8 0.8 0.8 1</diffuse>
          </material>
        </visual>
      </link>
    </model>
    
    <!-- Simple box robot -->
    <model name="box_robot">
      <pose>0 0 0.5 0 0 0</pose>
      
      <link name="chassis">
        <inertial>
          <mass>10.0</mass>
          <inertia>
            <ixx>0.166</ixx>
            <iyy>0.166</iyy>
            <izz>0.166</izz>
          </inertia>
        </inertial>
        
        <collision name="collision">
          <geometry>
            <box>
              <size>1 0.5 0.3</size>
            </box>
          </geometry>
        </collision>
        
        <visual name="visual">
          <geometry>
            <box>
              <size>1 0.5 0.3</size>
            </box>
          </geometry>
          <material>
            <ambient>0.0 0.0 1.0 1</ambient>
            <diffuse>0.0 0.0 1.0 1</diffuse>
          </material>
        </visual>
      </link>
      
    </model>
    
  </world>
</sdf>
```

Launch it:

```bash
gz sim simple_robot.sdf
```

### Step 3: Control the Robot from ROS 2

Create a Python node to control the robot:

```python
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist


class GazeboController(Node):
    """Control a Gazebo robot from ROS 2."""
    
    def __init__(self):
        super().__init__('gazebo_controller')
        
        # Publisher to Gazebo
        self.publisher_ = self.create_publisher(
            Twist,
            '/model/box_robot/cmd_vel',
            10
        )
        
        # Timer for movement
        self.timer = self.create_timer(0.1, self.move_robot)
        self.counter = 0
        
    def move_robot(self):
        """Send movement commands."""
        msg = Twist()
        
        # Move in a square pattern
        phase = (self.counter // 50) % 4
        
        if phase == 0:  # Forward
            msg.linear.x = 0.5
        elif phase == 1:  # Turn left
            msg.angular.z = 0.5
        elif phase == 2:  # Forward
            msg.linear.x = 0.5
        elif phase == 3:  # Turn left
            msg.angular.z = 0.5
            
        self.publisher_.publish(msg)
        self.counter += 1


def main(args=None):
    rclpy.init(args=args)
    controller = GazeboController()
    rclpy.spin(controller)
    controller.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
```

## Understanding SDF Format

**SDF (Simulation Description Format)** is an XML format for describing robots and environments.

### Basic SDF Structure

```xml
<sdf version="1.8">
  <world name="my_world">
    <!-- World contains models -->
    
    <model name="my_robot">
      <!-- Model contains links and joints -->
      
      <link name="base_link">
        <!-- Link contains inertial, collision, visual -->
        
        <inertial>
          <!-- Mass and inertia properties -->
        </inertial>
        
        <collision name="collision">
          <!-- Collision geometry -->
        </collision>
        
        <visual name="visual">
          <!-- Visual appearance -->
        </visual>
        
      </link>
      
      <joint name="joint1" type="revolute">
        <!-- Connects two links -->
      </joint>
      
    </model>
    
  </world>
</sdf>
```

### Key SDF Elements

1. **World**: Top-level container
2. **Model**: A robot or object
3. **Link**: A rigid body (has mass, inertia)
4. **Joint**: Connects two links (revolute, prismatic, fixed)
5. **Collision**: Shape for physics calculations
6. **Visual**: Shape for rendering
7. **Sensor**: Simulated sensor (camera, lidar)
8. **Plugin**: Custom behavior code

## URDF vs SDF

**URDF (Unified Robot Description Format)** is ROS's native format. **SDF** is Gazebo's format.

| Feature | URDF | SDF |
|---------|------|-----|
| **Origin** | ROS | Gazebo |
| **Complexity** | Simpler | More features |
| **Worlds** | No | Yes |
| **Multiple Robots** | No | Yes |
| **Closed Loops** | No | Yes |
| **Preferred for** | ROS 2 | Gazebo |

**Good news**: You can convert between them!

```bash
# URDF to SDF
gz sdf -p robot.urdf > robot.sdf

# Use URDF directly in Gazebo (via plugin)
```

## Gazebo Plugins

Plugins add custom functionality to Gazebo simulations.

### Common Plugins

1. **Differential Drive**: Control wheeled robots
2. **Joint State Publisher**: Publish joint positions
3. **Camera**: Simulate cameras
4. **LiDAR**: Simulate laser scanners
5. **IMU**: Simulate inertial measurement units

### Example: Differential Drive Plugin

```xml
<plugin
  filename="gz-sim-diff-drive-system"
  name="gz::sim::systems::DiffDrive">
  <left_joint>left_wheel_joint</left_joint>
  <right_joint>right_wheel_joint</right_joint>
  <wheel_separation>0.5</wheel_separation>
  <wheel_radius>0.1</wheel_radius>
  <topic>/cmd_vel</topic>
</plugin>
```

## Unity for Robotics

Unity provides the **Unity Robotics Hub** for ROS 2 integration.

### Installing Unity

1. Download **Unity Hub** from [unity.com](https://unity.com/)
2. Install **Unity Editor** (LTS version recommended)
3. Create a new 3D project

### Installing Unity Robotics Hub

```bash
# In Unity, open Package Manager
# Add package from git URL:
https://github.com/Unity-Technologies/ROS-TCP-Connector.git?path=/com.unity.robotics.ros-tcp-connector

# Also add:
https://github.com/Unity-Technologies/URDF-Importer.git?path=/com.unity.robotics.urdf-importer
```

### ROS 2 Bridge Setup

On the ROS 2 side:

```bash
# Install ROS TCP Endpoint
sudo apt install ros-humble-ros-tcp-endpoint

# Run the endpoint
ros2 run ros_tcp_endpoint default_server_endpoint
```

In Unity, configure the ROS connection:
- **Robotics → ROS Settings**
- Set ROS IP Address: `127.0.0.1` (localhost)
- Set ROS Port: `10000`

## Simulation Best Practices

### 1. Start Simple

Begin with basic shapes, add complexity gradually:
```
Box → Box with wheels → Full robot model
```

### 2. Tune Physics Parameters

```xml
<physics name="fast" type="ignored">
  <max_step_size>0.001</max_step_size>  <!-- 1ms timestep -->
  <real_time_factor>1.0</real_time_factor>  <!-- Real-time -->
</physics>
```

### 3. Use Realistic Inertia

Calculate inertia properly for stable simulation:

```python
# For a box: I = (1/12) * m * (h² + d²)
mass = 10.0  # kg
height = 0.5  # m
depth = 0.3  # m
ixx = (1/12) * mass * (height**2 + depth**2)
```

### 4. Validate in Simulation First

Test edge cases in simulation:
- Obstacle collisions
- Sensor failures
- Extreme velocities
- Long-duration runs

## Common Simulation Pitfalls

### 1. Unrealistic Physics

**Problem**: Robot moves too fast or phases through walls

**Solution**: 
- Reduce max velocities
- Increase collision mesh detail
- Tune physics timestep

### 2. Sim-to-Real Gap

**Problem**: Works in simulation, fails on real robot

**Solution**:
- Add sensor noise
- Model actuator delays
- Include friction and slip
- Test in varied environments

### 3. Performance Issues

**Problem**: Simulation runs slowly

**Solution**:
- Simplify collision meshes
- Reduce sensor update rates
- Use level-of-detail (LOD) models
- Run headless (no GUI)

## Summary

- Simulation is essential for safe, fast robot development
- **Gazebo** is the standard for ROS 2 robotics
- **Unity** excels at photorealistic graphics and vision AI
- **SDF** describes robots and worlds in Gazebo
- Plugins add sensors and actuators to simulations
- Always validate in simulation before real-world deployment

## Next Steps

In the next chapters, we'll dive deeper into:
- **Physics simulation**: Gravity, collisions, dynamics
- **Sensor simulation**: Cameras, LiDAR, IMU

## Resources

- [Gazebo Documentation](https://gazebosim.org/docs)
- [Unity Robotics Hub](https://github.com/Unity-Technologies/Unity-Robotics-Hub)
- [SDF Format Specification](http://sdformat.org/)
- [ROS 2 Gazebo Integration](https://github.com/gazebosim/ros_gz)
