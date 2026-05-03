---
sidebar_position: 3
title: "Python AI Agents in ROS 2"
---

# Bridging Python AI Agents to ROS 2

## Introduction

Modern robotics is at the intersection of **traditional control systems** and **artificial intelligence**. In this chapter, we'll learn how to integrate Python AI agents with ROS 2 to create intelligent, autonomous robots.

**What you'll learn**:
- How to connect AI/ML models to ROS 2
- Building decision-making agents
- Integrating LLMs with robotic systems
- Real-world autonomous agent examples

## Why Python for AI + Robotics?

Python dominates the AI/ML ecosystem:

- **PyTorch** and **TensorFlow** for deep learning
- **OpenAI API** for LLMs
- **LangChain** for agent frameworks
- **NumPy** and **Pandas** for data processing
- **OpenCV** for computer vision

ROS 2 has **first-class Python support** via `rclpy`, making it perfect for AI-powered robots.

## Architecture: AI Agent + ROS 2

```
┌─────────────────────────────────────────────────────────┐
│                    AI-Powered Robot                     │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────┐         ┌──────────────┐            │
│  │   Sensors    │────────►│  Perception  │            │
│  │ (Camera,     │         │    Node      │            │
│  │  LiDAR, IMU) │         │ (CV/ML)      │            │
│  └──────────────┘         └──────┬───────┘            │
│                                   │                     │
│                                   ↓                     │
│                          ┌─────────────────┐           │
│                          │   AI Agent      │           │
│                          │   (Decision     │           │
│                          │    Making)      │           │
│                          └────────┬────────┘           │
│                                   │                     │
│                                   ↓                     │
│  ┌──────────────┐         ┌──────────────┐            │
│  │   Actuators  │◄────────│   Control    │            │
│  │ (Motors,     │         │    Node      │            │
│  │  Servos)     │         │              │            │
│  └──────────────┘         └──────────────┘            │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## The rclpy Library

`rclpy` is the Python client library for ROS 2. It provides:

- Node creation and management
- Publishers and subscribers
- Services and actions
- Timers and callbacks
- Parameter handling
- Logging utilities

### Basic rclpy Patterns

```python
import rclpy
from rclpy.node import Node

# Initialize ROS 2
rclpy.init()

# Create node
node = Node('my_node')

# Use the node
# ...

# Spin (process callbacks)
rclpy.spin(node)

# Cleanup
node.destroy_node()
rclpy.shutdown()
```

## Building an AI Agent Node

Let's create a simple decision-making agent that processes sensor data and makes decisions.

### Example 1: Rule-Based Agent

```python
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import Twist
from enum import Enum


class RobotState(Enum):
    """Possible robot states."""
    EXPLORING = 1
    AVOIDING_OBSTACLE = 2
    STUCK = 3
    GOAL_REACHED = 4


