---
sidebar_position: 3
title: "Sensor Simulation"
---

# Sensor Simulation: The Robot's Senses

## Introduction

Sensors are how robots perceive the world. In simulation, we can create perfect virtual sensors or add realistic noise and imperfections to match real hardware.

**Common robot sensors**:
- **Cameras**: Visual perception
- **LiDAR**: Distance measurement (laser scanning)
- **IMU**: Orientation and acceleration
- **GPS**: Global positioning
- **Depth Cameras**: 3D vision (RGB-D)
- **Force/Torque**: Contact sensing

## Why Simulate Sensors?

1. **Test perception algorithms** before hardware arrives
2. **Generate synthetic training data** for ML models
3. **Validate sensor fusion** algorithms
4. **Test edge cases** (sensor failures, extreme conditions)
5. **Rapid prototyping** of sensor configurations

## Camera Simulation

Cameras are the most common robot sensor for vision-based AI.

### Adding a Camera in SDF

```xml
<model name="camera_robot">
  <link name="base_link">
    <!-- Base robot geometry -->
  </link>
  
  <!-- Camera link -->
  <link name="camera_link">
    <pose>0.3 0 0.2 0 0 0</pose>  <!-- Front of robot -->
    
    <visual name="visual">
      <geometry>
        <box><size>0.05 0.05 0.05</size></box>
      </geometry>
      <material>
        <ambient>0.1 0.1 0.1 1</ambient>
      </material>
    </visual>
    
    <!-- Camera sensor -->
    <sensor name="camera" type="camera">
      <camera>
        <horizontal_fov>1.047</horizontal_fov>  <!-- 60 degrees -->
        <image>
          <width>640</width>
          <height>480</height>
          <format>R8G8B8</format>  <!-- RGB -->
        </image>
        <clip>
          <near>0.1</near>   <!-- Min distance -->
          <far>100.0</far>   <!-- Max distance -->
        </clip>
        <noise>
          <type>gaussian</type>
          <mean>0.0</mean>
          <stddev>0.007</stddev>  <!-- Realistic noise -->
        </noise>
      </camera>
      <always_on>1</always_on>
      <update_rate>30</update_rate>  <!-- 30 FPS -->
      <visualize>true</visualize>
      <topic>camera/image</topic>
    </sensor>
  </link>
  
  <!-- Joint connecting camera to base -->
  <joint name="camera_joint" type="fixed">
    <parent>base_link</parent>
    <child>camera_link</child>
  </joint>
</model>
```

### Reading Camera Data in ROS 2

```python
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2


class CameraSubscriber(Node):
    """Subscribe to simulated camera images."""
    
    def __init__(self):
        super().__init__('camera_subscriber')
        
        # CV Bridge for ROS-OpenCV conversion
        self.bridge = CvBridge()
        
        # Subscribe to camera topic
        self.subscription = self.create_subscription(
            Image,
            '/camera/image',
            self.image_callback,
            10
        )
        
        self.get_logger().info('Camera subscriber started')
        
    def image_callback(self, msg):
        """Process incoming camera images."""
        try:
            # Convert ROS Image to OpenCV format
            cv_image = self.bridge.imgmsg_to_cv2(msg, 'bgr8')
            
            # Process image (example: edge detection)
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            
            # Display
            cv2.imshow('Camera Feed', cv_image)
            cv2.imshow('Edges', edges)
            cv2.waitKey(1)
            
            self.get_logger().debug(
                f'Image: {msg.width}x{msg.height}, '
                f'encoding: {msg.encoding}'
            )
            
        except Exception as e:
            self.get_logger().error(f'Image processing error: {e}')


def main(args=None):
    rclpy.init(args=args)
    node = CameraSubscriber()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
```

### Camera Parameters Explained

**Field of View (FOV)**: How wide the camera sees
- Wide angle: 90-120° (security cameras)
- Normal: 60-80° (human-like)
- Telephoto: 20-40° (zoom lens)

**Resolution**: Image size in pixels
- Low: 320x240 (fast processing)
- Medium: 640x480 (standard)
- High: 1920x1080 (HD, slower)

