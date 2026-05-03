---
sidebar_position: 2
title: "Physics Simulation"
---

# Physics Simulation: Making Virtual Robots Real

## Introduction

Physics simulation is what makes virtual robots behave like real ones. Without accurate physics, your robot would float through walls, ignore gravity, and behave unpredictably.

In this chapter, we'll explore:
- How physics engines work
- Gravity, collisions, and friction
- Rigid body dynamics
- Creating realistic robot environments
- URDF and SDF formats in depth

## How Physics Engines Work

A **physics engine** calculates how objects move and interact based on physical laws.

### The Simulation Loop

```
┌─────────────────────────────────────────────────┐
│         Physics Simulation Loop                 │
├─────────────────────────────────────────────────┤
│                                                 │
│  1. Read current state (positions, velocities) │
│           ↓                                     │
│  2. Apply forces (gravity, motors, collisions) │
│           ↓                                     │
│  3. Integrate equations of motion              │
│           ↓                                     │
│  4. Detect and resolve collisions              │
│           ↓                                     │
│  5. Update state (new positions, velocities)   │
│           ↓                                     │
│  6. Render frame                                │
│           ↓                                     │
│  [Repeat at fixed timestep, e.g., 1ms]         │
│                                                 │
└─────────────────────────────────────────────────┘
```

### Physics Engines in Gazebo

Gazebo supports multiple physics engines:

1. **ODE (Open Dynamics Engine)**: Default, fast, stable
2. **Bullet**: Good for complex collisions
3. **DART**: Advanced constraints and contacts
4. **Simbody**: High-fidelity biomechanics

**Most common**: ODE for general robotics

## Fundamental Physics Concepts

### 1. Gravity

Gravity pulls objects downward with acceleration **g = 9.81 m/s²**.

In SDF:

```xml
<world name="my_world">
  <gravity>0 0 -9.81</gravity>
  <!-- Negative Z is downward -->
</world>
```

**Custom gravity** (e.g., Moon simulation):

```xml
<gravity>0 0 -1.62</gravity>  <!-- Moon: 1.62 m/s² -->
```

### 2. Mass and Inertia

Every link needs **mass** and **inertia tensor**.

**Mass**: How much matter (kg)
**Inertia**: Resistance to rotation (kg⋅m²)

```xml
<link name="chassis">
  <inertial>
    <mass>15.0</mass>  <!-- 15 kg -->
    <inertia>
      <ixx>0.5</ixx>  <!-- Inertia around X axis -->
      <iyy>0.8</iyy>  <!-- Inertia around Y axis -->
      <izz>1.0</izz>  <!-- Inertia around Z axis -->
      <ixy>0</ixy>    <!-- Cross terms (usually 0) -->
      <ixz>0</ixz>
      <iyz>0</iyz>
    </inertia>
  </inertial>
</link>
```

### Calculating Inertia

For common shapes:

**Box** (width w, height h, depth d):
```
Ixx = (1/12) * m * (h² + d²)
Iyy = (1/12) * m * (w² + d²)
Izz = (1/12) * m * (w² + h²)
```

**Cylinder** (radius r, height h):
```
Ixx = Iyy = (1/12) * m * (3r² + h²)
Izz = (1/2) * m * r²
```

**Sphere** (radius r):
```
Ixx = Iyy = Izz = (2/5) * m * r²
```

Python helper:

```python
def box_inertia(mass, width, height, depth):
    """Calculate inertia tensor for a box."""
    ixx = (1/12) * mass * (height**2 + depth**2)
    iyy = (1/12) * mass * (width**2 + depth**2)
    izz = (1/12) * mass * (width**2 + height**2)
    return ixx, iyy, izz

# Example
mass = 10.0  # kg
w, h, d = 1.0, 0.5, 0.3  # meters
ixx, iyy, izz = box_inertia(mass, w, h, d)
print(f"Ixx={ixx:.3f}, Iyy={iyy:.3f}, Izz={izz:.3f}")
```

### 3. Friction

Friction opposes motion between surfaces.

**Types**:
- **Static friction**: Prevents initial motion
- **Kinetic friction**: Opposes sliding motion

In SDF:

```xml
<collision name="collision">
  <geometry>
    <box><size>1 1 1</size></box>
  </geometry>
  <surface>
    <friction>
      <ode>
        <mu>0.8</mu>   <!-- Coefficient of friction -->
        <mu2>0.8</mu2> <!-- Secondary direction -->
      </ode>
    </friction>
  </surface>
</collision>
```

**Friction coefficients**:
- Rubber on concrete: 0.7-1.0
- Metal on metal: 0.15-0.25
- Ice on ice: 0.02-0.05