class SimpleAgent(Node):
    """A simple rule-based agent for robot navigation."""
    
    def __init__(self):
        super().__init__('simple_agent')
        
        # Subscriptions
        self.scan_sub = self.create_subscription(
            LaserScan,
            '/scan',
            self.scan_callback,
            10
        )
        
        # Publishers
        self.vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        
        # Agent state
        self.state = RobotState.EXPLORING
        self.min_distance = float('inf')
        self.stuck_counter = 0
        
        # Parameters
        self.safe_distance = 1.0  # meters
        self.danger_distance = 0.5  # meters
        
        # Decision loop at 10 Hz
        self.timer = self.create_timer(0.1, self.decision_loop)
        
        self.get_logger().info('Simple Agent initialized')
        
    def scan_callback(self, msg):
        """Process LiDAR data."""
        valid_ranges = [
            r for r in msg.ranges 
            if msg.range_min < r < msg.range_max
        ]
        
        if valid_ranges:
            self.min_distance = min(valid_ranges)
        else:
            self.min_distance = float('inf')
            
    def decision_loop(self):
        """Main decision-making loop."""
        # State machine
        if self.state == RobotState.EXPLORING:
            self.explore()
            
        elif self.state == RobotState.AVOIDING_OBSTACLE:
            self.avoid_obstacle()
            
        elif self.state == RobotState.STUCK:
            self.recover_from_stuck()
            
    def explore(self):
        """Exploration behavior."""
        cmd = Twist()
        
        if self.min_distance < self.danger_distance:
            # Transition to obstacle avoidance
            self.state = RobotState.AVOIDING_OBSTACLE
            self.get_logger().info('State: AVOIDING_OBSTACLE')
            
        elif self.min_distance < self.safe_distance:
            # Slow down
            cmd.linear.x = 0.2
            cmd.angular.z = 0.0
            
        else:
            # Full speed
            cmd.linear.x = 0.5
            cmd.angular.z = 0.0
            
        self.vel_pub.publish(cmd)
        
    def avoid_obstacle(self):
        """Obstacle avoidance behavior."""
        cmd = Twist()
        
        # Stop and turn
        cmd.linear.x = 0.0
        cmd.angular.z = 0.5
        
        self.vel_pub.publish(cmd)
        
        # Check if we've cleared the obstacle
        if self.min_distance > self.safe_distance:
            self.state = RobotState.EXPLORING
            self.stuck_counter = 0
            self.get_logger().info('State: EXPLORING')
        else:
            self.stuck_counter += 1
            
        # Check if we're stuck
        if self.stuck_counter > 50:  # 5 seconds at 10 Hz
            self.state = RobotState.STUCK
            self.get_logger().warn('State: STUCK')
            
    def recover_from_stuck(self):
        """Recovery behavior when stuck."""
        cmd = Twist()
        
        # Back up and turn
        cmd.linear.x = -0.2
        cmd.angular.z = 0.8
        
        self.vel_pub.publish(cmd)
        
        # After backing up, try exploring again
        self.stuck_counter += 1
        if self.stuck_counter > 70:  # 7 seconds
            self.state = RobotState.EXPLORING
            self.stuck_counter = 0
            self.get_logger().info('Recovery complete, State: EXPLORING')


def main(args=None):
    rclpy.init(args=args)
    agent = SimpleAgent()
    rclpy.spin(agent)
    agent.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
```

## Example 2: ML-Based Agent

Using a neural network for decision making:

```python
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import Twist
import numpy as np
import torch
import torch.nn as nn


class PolicyNetwork(nn.Module):
    """Simple neural network for robot control."""
    
    def __init__(self, input_size, hidden_size, output_size):
        super(PolicyNetwork, self).__init__()
        self.fc1 = nn.Linear(input_size, hidden_size)
        self.fc2 = nn.Linear(hidden_size, hidden_size)
        self.fc3 = nn.Linear(hidden_size, output_size)
        self.relu = nn.ReLU()
        self.tanh = nn.Tanh()
        
    def forward(self, x):
        x = self.relu(self.fc1(x))
        x = self.relu(self.fc2(x))
        x = self.tanh(self.fc3(x))
        return x


class MLAgent(Node):
    """ML-based agent using a trained neural network."""
    
    def __init__(self):
        super().__init__('ml_agent')
        
        # Load trained model
        self.model = PolicyNetwork(
            input_size=360,   # 360-degree LiDAR
            hidden_size=128,
            output_size=2     # [linear_vel, angular_vel]
        )
        
        # Load weights (assuming you have a trained model)
        # self.model.load_state_dict(torch.load('model.pth'))
        self.model.eval()
        
        # ROS 2 interfaces
        self.scan_sub = self.create_subscription(
            LaserScan,
            '/scan',
            self.scan_callback,
            10
        )
        
        self.vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        
        # State
        self.latest_scan = None
        
        # Control loop
        self.timer = self.create_timer(0.1, self.control_loop)
        
        self.get_logger().info('ML Agent initialized')
        
    def scan_callback(self, msg):
        """Store latest scan."""
        self.latest_scan = msg
        
    def preprocess_scan(self, scan_msg):
        """Convert LaserScan to neural network input."""
        ranges = np.array(scan_msg.ranges)
        
        # Replace inf values with max range
        ranges[np.isinf(ranges)] = scan_msg.range_max
        
        # Normalize to [0, 1]
        ranges = ranges / scan_msg.range_max
        
        return ranges
        
    def control_loop(self):
        """Use neural network to generate control commands."""
        if self.latest_scan is None:
            return
            
        # Preprocess sensor data
        scan_data = self.preprocess_scan(self.latest_scan)
        
        # Convert to tensor
        input_tensor = torch.FloatTensor(scan_data).unsqueeze(0)
        
        # Forward pass through network
        with torch.no_grad():
            output = self.model(input_tensor)
            
        # Extract velocities
        linear_vel = output[0, 0].item() * 0.5   # Scale to max 0.5 m/s
        angular_vel = output[0, 1].item() * 1.0  # Scale to max 1.0 rad/s
        
        # Publish command
        cmd = Twist()
        cmd.linear.x = float(linear_vel)
        cmd.angular.z = float(angular_vel)
        self.vel_pub.publish(cmd)
        
        self.get_logger().debug(
            f'Command: linear={linear_vel:.2f}, angular={angular_vel:.2f}'
        )


