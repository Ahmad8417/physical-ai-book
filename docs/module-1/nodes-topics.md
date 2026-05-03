---
sidebar_position: 2
title: "Nodes and Topics Deep Dive"
---

# Nodes and Topics: The Communication Backbone

## Introduction

In this chapter, we'll explore the fundamental building blocks of ROS 2 communication: **nodes** and **topics**. By the end, you'll understand how to build complex robotic systems using the publish-subscribe pattern.

## What is a Node?

A **node** is an executable process that performs a specific task in your robot system. Think of nodes as specialized workers in a factory:

- **Camera Node**: Captures images
- **Object Detection Node**: Identifies objects in images
- **Path Planning Node**: Calculates routes
- **Motor Control Node**: Moves the robot

### Node Design Philosophy

**Single Responsibility Principle**: Each node should do one thing well.

**Good Design**:
```
Camera Node → Image Processing Node → Object Detection Node → Decision Node
```

**Bad Design**:
```
Monolithic Node (does everything)
```

### Why Multiple Nodes?

1. **Modularity**: Replace one component without affecting others
2. **Debugging**: Isolate problems to specific nodes
3. **Reusability**: Use the same node in different robots
4. **Parallel Processing**: Nodes run independently on different CPU cores
5. **Fault Isolation**: One node crashing doesn't kill the entire system

## Creating Nodes in Python

### Basic Node Structure

```python
import rclpy
from rclpy.node import Node


class MyNode(Node):
    def __init__(self):
        # Initialize with a unique node name
        super().__init__('my_node_name')
        
        # Node initialization code here
        self.get_logger().info('Node has been started!')


def main(args=None):
    rclpy.init(args=args)
    node = MyNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
```

### Node with Timer

Timers execute code at regular intervals:

```python
import rclpy
from rclpy.node import Node


class TimerNode(Node):
    def __init__(self):
        super().__init__('timer_node')
        
        # Create a timer that fires every 1.0 seconds
        self.timer = self.create_timer(1.0, self.timer_callback)
        self.counter = 0
        
    def timer_callback(self):
        """Called every second."""
        self.counter += 1
        self.get_logger().info(f'Timer fired {self.counter} times')


def main(args=None):
    rclpy.init(args=args)
    node = TimerNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
```

## Topics: The Data Highway

**Topics** are named channels for streaming data. They implement the **publish-subscribe pattern**:

- **Publishers** send data to a topic
- **Subscribers** receive data from a topic
- **Decoupled**: Publishers don't know who's listening, subscribers don't know who's publishing

### Topic Characteristics

1. **Asynchronous**: Non-blocking communication
2. **Many-to-Many**: Multiple publishers and subscribers
3. **Typed**: Each topic has a specific message type
4. **Named**: Topics have unique names like `/camera/image` or `/cmd_vel`

### Topic Naming Conventions

```
/global_topic              # Global namespace
/robot1/camera/image       # Namespaced (for multi-robot)
~/private_topic            # Private to node
camera/image               # Relative to node namespace
```

## Publishers in Detail

### Creating a Publisher

```python
import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class PublisherNode(Node):
    def __init__(self):
        super().__init__('publisher_node')
        
        # Create publisher
        # Parameters: message_type, topic_name, queue_size
        self.publisher_ = self.create_publisher(
            String,           # Message type
            'chatter',        # Topic name
            10                # Queue size (buffer)
        )
        
        # Publish every 0.5 seconds
        self.timer = self.create_timer(0.5, self.publish_message)
        self.count = 0
        
    def publish_message(self):
        msg = String()
        msg.data = f'Message {self.count}'
        self.publisher_.publish(msg)
        self.get_logger().info(f'Published: {msg.data}')
        self.count += 1


def main(args=None):
    rclpy.init(args=args)
    node = PublisherNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
```

### Queue Size Explained

The **queue size** determines how many messages to buffer if subscribers can't keep up:

- **Small queue (1-10)**: Low latency, may drop messages under load
- **Large queue (100+)**: No message loss, but higher memory usage and latency

**Rule of thumb**: Use 10 for most applications.

## Subscribers in Detail

### Creating a Subscriber