### 4. Collisions

Collision detection prevents objects from passing through each other.

**Collision geometry** should be **simpler** than visual geometry for performance:

```xml
<!-- Visual: detailed mesh -->
<visual name="visual">
  <geometry>
    <mesh><uri>model://robot/meshes/chassis.dae</uri></mesh>
  </geometry>
</visual>

<!-- Collision: simple box -->
<collision name="collision">
  <geometry>
    <box><size>1 0.5 0.3</size></box>
  </geometry>
</collision>
```

### 5. Damping

Damping simulates energy loss (air resistance, internal friction).

```xml
<link name="arm">
  <inertial>
    <mass>2.0</mass>
    <!-- ... -->
  </inertial>
  
  <!-- Damping -->
  <velocity_decay>
    <linear>0.01</linear>   <!-- Linear damping -->
    <angular>0.05</angular> <!-- Angular damping -->
  </velocity_decay>
</link>
```

## Creating a Complete Robot Model

Let's build a differential drive robot (two wheels + caster).

### Step 1: Define the Chassis

```xml
<?xml version="1.0"?>
<sdf version="1.8">
  <model name="diff_drive_robot">
    
    <!-- Chassis link -->
    <link name="chassis">
      <pose>0 0 0.1 0 0 0</pose>
      
      <inertial>
        <mass>10.0</mass>
        <inertia>
          <ixx>0.166</ixx>
          <iyy>0.416</iyy>
          <izz>0.5</izz>
        </inertia>
      </inertial>
      
      <collision name="collision">
        <geometry>
          <box>
            <size>0.6 0.4 0.2</size>
          </box>
        </geometry>
      </collision>
      
      <visual name="visual">
        <geometry>
          <box>
            <size>0.6 0.4 0.2</size>
          </box>
        </geometry>
        <material>
          <ambient>0.2 0.2 0.8 1</ambient>
          <diffuse>0.2 0.2 0.8 1</diffuse>
        </material>
      </visual>
    </link>
```

### Step 2: Add Wheels

```xml
    <!-- Left wheel -->
    <link name="left_wheel">
      <pose>0 0.25 0.1 -1.5707 0 0</pose>  <!-- Rotated 90° -->
      
      <inertial>
        <mass>1.0</mass>
        <inertia>
          <ixx>0.0025</ixx>
          <iyy>0.0025</iyy>
          <izz>0.005</izz>
        </inertia>
      </inertial>
      
      <collision name="collision">
        <geometry>
          <cylinder>
            <radius>0.1</radius>
            <length>0.05</length>
          </cylinder>
        </geometry>
        <surface>
          <friction>
            <ode>
              <mu>1.0</mu>  <!-- High friction for traction -->
              <mu2>1.0</mu2>
            </ode>
          </friction>
        </surface>
      </collision>
      
      <visual name="visual">
        <geometry>
          <cylinder>
            <radius>0.1</radius>
            <length>0.05</length>
          </cylinder>
        </geometry>
        <material>
          <ambient>0.1 0.1 0.1 1</ambient>
          <diffuse>0.1 0.1 0.1 1</diffuse>
        </material>
      </visual>
    </link>
    
    <!-- Right wheel (mirror of left) -->
    <link name="right_wheel">
      <pose>0 -0.25 0.1 -1.5707 0 0</pose>
      <!-- Same as left wheel but mirrored -->
      <!-- ... (inertial, collision, visual) ... -->
    </link>
```

### Step 3: Add Joints

```xml
    <!-- Left wheel joint -->
    <joint name="left_wheel_joint" type="revolute">
      <parent>chassis</parent>
      <child>left_wheel</child>
      <axis>
        <xyz>0 0 1</xyz>  <!-- Rotation axis -->
        <limit>
          <lower>-1e16</lower>  <!-- Unlimited rotation -->
          <upper>1e16</upper>
        </limit>
      </axis>
    </joint>
    
    <!-- Right wheel joint -->
    <joint name="right_wheel_joint" type="revolute">
      <parent>chassis</parent>
      <child>right_wheel</child>
      <axis>
        <xyz>0 0 1</xyz>
      </axis>
    </joint>
```

### Step 4: Add Caster Wheel