**Frame Rate**: Images per second
- 10 FPS: Slow-moving robots
- 30 FPS: Standard
- 60+ FPS: Fast-moving robots

## LiDAR Simulation

**LiDAR (Light Detection and Ranging)** measures distances using laser beams.

### 2D LiDAR (Laser Scanner)

```xml
<sensor name="lidar" type="gpu_lidar">
  <pose>0 0 0.2 0 0 0</pose>
  
  <lidar>
    <scan>
      <horizontal>
        <samples>360</samples>        <!-- 360 rays -->
        <resolution>1.0</resolution>
        <min_angle>-3.14159</min_angle>  <!-- -180° -->
        <max_angle>3.14159</max_angle>   <!-- +180° -->
      </horizontal>
    </scan>
    
    <range>
      <min>0.1</min>   <!-- 10 cm minimum -->
      <max>10.0</max>  <!-- 10 m maximum -->
      <resolution>0.01</resolution>  <!-- 1 cm accuracy -->
    </range>
    
    <noise>
      <type>gaussian</type>
      <mean>0.0</mean>
      <stddev>0.01</stddev>  <!-- 1 cm noise -->
    </noise>
  </lidar>
  
  <always_on>1</always_on>
  <update_rate>10</update_rate>  <!-- 10 Hz -->
  <visualize>true</visualize>
  <topic>scan</topic>
</sensor>
```

### Reading LiDAR Data

```python
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
import numpy as np
import matplotlib.pyplot as plt


class LidarVisualizer(Node):
    """Visualize LiDAR scans."""
    
    def __init__(self):
        super().__init__('lidar_visualizer')
        
        self.subscription = self.create_subscription(
            LaserScan,
            '/scan',
            self.scan_callback,
            10
        )
        
        # Setup matplotlib for live plotting
        plt.ion()
        self.fig, self.ax = plt.subplots(subplot_kw={'projection': 'polar'})
        
        self.get_logger().info('LiDAR visualizer started')
        
    def scan_callback(self, msg):
        """Process and visualize LiDAR scan."""
        # Extract ranges and angles
        ranges = np.array(msg.ranges)
        angles = np.linspace(
            msg.angle_min,
            msg.angle_max,
            len(ranges)
        )
        
        # Filter invalid readings
        valid_indices = (ranges >= msg.range_min) & (ranges <= msg.range_max)
        valid_ranges = ranges[valid_indices]
        valid_angles = angles[valid_indices]
        
        # Find closest obstacle
        if len(valid_ranges) > 0:
            min_distance = np.min(valid_ranges)
            min_angle = valid_angles[np.argmin(valid_ranges)]
            
            self.get_logger().info(
                f'Closest obstacle: {min_distance:.2f}m at '
                f'{np.degrees(min_angle):.1f}°'
            )
        
        # Plot
        self.ax.clear()
        self.ax.plot(valid_angles, valid_ranges, 'b.')
        self.ax.set_ylim(0, msg.range_max)
        self.ax.set_title('LiDAR Scan')
        plt.draw()
        plt.pause(0.001)


def main(args=None):
    rclpy.init(args=args)
    node = LidarVisualizer()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
```

### 3D LiDAR (Point Cloud)

For 3D perception:

```xml
<sensor name="lidar_3d" type="gpu_lidar">
  <lidar>
    <scan>
      <horizontal>
        <samples>1800</samples>
        <resolution>1.0</resolution>
        <min_angle>-3.14159</min_angle>
        <max_angle>3.14159</max_angle>
      </horizontal>
      <vertical>
        <samples>16</samples>  <!-- 16 vertical layers -->
        <resolution>1.0</resolution>
        <min_angle>-0.2618</min_angle>  <!-- -15° -->
        <max_angle>0.2618</max_angle>   <!-- +15° -->
      </vertical>
    </scan>
    <range>
      <min>0.5</min>
      <max>100.0</max>
    </range>
  </lidar>
  <update_rate>10</update_rate>
  <topic>point_cloud</topic>
</sensor>
```

## IMU Simulation