def main(args=None):
    rclpy.init(args=args)
    agent = MLAgent()
    rclpy.spin(agent)
    agent.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
```

## Example 3: LLM-Powered Agent

Integrating Large Language Models for high-level reasoning:

```python
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from geometry_msgs.msg import Twist
from sensor_msgs.msg import LaserScan
import json
import os
from openai import OpenAI


class LLMAgent(Node):
    """Agent that uses an LLM for decision making."""
    
    def __init__(self):
        super().__init__('llm_agent')
        
        # Initialize OpenAI client
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # ROS 2 interfaces
        self.scan_sub = self.create_subscription(
            LaserScan,
            '/scan',
            self.scan_callback,
            10
        )
        
        self.command_sub = self.create_subscription(
            String,
            '/voice_command',
            self.command_callback,
            10
        )
        
        self.vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.status_pub = self.create_publisher(String, '/robot_status', 10)
        
        # State
        self.current_command = None
        self.min_distance = float('inf')
        self.conversation_history = []
        
        # Decision loop
        self.timer = self.create_timer(1.0, self.decision_loop)
        
        self.get_logger().info('LLM Agent initialized')
        
    def scan_callback(self, msg):
        """Process LiDAR data."""
        valid_ranges = [r for r in msg.ranges if 0.1 < r < 10.0]
        if valid_ranges:
            self.min_distance = min(valid_ranges)
            
    def command_callback(self, msg):
        """Receive voice commands."""
        self.current_command = msg.data
        self.get_logger().info(f'Received command: {self.current_command}')
        
    def get_sensor_summary(self):
        """Summarize sensor data for LLM."""
        if self.min_distance < 0.5:
            return "obstacle very close (danger)"
        elif self.min_distance < 1.0:
            return "obstacle nearby (caution)"
        elif self.min_distance < 2.0:
            return "obstacle detected (safe distance)"
        else:
            return "path clear"
            
    def decision_loop(self):
        """Use LLM to make decisions."""
        if self.current_command is None:
            return
            
        # Prepare context for LLM
        sensor_summary = self.get_sensor_summary()
        
        prompt = f"""You are controlling a mobile robot. 

Current situation:
- User command: "{self.current_command}"
- Sensor status: {sensor_summary}
- Minimum obstacle distance: {self.min_distance:.2f} meters

Based on this information, decide what the robot should do.
Respond with a JSON object containing:
- "action": one of ["move_forward", "turn_left", "turn_right", "stop", "move_backward"]
- "speed": a number between 0.0 and 1.0
- "reasoning": brief explanation of your decision

Example response:
{{"action": "move_forward", "speed": 0.5, "reasoning": "Path is clear and user wants to move forward"}}
"""

        try:
            # Call LLM
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a robot control AI. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=150
            )
            
            # Parse response
            decision_text = response.choices[0].message.content
            decision = json.loads(decision_text)
            
            # Execute decision
            self.execute_action(decision)
            
            # Log reasoning
            self.get_logger().info(f"Decision: {decision['reasoning']}")
            
            # Publish status
            status_msg = String()
            status_msg.data = decision['reasoning']
            self.status_pub.publish(status_msg)
            
        except Exception as e:
            self.get_logger().error(f'LLM decision error: {e}')
            # Fallback: stop
            self.execute_action({"action": "stop", "speed": 0.0})
            
    def execute_action(self, decision):
        """Convert LLM decision to robot commands."""
        cmd = Twist()
        action = decision['action']
        speed = decision['speed']
        
        if action == 'move_forward':
            cmd.linear.x = 0.5 * speed
            cmd.angular.z = 0.0
            
        elif action == 'move_backward':
            cmd.linear.x = -0.3 * speed
            cmd.angular.z = 0.0
            
        elif action == 'turn_left':
            cmd.linear.x = 0.0
            cmd.angular.z = 0.5 * speed
            
        elif action == 'turn_right':
            cmd.linear.x = 0.0
            cmd.angular.z = -0.5 * speed
            
        elif action == 'stop':
            cmd.linear.x = 0.0
            cmd.angular.z = 0.0
            
        self.vel_pub.publish(cmd)


