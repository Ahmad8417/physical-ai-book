---
sidebar_position: 1
title: "ROS 2 Overview"
---

# Module 1: The Robotic Nervous System (ROS 2)

## What is ROS 2?

**ROS 2 (Robot Operating System 2)** is an open-source middleware framework designed for building robot applications. Despite its name, ROS is not an operating system—it's a collection of software libraries and tools that help you build robot software.

Think of ROS 2 as the **nervous system** of a robot:
- Just like your nervous system connects your brain to your muscles and sensors
- ROS 2 connects different software components (perception, planning, control) in a robot

### Why ROS 2 Matters

ROS 2 is the industry standard for robotics development. Here's why:

1. **Modularity**: Break complex robot systems into manageable pieces
2. **Reusability**: Use existing packages instead of reinventing the wheel
3. **Community**: Thousands of developers contributing packages and solutions
4. **Industry Adoption**: Used by Boston Dynamics, NASA, automotive companies
5. **Real-time Capable**: Built on DDS (Data Distribution Service) for deterministic communication

### ROS 1 vs ROS 2

| Feature | ROS 1 | ROS 2 |
|---------|-------|-------|
| Communication | Custom TCP/UDP | DDS (Data Distribution Service) |
| Real-time | Limited | Full support |
| Security | Basic | Encrypted, authenticated |
| Multi-robot | Difficult | Native support |
| Operating Systems | Linux only | Linux, Windows, macOS |
| Python Version | Python 2 (deprecated) | Python 3 |

**Bottom line**: ROS 2 is production-ready for commercial robots. ROS 1 reached end-of-life in 2025.

## ROS 2 Architecture

ROS 2 uses a **distributed architecture** where multiple processes (called nodes) communicate with each other.

```
┌─────────────────────────────────────────────────────────┐
│                    ROS 2 Graph                          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────┐         Topic: /camera/image            │
│  │  Camera  │────────────────────────────────────────┐ │
│  │   Node   │                                        │ │
│  └──────────┘                                        ↓ │
│                                                  ┌──────────┐
│  ┌──────────┐         Topic: /cmd_vel           │  Vision  │
│  │  Lidar   │────────────────────────────────┐  │   Node   │
│  │   Node   │                                │  └──────────┘
│  └──────────┘                                ↓       │
│                                          ┌──────────┐ │
│  ┌──────────┐      Service: /get_plan   │ Planning │ │
│  │   IMU    │◄─────────────────────────┤   Node   │ │
│  │   Node   │                           └──────────┘ │
│  └──────────┘                                 │      │
│       │                                       ↓      │
│       │         Topic: /joint_states    ┌──────────┐ │
│       └─────────────────────────────────►  Control │ │
│                                          │   Node   │ │
│                                          └──────────┘ │
│                                                       │
└───────────────────────────────────────────────────────┘
```

### Key Components

1. **Nodes**: Independent processes that perform computation
2. **Topics**: Named buses for streaming data (publish/subscribe)
3. **Services**: Request/response communication (like function calls)
4. **Actions**: Long-running tasks with feedback (like async functions)
5. **Parameters**: Configuration values for nodes

## Key Concepts Explained

### 1. Nodes

A **node** is a single-purpose executable program. Examples:
- A node that reads camera data
- A node that processes images to detect objects
- A node that plans a path from A to B
- A node that sends commands to motors

**Philosophy**: One node = one responsibility (like microservices)

### 2. Topics

**Topics** are named channels for data streaming. They use a **publish-subscribe** pattern:

```
Publisher Node ──► Topic (/sensor_data) ──► Subscriber Node(s)
```

- **Publishers** send messages to a topic
- **Subscribers** receive messages from a topic
- Many-to-many: Multiple publishers and subscribers can use the same topic

**Example**: A camera node publishes images to `/camera/image`, and multiple nodes (object detection, recording, display) can subscribe to it.

### 3. Services

**Services** are for request-response interactions:

```
Client Node ──[Request]──► Service (/add_two_ints) ──[Response]──► Client Node
                                    │
                              Server Node
```

- **Synchronous**: Client waits for response
- **One-to-one**: One client talks to one server at a time