**IMU (Inertial Measurement Unit)** measures acceleration and rotation.

### Adding an IMU

```xml
<sensor name="imu" type="imu">
  <pose>0 0 0 0 0 0</pose>
  
  <imu>
    <angular_velocity>
      <x>
        <noise type="gaussian">
          <mean>0.0</mean>
          <stddev>0.009</stddev>
        </noise>
      </x>
      <y>
        <noise type="gaussian">
          <mean>0.0</mean>
          <stddev>0.009</stddev>
        </noise>
      </y>
      <z>
        <noise type="gaussian">
          <mean>0.0</mean>
          <stddev>0.009</stddev>
        </noise>
      </z>
    </angular_velocity>
    
    <linear_acceleration>
      <x>
        <noise type="gaussian">
          <mean>0.0</mean>
          <stddev>0.017</stddev>
        </noise>
      </x>
      <y>
        <noise type="gaussian">
          <mean>0.0</mean>
          <stddev>0.017</stddev>
        </noise>
      </y>
      <z>
        <noise type="gaussian">
          <mean>0.0</mean>
          <stddev>0.017</stddev>
        </noise>
      </z>
    </linear_acceleration>
  </imu>
  
  <always_on>1</always_on>
  <update_rate>100</update_rate>  <!-- 100 Hz -->
  <topic>imu</topic>
</sensor>
```

### Reading IMU Data

```python
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu
import numpy as np


class ImuMonitor(Node):
    """Monitor IMU data for robot stability."""
    
    def __init__(self):
        super().__init__('imu_monitor')
        
        self.subscription = self.create_subscription(
            Imu,
            '/imu',
            self.imu_callback,
            10
        )
        
        self.get_logger().info('IMU monitor started')
        
    def imu_callback(self, msg):
        """Process IMU data."""
        # Linear acceleration
        accel = msg.linear_acceleration
        accel_magnitude = np.sqrt(
            accel.x**2 + accel.y**2 + accel.z**2
        )
        
        # Angular velocity
        gyro = msg.angular_velocity
        rotation_rate = np.sqrt(
            gyro.x**2 + gyro.y**2 + gyro.z**2
        )
        
        # Orientation (quaternion)
        orientation = msg.orientation
        
        # Check for instability
        if accel_magnitude > 15.0:  # More than 1.5g
            self.get_logger().warn(
                f'High acceleration detected: {accel_magnitude:.2f} m/s²'
            )
        
        if rotation_rate > 2.0:  # Fast rotation
            self.get_logger().warn(
                f'Fast rotation detected: {rotation_rate:.2f} rad/s'
            )
        
        # Log periodically
        self.get_logger().debug(
            f'Accel: {accel_magnitude:.2f} m/s², '
            f'Rotation: {rotation_rate:.2f} rad/s'
        )


def main(args=None):
    rclpy.init(args=args)
    node = ImuMonitor()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
```

## Depth Camera (RGB-D)

Depth cameras provide both color images and depth information.

### Adding a Depth Camera

```xml
<sensor name="depth_camera" type="depth_camera">
  <camera>
    <horizontal_fov>1.047</horizontal_fov>
    <image>
      <width>640</width>
      <height>480</height>
      <format>R8G8B8</format>
    </image>
    <clip>
      <near>0.1</near>
      <far>10.0</far>
    </clip>
  </camera>
  
  <always_on>1</always_on>
  <update_rate>30</update_rate>
  <visualize>true</visualize>
  
  <!-- Publish both RGB and depth -->
  <topic>camera/image</topic>
  <depth_camera>
    <output>depths</output>
    <clip>
      <near>0.1</near>
      <far>10.0</far>
    </clip>
  </depth_camera>
</sensor>
```

### Processing Depth Data