def main(args=None):
    rclpy.init(args=args)
    agent = LLMAgent()
    rclpy.spin(agent)
    agent.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
```

## Example 4: Vision-Language Agent

Combining computer vision with language understanding:

```python
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String
from geometry_msgs.msg import Twist
from cv_bridge import CvBridge
import cv2
import numpy as np
from openai import OpenAI
import base64
import os


class VisionLanguageAgent(Node):
    """Agent that uses vision and language for decision making."""
    
    def __init__(self):
        super().__init__('vision_language_agent')
        
        # OpenAI client
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # CV Bridge for ROS image conversion
        self.bridge = CvBridge()
        
        # ROS 2 interfaces
        self.image_sub = self.create_subscription(
            Image,
            '/camera/image_raw',
            self.image_callback,
            10
        )
        
        self.command_sub = self.create_subscription(
            String,
            '/voice_command',
            self.command_callback,
            10
        )
        
        self.vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.description_pub = self.create_publisher(String, '/scene_description', 10)
        
        # State
        self.latest_image = None
        self.current_command = None
        
        # Process at 1 Hz (vision models are slow)
        self.timer = self.create_timer(1.0, self.process_scene)
        
        self.get_logger().info('Vision-Language Agent initialized')
        
    def image_callback(self, msg):
        """Store latest camera image."""
        try:
            self.latest_image = self.bridge.imgmsg_to_cv2(msg, 'bgr8')
        except Exception as e:
            self.get_logger().error(f'Image conversion error: {e}')
            
    def command_callback(self, msg):
        """Receive voice commands."""
        self.current_command = msg.data
        self.get_logger().info(f'Command: {self.current_command}')
        
    def encode_image(self, image):
        """Encode OpenCV image to base64 for API."""
        _, buffer = cv2.imencode('.jpg', image)
        return base64.b64encode(buffer).decode('utf-8')
        
    def process_scene(self):
        """Analyze scene and make decisions."""
        if self.latest_image is None or self.current_command is None:
            return
            
        try:
            # Encode image
            image_base64 = self.encode_image(self.latest_image)
            
            # Prepare prompt
            prompt = f"""You are controlling a mobile robot with a camera.

User command: "{self.current_command}"

Analyze the image and decide what the robot should do.
Respond with JSON:
- "scene_description": what you see in the image
- "action": one of ["move_forward", "turn_left", "turn_right", "stop"]
- "speed": 0.0 to 1.0
- "reasoning": why you chose this action

Consider obstacles, people, and the user's command.
"""

            # Call GPT-4 Vision
            response = self.client.chat.completions.create(
                model="gpt-4-vision-preview",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=300
            )
            
            # Parse response
            import json
            decision = json.loads(response.choices[0].message.content)
            
            # Publish scene description
            desc_msg = String()
            desc_msg.data = decision['scene_description']
            self.description_pub.publish(desc_msg)
            
            # Execute action
            self.execute_action(decision)
            
            self.get_logger().info(f"Scene: {decision['scene_description']}")
            self.get_logger().info(f"Action: {decision['reasoning']}")
            
        except Exception as e:
            self.get_logger().error(f'Vision processing error: {e}')
            
    def execute_action(self, decision):
        """Execute the decided action."""
        cmd = Twist()
        action = decision['action']
        speed = decision['speed']
        
        if action == 'move_forward':
            cmd.linear.x = 0.5 * speed
        elif action == 'turn_left':
            cmd.angular.z = 0.5 * speed
        elif action == 'turn_right':
            cmd.angular.z = -0.5 * speed
        elif action == 'stop':
            cmd.linear.x = 0.0
            cmd.angular.z = 0.0
            
        self.vel_pub.publish(cmd)