```python
import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class SubscriberNode(Node):
    def __init__(self):
        super().__init__('subscriber_node')
        
        # Create subscription
        self.subscription = self.create_subscription(
            String,                    # Message type
            'chatter',                 # Topic name
            self.listener_callback,    # Callback function
            10                         # Queue size
        )
        
    def listener_callback(self, msg):
        """Called whenever a message arrives."""
        self.get_logger().info(f'Received: {msg.data}')


def main(args=None):
    rclpy.init(args=args)
    node = SubscriberNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
```

### Callback Execution

- Callbacks run in the **main thread** by default
- Keep callbacks **fast** (< 10ms) to avoid blocking other callbacks
- For heavy processing, use a separate thread or node

## Message Types

ROS 2 uses strongly-typed messages. Common message packages:

### std_msgs: Basic Types

```python
from std_msgs.msg import String, Int32, Float64, Bool

# String message
msg = String()
msg.data = "Hello"

# Integer message
msg = Int32()
msg.data = 42

# Float message
msg = Float64()
msg.data = 3.14159

# Boolean message
msg = Bool()
msg.data = True
```

### geometry_msgs: Spatial Data

```python
from geometry_msgs.msg import Point, Pose, Twist

# 3D Point
point = Point()
point.x = 1.0
point.y = 2.0
point.z = 3.0

# Velocity command (linear and angular)
twist = Twist()
twist.linear.x = 0.5   # Move forward at 0.5 m/s
twist.angular.z = 0.1  # Turn at 0.1 rad/s
```

### sensor_msgs: Sensor Data

```python
from sensor_msgs.msg import Image, LaserScan, Imu

# Camera image
image = Image()
image.height = 480
image.width = 640
image.encoding = "rgb8"
image.data = [...]  # Raw pixel data

# LiDAR scan
scan = LaserScan()
scan.ranges = [1.2, 1.5, 2.0, ...]  # Distance measurements
scan.angle_min = -1.57  # -90 degrees
scan.angle_max = 1.57   # +90 degrees
```

## Real Robot Example: Velocity Controller

Let's build a node that controls a robot's movement using keyboard input.

### Robot Velocity Publisher

```python
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import sys
import termios
import tty


class TeleopNode(Node):
    """Teleoperation node for controlling robot with keyboard."""
    
    def __init__(self):
        super().__init__('teleop_node')
        
        # Publisher for velocity commands
        self.publisher_ = self.create_publisher(Twist, '/cmd_vel', 10)
        
        # Movement parameters
        self.linear_speed = 0.5   # m/s
        self.angular_speed = 1.0  # rad/s
        
        self.get_logger().info('Teleop node started!')
        self.get_logger().info('Use WASD to move, Q to quit')
        
    def get_key(self):
        """Get a single keypress from terminal."""
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            key = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return key
    
    def publish_velocity(self, linear, angular):
        """Publish velocity command."""
        msg = Twist()
        msg.linear.x = linear
        msg.angular.z = angular
        self.publisher_.publish(msg)
        
    def run(self):
        """Main control loop."""
        while rclpy.ok():
            key = self.get_key()
            
            if key == 'w':  # Forward
                self.publish_velocity(self.linear_speed, 0.0)
                self.get_logger().info('Moving forward')
                
            elif key == 's':  # Backward
                self.publish_velocity(-self.linear_speed, 0.0)
                self.get_logger().info('Moving backward')
                
            elif key == 'a':  # Turn left
                self.publish_velocity(0.0, self.angular_speed)
                self.get_logger().info('Turning left')
                
            elif key == 'd':  # Turn right
                self.publish_velocity(0.0, -self.angular_speed)
                self.get_logger().info('Turning right')
                
            elif key == ' ':  # Stop
                self.publish_velocity(0.0, 0.0)
                self.get_logger().info('Stopped')
                
            elif key == 'q':  # Quit
                self.publish_velocity(0.0, 0.0)
                self.get_logger().info('Quitting...')
                break


def main(args=None):
    rclpy.init(args=args)
    node = TeleopNode()
    
    try:
        node.run()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
```

### Robot Velocity Subscriber (Safety Monitor)