```xml
    <!-- Caster (passive wheel) -->
    <link name="caster">
      <pose>-0.25 0 0.05 0 0 0</pose>
      
      <inertial>
        <mass>0.5</mass>
        <inertia>
          <ixx>0.0001</ixx>
          <iyy>0.0001</iyy>
          <izz>0.0001</izz>
        </inertia>
      </inertial>
      
      <collision name="collision">
        <geometry>
          <sphere>
            <radius>0.05</radius>
          </sphere>
        </geometry>
        <surface>
          <friction>
            <ode>
              <mu>0.1</mu>  <!-- Low friction for easy turning -->
              <mu2>0.1</mu2>
            </ode>
          </friction>
        </surface>
      </collision>
      
      <visual name="visual">
        <geometry>
          <sphere>
            <radius>0.05</radius>
          </sphere>
        </geometry>
        <material>
          <ambient>0.5 0.5 0.5 1</ambient>
        </material>
      </visual>
    </link>
    
    <!-- Caster joint (fixed to chassis) -->
    <joint name="caster_joint" type="fixed">
      <parent>chassis</parent>
      <child>caster</child>
    </joint>
```

### Step 5: Add Differential Drive Plugin

```xml
    <!-- Differential drive controller -->
    <plugin
      filename="gz-sim-diff-drive-system"
      name="gz::sim::systems::DiffDrive">
      <left_joint>left_wheel_joint</left_joint>
      <right_joint>right_wheel_joint</right_joint>
      <wheel_separation>0.5</wheel_separation>
      <wheel_radius>0.1</wheel_radius>
      <odom_publish_frequency>50</odom_publish_frequency>
      <topic>cmd_vel</topic>
      <odom_topic>odom</odom_topic>
      <frame_id>odom</frame_id>
      <child_frame_id>chassis</child_frame_id>
    </plugin>
    
  </model>
</sdf>
```

## URDF Format Deep Dive

**URDF (Unified Robot Description Format)** is ROS's native format.

### Basic URDF Structure

```xml
<?xml version="1.0"?>
<robot name="my_robot">
  
  <!-- Links -->
  <link name="base_link">
    <visual>
      <geometry>
        <box size="1 0.5 0.3"/>
      </geometry>
      <material name="blue">
        <color rgba="0 0 1 1"/>
      </material>
    </visual>
    
    <collision>
      <geometry>
        <box size="1 0.5 0.3"/>
      </geometry>
    </collision>
    
    <inertial>
      <mass value="10.0"/>
      <inertia ixx="0.166" iyy="0.416" izz="0.5"
               ixy="0" ixz="0" iyz="0"/>
    </inertial>
  </link>
  
  <!-- Joints -->
  <joint name="wheel_joint" type="continuous">
    <parent link="base_link"/>
    <child link="wheel_link"/>
    <origin xyz="0 0.25 0" rpy="0 0 0"/>
    <axis xyz="0 0 1"/>
  </joint>
  
  <link name="wheel_link">
    <!-- ... -->
  </link>
  
</robot>
```

### URDF Joint Types

1. **fixed**: No movement (welded together)
2. **revolute**: Rotation with limits
3. **continuous**: Unlimited rotation (wheels)
4. **prismatic**: Linear sliding (elevator)
5. **floating**: 6 DOF (free-flying)
6. **planar**: 2D motion in a plane

### Using URDF with Gazebo

Add Gazebo-specific tags:

```xml
<robot name="my_robot">
  
  <link name="base_link">
    <!-- Standard URDF -->
  </link>
  
  <!-- Gazebo-specific properties -->
  <gazebo reference="base_link">
    <material>Gazebo/Blue</material>
    <mu1>0.8</mu1>  <!-- Friction -->
    <mu2>0.8</mu2>
  </gazebo>
  
  <!-- Gazebo plugins -->
  <gazebo>
    <plugin name="diff_drive" filename="libgazebo_ros_diff_drive.so">
      <left_joint>left_wheel_joint</left_joint>
      <right_joint>right_wheel_joint</right_joint>
      <wheel_separation>0.5</wheel_separation>
      <wheel_diameter>0.2</wheel_diameter>
      <command_topic>cmd_vel</command_topic>
      <odometry_topic>odom</odometry_topic>
    </plugin>
  </gazebo>
  
</robot>
```

## Creating Realistic Environments

### Building a Test Arena