def main(args=None):
    rclpy.init(args=args)
    agent = VisionLanguageAgent()
    rclpy.spin(agent)
    agent.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
```

## Agent Design Patterns

### 1. Sense-Think-Act Loop

```python
class SenseThinkActAgent(Node):
    def __init__(self):
        super().__init__('sta_agent')
        
        # Sense: Subscribe to sensors
        self.sensor_sub = self.create_subscription(...)
        
        # Act: Publish commands
        self.actuator_pub = self.create_publisher(...)
        
        # Think: Decision loop
        self.timer = self.create_timer(0.1, self.think)
        
    def think(self):
        """Decision-making logic."""
        # 1. Sense: Get current state
        state = self.get_current_state()
        
        # 2. Think: Decide action
        action = self.decide_action(state)
        
        # 3. Act: Execute action
        self.execute_action(action)
```

### 2. Behavior Trees

```python
from enum import Enum

class BehaviorStatus(Enum):
    SUCCESS = 1
    FAILURE = 2
    RUNNING = 3

class Behavior:
    def tick(self):
        """Execute behavior and return status."""
        raise NotImplementedError

class Sequence(Behavior):
    """Execute children in order until one fails."""
    def __init__(self, children):
        self.children = children
        self.current = 0
        
    def tick(self):
        while self.current < len(self.children):
            status = self.children[self.current].tick()
            
            if status == BehaviorStatus.FAILURE:
                self.current = 0
                return BehaviorStatus.FAILURE
                
            elif status == BehaviorStatus.RUNNING:
                return BehaviorStatus.RUNNING
                
            self.current += 1
            
        self.current = 0
        return BehaviorStatus.SUCCESS
```

### 3. Hierarchical State Machines

```python
class State:
    def enter(self):
        """Called when entering state."""
        pass
        
    def execute(self):
        """Called every update."""
        pass
        
    def exit(self):
        """Called when leaving state."""
        pass

class StateMachine:
    def __init__(self):
        self.states = {}
        self.current_state = None
        
    def add_state(self, name, state):
        self.states[name] = state
        
    def transition(self, new_state_name):
        if self.current_state:
            self.current_state.exit()
            
        self.current_state = self.states[new_state_name]
        self.current_state.enter()
        
    def update(self):
        if self.current_state:
            self.current_state.execute()
```

## Best Practices

### 1. Separate Perception and Control

```python
# Good: Separate nodes
class PerceptionNode(Node):
    """Processes sensor data."""
    pass

class ControlNode(Node):
    """Makes decisions and controls actuators."""
    pass
```

### 2. Use Async for Slow Operations

```python
import asyncio

class AsyncAgent(Node):
    def __init__(self):
        super().__init__('async_agent')
        self.executor = rclpy.executors.MultiThreadedExecutor()
        
    async def slow_operation(self):
        """Long-running AI inference."""
        result = await self.call_llm_api()
        return result
```

### 3. Handle Failures Gracefully

```python
def decision_loop(self):
    try:
        decision = self.make_decision()
        self.execute(decision)
    except Exception as e:
        self.get_logger().error(f'Decision failed: {e}')
        # Fallback to safe behavior
        self.stop_robot()
```

## Summary

- Python AI agents integrate seamlessly with ROS 2 via `rclpy`
- Agents can be rule-based, ML-based, or LLM-powered
- The Sense-Think-Act loop is a fundamental pattern
- Separate perception from control for better modularity
- Handle failures gracefully with fallback behaviors
- Use async operations for slow AI inference

## Next Steps

In Module 2, we'll learn how to simulate these agents in Gazebo and Unity before deploying to real robots.

## Resources

- [rclpy API Documentation](https://docs.ros2.org/latest/api/rclpy/)
- [PyTorch](https://pytorch.org/)
- [OpenAI API](https://platform.openai.com/docs)
- [LangChain](https://python.langchain.com/)