**Example**: A planning node requests a path from a path planning service.

### 4. Actions

**Actions** are for long-running tasks with feedback:

```
Action Client ──[Goal]──► Action Server
              ◄─[Feedback]─
              ◄─[Result]───
```

- **Asynchronous**: Client doesn't block
- **Cancellable**: Client can cancel the goal
- **Feedback**: Server sends progress updates

**Example**: "Navigate to kitchen" action sends feedback like "50% complete, 2 meters remaining".

## Installation Guide (Ubuntu 22.04)

### Prerequisites

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install locale
sudo apt install locales
sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8
```

### Add ROS 2 Repository

```bash
# Add ROS 2 GPG key
sudo apt install software-properties-common
sudo add-apt-repository universe
sudo apt update && sudo apt install curl -y

sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
  -o /usr/share/keyrings/ros-archive-keyring.gpg

# Add repository to sources list
echo "deb [arch=$(dpkg --print-architecture) \
  signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] \
  http://packages.ros.org/ros2/ubuntu \
  $(. /etc/os-release && echo $UBUNTU_CODENAME) main" \
  | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null
```

### Install ROS 2 Humble

```bash
# Update package index
sudo apt update

# Install ROS 2 Desktop (includes RViz, demos, tutorials)
sudo apt install ros-humble-desktop -y

# Install development tools
sudo apt install ros-dev-tools -y
```

### Setup Environment

```bash
# Source ROS 2 setup file
source /opt/ros/humble/setup.bash

# Add to .bashrc for automatic sourcing
echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
```

### Verify Installation

```bash
# Check ROS 2 version
ros2 --version

# List available commands
ros2 --help

# Run a demo talker node
ros2 run demo_nodes_cpp talker
```

In another terminal:

```bash
# Run a demo listener node
ros2 run demo_nodes_cpp listener
```

You should see the listener receiving messages from the talker!

## Your First ROS 2 Program

Let's create a simple publisher node in Python.

### Step 1: Create a Workspace

```bash
# Create workspace directory
mkdir -p ~/ros2_ws/src
cd ~/ros2_ws/src

# Create a package
ros2 pkg create --build-type ament_python my_first_package \
  --dependencies rclpy std_msgs
```

### Step 2: Write a Publisher Node

Create `~/ros2_ws/src/my_first_package/my_first_package/publisher.py`:

```python
import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class MinimalPublisher(Node):
    """A simple publisher node that sends messages."""
    
    def __init__(self):
        # Initialize the node with name 'minimal_publisher'
        super().__init__('minimal_publisher')
        
        # Create a publisher on topic 'topic' with message type String
        # Queue size of 10 means buffer up to 10 messages
        self.publisher_ = self.create_publisher(String, 'topic', 10)
        
        # Create a timer that calls timer_callback every 0.5 seconds
        timer_period = 0.5  # seconds
        self.timer = self.create_timer(timer_period, self.timer_callback)
        
        # Counter for messages
        self.i = 0
        
        self.get_logger().info('Publisher node started!')

    def timer_callback(self):
        """Called every 0.5 seconds to publish a message."""
        msg = String()
        msg.data = f'Hello World: {self.i}'
        
        # Publish the message
        self.publisher_.publish(msg)
        
        # Log to console
        self.get_logger().info(f'Publishing: "{msg.data}"')
        
        self.i += 1


def main(args=None):
    # Initialize ROS 2 Python client library
    rclpy.init(args=args)
    
    # Create the node
    minimal_publisher = MinimalPublisher()
    
    # Keep the node running (spin = process callbacks)
    rclpy.spin(minimal_publisher)
    
    # Cleanup
    minimal_publisher.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
```

### Step 3: Write a Subscriber Node

Create `~/ros2_ws/src/my_first_package/my_first_package/subscriber.py`:

```python
import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class MinimalSubscriber(Node):
    """A simple subscriber node that receives messages."""
    
    def __init__(self):
        super().__init__('minimal_subscriber')
        
        # Create a subscription to topic 'topic' with message type String
        self.subscription = self.create_subscription(
            String,
            'topic',
            self.listener_callback,
            10  # Queue size
        )
        
        self.get_logger().info('Subscriber node started!')

    def listener_callback(self, msg):
        """Called whenever a message is received on the topic."""
        self.get_logger().info(f'I heard: "{msg.data}"')