```python
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist


class SafetyMonitor(Node):
    """Monitor velocity commands and enforce safety limits."""
    
    def __init__(self):
        super().__init__('safety_monitor')
        
        # Subscribe to commanded velocities
        self.subscription = self.create_subscription(
            Twist,
            '/cmd_vel',
            self.velocity_callback,
            10
        )
        
        # Publish safe velocities
        self.publisher_ = self.create_publisher(Twist, '/cmd_vel_safe', 10)
        
        # Safety limits
        self.max_linear = 1.0   # m/s
        self.max_angular = 2.0  # rad/s
        
        self.get_logger().info('Safety monitor active')
        
    def velocity_callback(self, msg):
        """Check and limit velocities."""
        safe_msg = Twist()
        
        # Clamp linear velocity
        safe_msg.linear.x = max(
            -self.max_linear,
            min(self.max_linear, msg.linear.x)
        )
        
        # Clamp angular velocity
        safe_msg.angular.z = max(
            -self.max_angular,
            min(self.max_angular, msg.angular.z)
        )
        
        # Log if we had to limit
        if (abs(msg.linear.x) > self.max_linear or 
            abs(msg.angular.z) > self.max_angular):
            self.get_logger().warn('Velocity command exceeded limits!')
        
        # Publish safe command
        self.publisher_.publish(safe_msg)


def main(args=None):
    rclpy.init(args=args)
    node = SafetyMonitor()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
```

## Multi-Publisher Example: Sensor Fusion

Combining data from multiple sensors:

```python
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan, Imu
from geometry_msgs.msg import Twist
import math


class ObstacleAvoidance(Node):
    """Avoid obstacles using LiDAR and IMU data."""
    
    def __init__(self):
        super().__init__('obstacle_avoidance')
        
        # Subscribe to sensors
        self.lidar_sub = self.create_subscription(
            LaserScan,
            '/scan',
            self.lidar_callback,
            10
        )
        
        self.imu_sub = self.create_subscription(
            Imu,
            '/imu',
            self.imu_callback,
            10
        )
        
        # Publish velocity commands
        self.vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        
        # State
        self.min_distance = float('inf')
        self.is_stable = True
        
        # Control loop at 10 Hz
        self.timer = self.create_timer(0.1, self.control_loop)
        
    def lidar_callback(self, msg):
        """Process LiDAR data."""
        # Find minimum distance to obstacles
        valid_ranges = [r for r in msg.ranges if r > msg.range_min and r < msg.range_max]
        
        if valid_ranges:
            self.min_distance = min(valid_ranges)
        else:
            self.min_distance = float('inf')
            
    def imu_callback(self, msg):
        """Process IMU data."""
        # Check if robot is stable (not tipping)
        accel = msg.linear_acceleration
        total_accel = math.sqrt(accel.x**2 + accel.y**2 + accel.z**2)
        
        # If acceleration is close to gravity (9.81 m/s²), we're stable
        self.is_stable = abs(total_accel - 9.81) < 2.0
        
    def control_loop(self):
        """Main control logic."""
        msg = Twist()
        
        # Safety check
        if not self.is_stable:
            self.get_logger().warn('Robot unstable! Stopping.')
            msg.linear.x = 0.0
            msg.angular.z = 0.0
            self.vel_pub.publish(msg)
            return
        
        # Obstacle avoidance
        if self.min_distance < 0.5:  # Less than 50cm
            # Stop and turn
            msg.linear.x = 0.0
            msg.angular.z = 0.5
            self.get_logger().info(f'Obstacle at {self.min_distance:.2f}m, turning')
            
        elif self.min_distance < 1.0:  # Less than 1m
            # Slow down
            msg.linear.x = 0.2
            msg.angular.z = 0.0
            self.get_logger().info(f'Obstacle at {self.min_distance:.2f}m, slowing')
            
        else:
            # Full speed ahead
            msg.linear.x = 0.5
            msg.angular.z = 0.0
            
        self.vel_pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = ObstacleAvoidance()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
```

## Quality of Service (QoS)

QoS policies control how messages are delivered. Important for real-time systems.

### QoS Profiles