```python
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import numpy as np


class DepthProcessor(Node):
    """Process RGB-D camera data."""
    
    def __init__(self):
        super().__init__('depth_processor')
        
        self.bridge = CvBridge()
        
        # Subscribe to RGB and depth
        self.rgb_sub = self.create_subscription(
            Image,
            '/camera/image',
            self.rgb_callback,
            10
        )
        
        self.depth_sub = self.create_subscription(
            Image,
            '/camera/depth',
            self.depth_callback,
            10
        )
        
        self.latest_rgb = None
        self.latest_depth = None
        
    def rgb_callback(self, msg):
        """Store latest RGB image."""
        self.latest_rgb = self.bridge.imgmsg_to_cv2(msg, 'bgr8')
        
    def depth_callback(self, msg):
        """Process depth image."""
        # Convert to numpy array
        depth_image = self.bridge.imgmsg_to_cv2(msg, '32FC1')
        
        # Normalize for visualization
        depth_normalized = cv2.normalize(
            depth_image,
            None,
            0, 255,
            cv2.NORM_MINMAX,
            cv2.CV_8U
        )
        
        # Apply colormap
        depth_colormap = cv2.applyColorMap(
            depth_normalized,
            cv2.COLORMAP_JET
        )
        
        # Find closest point
        valid_depths = depth_image[depth_image > 0]
        if len(valid_depths) > 0:
            min_depth = np.min(valid_depths)
            self.get_logger().info(f'Closest object: {min_depth:.2f}m')
        
        # Display
        if self.latest_rgb is not None:
            combined = np.hstack([self.latest_rgb, depth_colormap])
            cv2.imshow('RGB-D', combined)
            cv2.waitKey(1)


def main(args=None):
    rclpy.init(args=args)
    node = DepthProcessor()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
```

## Sensor Fusion Example

Combining multiple sensors for robust perception:

```python
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan, Imu, Image
from geometry_msgs.msg import Twist
import numpy as np


class SensorFusionNode(Node):
    """Fuse LiDAR, IMU, and camera for navigation."""
    
    def __init__(self):
        super().__init__('sensor_fusion')
        
        # Subscribers
        self.lidar_sub = self.create_subscription(
            LaserScan, '/scan', self.lidar_callback, 10
        )
        self.imu_sub = self.create_subscription(
            Imu, '/imu', self.imu_callback, 10
        )
        self.camera_sub = self.create_subscription(
            Image, '/camera/image', self.camera_callback, 10
        )
        
        # Publisher
        self.vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        
        # State
        self.min_distance = float('inf')
        self.is_stable = True
        self.obstacle_detected = False
        
        # Control loop
        self.timer = self.create_timer(0.1, self.control_loop)
        
    def lidar_callback(self, msg):
        """Process LiDAR data."""
        valid_ranges = [
            r for r in msg.ranges
            if msg.range_min < r < msg.range_max
        ]
        if valid_ranges:
            self.min_distance = min(valid_ranges)
            
    def imu_callback(self, msg):
        """Check robot stability."""
        accel = msg.linear_acceleration
        total_accel = np.sqrt(
            accel.x**2 + accel.y**2 + accel.z**2
        )
        # Stable if close to gravity
        self.is_stable = abs(total_accel - 9.81) < 2.0
        
    def camera_callback(self, msg):
        """Detect obstacles in camera (simplified)."""
        # In real implementation, use object detection
        # For now, just a placeholder
        self.obstacle_detected = False
        
    def control_loop(self):
        """Fused decision making."""
        cmd = Twist()
        
        # Safety first: check stability
        if not self.is_stable:
            self.get_logger().warn('Robot unstable! Stopping.')
            cmd.linear.x = 0.0
            cmd.angular.z = 0.0
            self.vel_pub.publish(cmd)
            return
        
        # Obstacle avoidance from LiDAR
        if self.min_distance < 0.5:
            # Emergency stop
            cmd.linear.x = 0.0
            cmd.angular.z = 0.5  # Turn
            self.get_logger().info('LiDAR: Obstacle close, turning')
            
        elif self.min_distance < 1.0:
            # Slow down
            cmd.linear.x = 0.2
            cmd.angular.z = 0.0
            self.get_logger().info('LiDAR: Obstacle nearby, slowing')
            
        elif self.obstacle_detected:
            # Camera detected something
            cmd.linear.x = 0.3
            cmd.angular.z = 0.0
            self.get_logger().info('Camera: Obstacle detected')
            
        else:
            # All clear
            cmd.linear.x = 0.5
            cmd.angular.z = 0.0
            
        self.vel_pub.publish(cmd)


def main(args=None):
    rclpy.init(args=args)
    node = SensorFusionNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
```