def main(args=None):
    rclpy.init(args=args)
    minimal_subscriber = MinimalSubscriber()
    rclpy.spin(minimal_subscriber)
    minimal_subscriber.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
```

### Step 4: Update setup.py

Edit `~/ros2_ws/src/my_first_package/setup.py`:

```python
from setuptools import setup

package_name = 'my_first_package'

setup(
    name=package_name,
    version='0.0.1',
    packages=[package_name],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Your Name',
    maintainer_email='your.email@example.com',
    description='My first ROS 2 package',
    license='Apache License 2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'publisher = my_first_package.publisher:main',
            'subscriber = my_first_package.subscriber:main',
        ],
    },
)
```

### Step 5: Build and Run

```bash
# Navigate to workspace root
cd ~/ros2_ws

# Build the package
colcon build --packages-select my_first_package

# Source the workspace
source install/setup.bash

# Run publisher in one terminal
ros2 run my_first_package publisher

# Run subscriber in another terminal (after sourcing)
ros2 run my_first_package subscriber
```

**Output**:
```
[INFO] [minimal_publisher]: Publishing: "Hello World: 0"
[INFO] [minimal_publisher]: Publishing: "Hello World: 1"
...

[INFO] [minimal_subscriber]: I heard: "Hello World: 0"
[INFO] [minimal_subscriber]: I heard: "Hello World: 1"
...
```

## Understanding the Code

### Node Lifecycle

1. **Initialize**: `rclpy.init()` sets up ROS 2 communication
2. **Create Node**: Instantiate your node class
3. **Spin**: `rclpy.spin()` processes callbacks (messages, timers, services)
4. **Cleanup**: Destroy node and shutdown

### Publisher Pattern

```python
# Create publisher
self.publisher_ = self.create_publisher(MessageType, 'topic_name', queue_size)

# Publish message
msg = MessageType()
msg.data = "some data"
self.publisher_.publish(msg)
```

### Subscriber Pattern

```python
# Create subscription
self.subscription = self.create_subscription(
    MessageType,
    'topic_name',
    self.callback_function,
    queue_size
)

# Callback receives messages
def callback_function(self, msg):
    # Process msg.data
    pass
```

## ROS 2 Command Line Tools

### Introspection Commands

```bash
# List all running nodes
ros2 node list

# Get info about a node
ros2 node info /minimal_publisher

# List all topics
ros2 topic list

# See messages on a topic
ros2 topic echo /topic

# Get topic info (publishers, subscribers, message type)
ros2 topic info /topic

# Publish to a topic from command line
ros2 topic pub /topic std_msgs/msg/String "data: 'Hello from CLI'"

# List all services
ros2 service list

# Call a service
ros2 service call /service_name std_srvs/srv/Empty
```

### Useful Debugging Commands

```bash
# Check message type definition
ros2 interface show std_msgs/msg/String

# Monitor topic frequency
ros2 topic hz /topic

# Monitor topic bandwidth
ros2 topic bw /topic

# Record topics to a bag file
ros2 bag record /topic1 /topic2

# Play back recorded data
ros2 bag play my_bag_file
```

## Next Steps

In the next chapters, we'll dive deeper into:
- **Nodes and Topics**: Building complex publish-subscribe systems
- **Python Agents**: Integrating AI agents with ROS 2

## Summary

- ROS 2 is the industry-standard middleware for robotics
- It uses a distributed architecture with nodes communicating via topics, services, and actions
- Topics are for streaming data (pub-sub pattern)
- Services are for request-response (synchronous)
- Actions are for long-running tasks (asynchronous with feedback)
- Python is a first-class language in ROS 2 via `rclpy`

## Resources

- [Official ROS 2 Documentation](https://docs.ros.org/en/humble/)
- [ROS 2 Tutorials](https://docs.ros.org/en/humble/Tutorials.html)
- [ROS Discourse Forum](https://discourse.ros.org/)
- [ROS Answers](https://answers.ros.org/)