```xml
<sdf version="1.8">
  <world name="test_arena">
    
    <!-- Physics -->
    <physics name="default_physics" type="ode">
      <max_step_size>0.001</max_step_size>
      <real_time_factor>1.0</real_time_factor>
    </physics>
    
    <!-- Lighting -->
    <light type="directional" name="sun">
      <pose>0 0 10 0 0 0</pose>
      <diffuse>0.8 0.8 0.8 1</diffuse>
      <specular>0.2 0.2 0.2 1</specular>
      <direction>-0.5 0.1 -0.9</direction>
    </light>
    
    <!-- Ground -->
    <model name="ground">
      <static>true</static>
      <link name="link">
        <collision name="collision">
          <geometry>
            <plane><normal>0 0 1</normal></plane>
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
            <ambient>0.5 0.5 0.5 1</ambient>
          </material>
        </visual>
      </link>
    </model>
    
    <!-- Walls -->
    <model name="wall_north">
      <static>true</static>
      <pose>5 0 1 0 0 0</pose>
      <link name="link">
        <collision name="collision">
          <geometry>
            <box><size>0.2 10 2</size></box>
          </geometry>
        </collision>
        <visual name="visual">
          <geometry>
            <box><size>0.2 10 2</size></box>
          </geometry>
          <material>
            <ambient>0.8 0.2 0.2 1</ambient>
          </material>
        </visual>
      </link>
    </model>
    
    <!-- Obstacles -->
    <model name="obstacle_1">
      <static>true</static>
      <pose>2 2 0.5 0 0 0</pose>
      <link name="link">
        <collision name="collision">
          <geometry>
            <cylinder>
              <radius>0.3</radius>
              <length>1.0</length>
            </cylinder>
          </geometry>
        </collision>
        <visual name="visual">
          <geometry>
            <cylinder>
              <radius>0.3</radius>
              <length>1.0</length>
            </cylinder>
          </geometry>
          <material>
            <ambient>0.2 0.8 0.2 1</ambient>
          </material>
        </visual>
      </link>
    </model>
    
  </world>
</sdf>
```

## Advanced Physics Tuning

### Timestep Selection

Smaller timestep = more accurate but slower:

```xml
<physics name="precise" type="ode">
  <max_step_size>0.0001</max_step_size>  <!-- 0.1ms: very precise -->
  <real_time_factor>1.0</real_time_factor>
</physics>

<physics name="fast" type="ode">
  <max_step_size>0.01</max_step_size>  <!-- 10ms: fast but less accurate -->
  <real_time_factor>1.0</real_time_factor>
</physics>
```

**Rule of thumb**: Use 1ms (0.001) for most robots.

### Contact Parameters

Fine-tune collision behavior:

```xml
<collision name="collision">
  <geometry>
    <box><size>1 1 1</size></box>
  </geometry>
  <surface>
    <contact>
      <ode>
        <kp>1000000.0</kp>  <!-- Contact stiffness -->
        <kd>1.0</kd>        <!-- Contact damping -->
        <max_vel>0.01</max_vel>
        <min_depth>0.001</min_depth>
      </ode>
    </contact>
    <friction>
      <ode>
        <mu>0.8</mu>
        <mu2>0.8</mu2>
      </ode>
    </friction>
  </surface>
</collision>
```

## Python Tools for URDF/SDF

### Generating URDF Programmatically

```python
def generate_box_robot(name, size, mass):
    """Generate a simple box robot URDF."""
    w, h, d = size
    ixx, iyy, izz = box_inertia(mass, w, h, d)
    
    urdf = f"""<?xml version="1.0"?>
<robot name="{name}">
  <link name="base_link">
    <visual>
      <geometry>
        <box size="{w} {h} {d}"/>
      </geometry>
      <material name="blue">
        <color rgba="0 0 1 1"/>
      </material>
    </visual>
    
    <collision>
      <geometry>
        <box size="{w} {h} {d}"/>
      </geometry>
    </collision>
    
    <inertial>
      <mass value="{mass}"/>
      <inertia ixx="{ixx}" iyy="{iyy}" izz="{izz}"
               ixy="0" ixz="0" iyz="0"/>
    </inertial>
  </link>
</robot>
"""
    return urdf

# Generate and save
urdf_content = generate_box_robot("my_robot", (1.0, 0.5, 0.3), 10.0)
with open("my_robot.urdf", "w") as f:
    f.write(urdf_content)
```

### Validating URDF

```bash
# Check URDF syntax
check_urdf my_robot.urdf

# Visualize in RViz
ros2 launch urdf_tutorial display.launch.py model:=my_robot.urdf
```

## Summary

- Physics engines simulate gravity, collisions, friction, and dynamics
- Accurate **mass** and **inertia** are critical for stable simulation
- **Collision geometry** should be simpler than visual geometry
- **URDF** is ROS's format, **SDF** is Gazebo's (more powerful)
- Tune physics parameters (timestep, friction, damping) for realism
- Start simple, add complexity gradually

## Next Steps

In the next chapter, we'll add sensors (cameras, LiDAR, IMU) to our simulated robots.

## Practice Exercises

1. Create a four-wheeled robot in SDF
2. Calculate inertia for a cylindrical robot arm
3. Build a maze environment with walls and obstacles
4. Tune friction coefficients for different surfaces
5. Convert a URDF model to SDF format