```python
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy, DurabilityPolicy

# Sensor data profile (best effort, may drop messages)
sensor_qos = QoSProfile(
    reliability=ReliabilityPolicy.BEST_EFFORT,
    history=HistoryPolicy.KEEP_LAST,
    depth=10
)

# Reliable profile (guaranteed delivery)
reliable_qos = QoSProfile(
    reliability=ReliabilityPolicy.RELIABLE,
    history=HistoryPolicy.KEEP_LAST,
    depth=10
)

# Transient local (late joiners get last message)
transient_qos = QoSProfile(
    reliability=ReliabilityPolicy.RELIABLE,
    durability=DurabilityPolicy.TRANSIENT_LOCAL,
    history=HistoryPolicy.KEEP_LAST,
    depth=1
)
```

### Using QoS Profiles

```python
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from rclpy.qos import qos_profile_sensor_data


class SensorNode(Node):
    def __init__(self):
        super().__init__('sensor_node')
        
        # Use sensor data QoS profile
        self.publisher_ = self.create_publisher(
            LaserScan,
            '/scan',
            qos_profile_sensor_data  # Predefined profile
        )
        
        self.subscription = self.create_subscription(
            LaserScan,
            '/scan',
            self.callback,
            qos_profile_sensor_data
        )
```

### When to Use Which QoS

| Use Case | Reliability | Durability | Example |
|----------|-------------|------------|---------|
| Sensor streams | Best Effort | Volatile | Camera, LiDAR |
| Commands | Reliable | Volatile | Velocity commands |
| Configuration | Reliable | Transient Local | Robot parameters |
| Critical data | Reliable | Transient Local | Safety states |

## Debugging Topics

### Command Line Tools

```bash
# List all topics
ros2 topic list

# Show topic info
ros2 topic info /cmd_vel

# Echo messages (print to console)
ros2 topic echo /cmd_vel

# Show message rate
ros2 topic hz /cmd_vel

# Show bandwidth usage
ros2 topic bw /cmd_vel

# Publish from command line
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.5}, angular: {z: 0.0}}"
```

### Programmatic Debugging

```python
import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class DebugNode(Node):
    def __init__(self):
        super().__init__('debug_node')
        
        self.subscription = self.create_subscription(
            String,
            'chatter',
            self.callback,
            10
        )
        
        self.msg_count = 0
        self.start_time = self.get_clock().now()
        
    def callback(self, msg):
        self.msg_count += 1
        
        # Calculate message rate
        elapsed = (self.get_clock().now() - self.start_time).nanoseconds / 1e9
        rate = self.msg_count / elapsed if elapsed > 0 else 0
        
        self.get_logger().info(
            f'Msg #{self.msg_count}: "{msg.data}" | Rate: {rate:.2f} Hz'
        )
```

## Best Practices

### 1. Node Naming

```python
# Good: Descriptive names
super().__init__('camera_driver')
super().__init__('object_detector')
super().__init__('path_planner')

# Bad: Generic names
super().__init__('node1')
super().__init__('my_node')
```

### 2. Topic Naming

```python
# Good: Hierarchical and descriptive
'/robot1/camera/image_raw'
'/robot1/lidar/scan'
'/robot1/cmd_vel'

# Bad: Flat and ambiguous
'/image'
'/data'
'/output'
```

### 3. Error Handling

```python
def callback(self, msg):
    try:
        # Process message
        result = self.process(msg)
        
    except Exception as e:
        self.get_logger().error(f'Error processing message: {e}')
        return
```

### 4. Resource Cleanup

```python
def __init__(self):
    super().__init__('my_node')
    self.publisher_ = self.create_publisher(String, 'topic', 10)
    
def __del__(self):
    """Cleanup when node is destroyed."""
    self.get_logger().info('Node shutting down')
    # ROS 2 handles cleanup automatically, but you can add custom cleanup here
```

## Summary

- **Nodes** are independent processes that perform specific tasks
- **Topics** enable asynchronous, many-to-many communication
- **Publishers** send messages to topics
- **Subscribers** receive messages from topics
- **QoS policies** control message delivery guarantees
- Keep nodes focused on single responsibilities
- Use descriptive names for nodes and topics
- Handle errors gracefully in callbacks

## Next Steps

In the next chapter, we'll learn how to integrate Python AI agents with ROS 2 to create intelligent robotic behaviors.

## Practice Exercises

1. Create a node that publishes random numbers to a topic
2. Create a subscriber that calculates the running average
3. Build a simple "echo" system with two nodes
4. Implement a traffic light controller using timers and publishers
5. Create a node that subscribes to multiple topics and combines their data