## Sensor Noise Models

Real sensors are noisy. Add realistic noise for better sim-to-real transfer.

### Gaussian Noise

Most common, models random errors:

```xml
<noise>
  <type>gaussian</type>
  <mean>0.0</mean>
  <stddev>0.01</stddev>  <!-- Standard deviation -->
</noise>
```

### Custom Noise in Python

```python
import numpy as np

def add_sensor_noise(measurement, noise_std):
    """Add Gaussian noise to sensor reading."""
    noise = np.random.normal(0, noise_std)
    return measurement + noise

# Example
true_distance = 5.0  # meters
noisy_distance = add_sensor_noise(true_distance, 0.05)
print(f'True: {true_distance}m, Measured: {noisy_distance:.3f}m')
```

## Synthetic Data Generation

Use simulation to generate training data for ML models.

### Collecting Camera Data

```python
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import os


class DataCollector(Node):
    """Collect synthetic training data."""
    
    def __init__(self, output_dir='dataset'):
        super().__init__('data_collector')
        
        self.bridge = CvBridge()
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        self.subscription = self.create_subscription(
            Image,
            '/camera/image',
            self.image_callback,
            10
        )
        
        self.frame_count = 0
        
    def image_callback(self, msg):
        """Save images to disk."""
        cv_image = self.bridge.imgmsg_to_cv2(msg, 'bgr8')
        
        # Save every 10th frame
        if self.frame_count % 10 == 0:
            filename = os.path.join(
                self.output_dir,
                f'frame_{self.frame_count:06d}.jpg'
            )
            cv2.imwrite(filename, cv_image)
            self.get_logger().info(f'Saved {filename}')
        
        self.frame_count += 1


def main(args=None):
    rclpy.init(args=args)
    node = DataCollector(output_dir='synthetic_data')
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    
    node.get_logger().info(
        f'Collected {node.frame_count} frames'
    )
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
```

## Best Practices

### 1. Match Real Sensor Specs

Use realistic parameters:
- Camera: 30 FPS, 640x480, 60° FOV
- LiDAR: 10 Hz, 0.1-10m range, 1° resolution
- IMU: 100 Hz, realistic noise levels

### 2. Add Appropriate Noise

Too clean = poor sim-to-real transfer
Too noisy = algorithms fail

**Start with**: 1-2% noise, tune based on real sensor specs

### 3. Optimize Update Rates

Higher rates = more CPU usage:
- IMU: 100 Hz (fast dynamics)
- LiDAR: 10-20 Hz (standard)
- Camera: 30 Hz (video rate)
- GPS: 1-10 Hz (slow)

### 4. Visualize Sensor Data

Always visualize to catch issues:
```bash
# RViz for visualization
ros2 run rviz2 rviz2

# Add displays for:
# - Camera → Image
# - LaserScan → LaserScan
# - PointCloud2 → PointCloud2
```

## Summary

- Sensors give robots perception of their environment
- **Cameras** for vision, **LiDAR** for distance, **IMU** for orientation
- Add realistic **noise** for better sim-to-real transfer
- **Sensor fusion** combines multiple sensors for robust perception
- Use simulation to generate **synthetic training data**
- Match simulated sensor specs to real hardware

## Next Steps

In Module 3, we'll explore NVIDIA Isaac for advanced simulation and AI-powered robotics.

## Resources

- [Gazebo Sensor Documentation](https://gazebosim.org/api/sensors/7/index.html)
- [ROS 2 Sensor Messages](https://github.com/ros2/common_interfaces/tree/rolling/sensor_msgs)
- [OpenCV Python Tutorials](https://docs.opencv.org/4.x/d6/d00/tutorial_py_root.html)
- [Point Cloud Library (PCL)](https://pointclouds.org/)
