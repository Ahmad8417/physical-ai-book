---
sidebar_position: 2
title: "Isaac Sim Deep Dive"
---

# Isaac Sim: Photorealistic Robot Simulation

## Introduction

**Isaac Sim** is NVIDIA's flagship robotics simulator built on Omniverse. It combines photorealistic rendering, accurate physics, and AI capabilities to create the most advanced robot simulation platform available.

In this chapter, we'll explore:
- Advanced Isaac Sim features
- Creating custom robots and environments
- Synthetic data generation pipelines
- Sim-to-real transfer techniques
- Performance optimization

## Isaac Sim Core Concepts

### Universal Scene Description (USD)

**USD** is the foundation of Isaac Sim. It's a file format for describing 3D scenes.

**Key features**:
- **Composable**: Combine multiple USD files
- **Layered**: Non-destructive editing
- **Collaborative**: Multiple users can edit simultaneously
- **Scalable**: Handle massive scenes efficiently

### USD File Structure

```
scene.usd
├── /World
│   ├── /Ground
│   ├── /Robot
│   │   ├── /base_link
│   │   ├── /wheel_left
│   │   └── /wheel_right
│   ├── /Camera
│   └── /Lights
```

### Creating a USD Scene Programmatically

```python
from pxr import Usd, UsdGeom, Gf

# Create stage
stage = Usd.Stage.CreateNew("my_scene.usd")

# Create world
world = UsdGeom.Xform.Define(stage, "/World")

# Create ground plane
ground = UsdGeom.Mesh.Define(stage, "/World/Ground")
ground.CreatePointsAttr([
    (-10, -10, 0), (10, -10, 0),
    (10, 10, 0), (-10, 10, 0)
])
ground.CreateFaceVertexCountsAttr([4])
ground.CreateFaceVertexIndicesAttr([0, 1, 2, 3])

# Create a cube
cube = UsdGeom.Cube.Define(stage, "/World/Cube")
cube.AddTranslateOp().Set(Gf.Vec3d(0, 0, 1))
cube.CreateSizeAttr(1.0)

# Save
stage.Save()
print("Scene saved to my_scene.usd")
```

## Building Custom Robots

### Method 1: Import URDF

Isaac Sim can import URDF files directly:

```python
from omni.isaac.core.utils.stage import add_reference_to_stage
from omni.importer.urdf import _urdf

# Import URDF
urdf_path = "/path/to/robot.urdf"
imported_robot = _urdf.acquire_urdf_interface().parse_urdf(
    urdf_path,
    "/World/MyRobot"
)

print(f"Robot imported: {imported_robot}")
```

### Method 2: Build in Isaac Sim

Create a robot from scratch using USD:

```python
from omni.isaac.core import World
from omni.isaac.core.objects import DynamicCuboid, DynamicCylinder
from omni.isaac.core.articulations import Articulation
from pxr import UsdPhysics, PhysxSchema

# Create world
world = World()

# Create robot base
base = DynamicCuboid(
    prim_path="/World/Robot/base",
    name="base",
    position=[0, 0, 0.5],
    size=[0.6, 0.4, 0.2],
    color=[0.2, 0.2, 0.8],
    mass=10.0
)

# Create wheels
left_wheel = DynamicCylinder(
    prim_path="/World/Robot/left_wheel",
    name="left_wheel",
    position=[0, 0.25, 0.5],
    radius=0.1,
    height=0.05,
    color=[0.1, 0.1, 0.1],
    mass=1.0
)

right_wheel = DynamicCylinder(
    prim_path="/World/Robot/right_wheel",
    name="right_wheel",
    position=[0, -0.25, 0.5],
    radius=0.1,
    height=0.05,
    color=[0.1, 0.1, 0.1],
    mass=1.0
)

# Add to scene
world.scene.add(base)
world.scene.add(left_wheel)
world.scene.add(right_wheel)

# Create joints (requires USD API)
stage = world.stage

# Left wheel joint
left_joint = UsdPhysics.RevoluteJoint.Define(
    stage,
    "/World/Robot/left_wheel_joint"
)
left_joint.CreateBody0Rel().SetTargets(["/World/Robot/base"])
left_joint.CreateBody1Rel().SetTargets(["/World/Robot/left_wheel"])
left_joint.CreateAxisAttr("Y")

# Right wheel joint
right_joint = UsdPhysics.RevoluteJoint.Define(
    stage,
    "/World/Robot/right_wheel_joint"
)
right_joint.CreateBody0Rel().SetTargets(["/World/Robot/base"])
right_joint.CreateBody1Rel().SetTargets(["/World/Robot/right_wheel"])
right_joint.CreateAxisAttr("Y")

print("Custom robot created!")
```

## Advanced Sensor Simulation

### RGB-D Camera with Semantic Segmentation

```python
from omni.isaac.sensor import Camera
import omni.replicator.core as rep

# Create camera
camera = Camera(
    prim_path="/World/Camera",
    position=[2, 0, 1],
    frequency=30,
    resolution=(1280, 720)
)

# Setup replicator for annotations
render_product = rep.create.render_product(
    camera.get_prim_path(),
    (1280, 720)
)

# Add annotators
rgb_annotator = rep.AnnotatorRegistry.get_annotator("rgb")
depth_annotator = rep.AnnotatorRegistry.get_annotator("distance_to_camera")
semantic_annotator = rep.AnnotatorRegistry.get_annotator("semantic_segmentation")
instance_annotator = rep.AnnotatorRegistry.get_annotator("instance_segmentation")
bbox_2d_annotator = rep.AnnotatorRegistry.get_annotator("bounding_box_2d_tight")
bbox_3d_annotator = rep.AnnotatorRegistry.get_annotator("bounding_box_3d")

# Attach to render product
rgb_annotator.attach([render_product])
depth_annotator.attach([render_product])
semantic_annotator.attach([render_product])
instance_annotator.attach([render_product])
bbox_2d_annotator.attach([render_product])
bbox_3d_annotator.attach([render_product])

# Capture data
def capture_frame():
    """Capture all sensor data."""
    return {
        "rgb": rgb_annotator.get_data(),
        "depth": depth_annotator.get_data(),
        "semantic": semantic_annotator.get_data(),
        "instance": instance_annotator.get_data(),
        "bbox_2d": bbox_2d_annotator.get_data(),
        "bbox_3d": bbox_3d_annotator.get_data()
    }
```

### 3D LiDAR Simulation

```python
from omni.isaac.range_sensor import _range_sensor

# Create LiDAR
lidar_config = _range_sensor.acquire_lidar_sensor_interface()

# Configure LiDAR
lidar_path = "/World/Robot/Lidar"
lidar_config.add_lidar_sensor(
    lidar_path,
    parent_path="/World/Robot/base",
    min_range=0.4,
    max_range=100.0,
    draw_points=True,
    draw_lines=False,
    horizontal_fov=360.0,
    vertical_fov=30.0,
    horizontal_resolution=0.4,  # degrees
    vertical_resolution=2.0,    # degrees
    rotation_rate=20.0,         # Hz
    high_lod=True,
    yaw_offset=0.0,
    enable_semantics=True
)

# Read LiDAR data
def get_lidar_data():
    """Get point cloud from LiDAR."""
    data = lidar_config.get_linear_depth_data(lidar_path)
    # Returns array of distances
    return data
```

### Contact Sensors

```python
from omni.isaac.sensor import ContactSensor

# Create contact sensor on gripper
contact_sensor = ContactSensor(
    prim_path="/World/Robot/gripper/contact_sensor",
    min_threshold=0.0,
    max_threshold=10000000.0,
    radius=0.05
)

# Check for contact
def check_contact():
    """Check if gripper is touching something."""
    reading = contact_sensor.get_current_frame()
    is_contact = reading["is_contact"]
    force = reading["force"]
    
    if is_contact:
        print(f"Contact detected! Force: {force} N")
    
    return is_contact
```

## Creating Realistic Environments

### Warehouse Environment

```python
from omni.isaac.core.utils.stage import add_reference_to_stage
from omni.isaac.core.prims import XFormPrim
import random

def create_warehouse(world):
    """Create a warehouse environment."""
    
    # Add ground
    world.scene.add_default_ground_plane()
    
    # Add walls
    wall_height = 3.0
    wall_thickness = 0.2
    warehouse_size = 20.0
    
    # North wall
    north_wall = DynamicCuboid(
        prim_path="/World/Walls/North",
        position=[warehouse_size/2, 0, wall_height/2],
        size=[wall_thickness, warehouse_size, wall_height],
        color=[0.7, 0.7, 0.7],
        mass=1000.0
    )
    north_wall.set_collision_enabled(True)
    
    # Add shelving units
    for i in range(5):
        for j in range(3):
            x = -8 + i * 4
            y = -6 + j * 6
            
            shelf = add_reference_to_stage(
                usd_path="/Isaac/Environments/Simple_Warehouse/Props/S_TrafficCone.usd",
                prim_path=f"/World/Shelves/Shelf_{i}_{j}"
            )
            
            # Position shelf
            xform = XFormPrim(f"/World/Shelves/Shelf_{i}_{j}")
            xform.set_world_pose(position=[x, y, 0])
    
    # Add random boxes
    for i in range(20):
        x = random.uniform(-8, 8)
        y = random.uniform(-8, 8)
        z = random.uniform(0.5, 2.0)
        
        box = DynamicCuboid(
            prim_path=f"/World/Boxes/Box_{i}",
            position=[x, y, z],
            size=[0.4, 0.4, 0.4],
            color=[random.random(), random.random(), random.random()],
            mass=5.0
        )
        world.scene.add(box)
    
    print("Warehouse environment created!")
```

### Outdoor Terrain

```python
from omni.isaac.core.utils.prims import create_prim
from pxr import UsdGeom, Gf
import numpy as np

def create_terrain(world, size=50, resolution=100):
    """Create procedural terrain."""
    
    # Generate heightmap
    x = np.linspace(-size/2, size/2, resolution)
    y = np.linspace(-size/2, size/2, resolution)
    X, Y = np.meshgrid(x, y)
    
    # Perlin-like noise (simplified)
    Z = (
        np.sin(X * 0.1) * np.cos(Y * 0.1) * 2 +
        np.sin(X * 0.3) * np.cos(Y * 0.3) * 0.5
    )
    
    # Create mesh
    stage = world.stage
    terrain_path = "/World/Terrain"
    
    mesh = UsdGeom.Mesh.Define(stage, terrain_path)
    
    # Create vertices
    points = []
    for i in range(resolution):
        for j in range(resolution):
            points.append((X[i, j], Y[i, j], Z[i, j]))
    
    mesh.CreatePointsAttr(points)
    
    # Create faces (triangles)
    face_vertex_counts = []
    face_vertex_indices = []
    
    for i in range(resolution - 1):
        for j in range(resolution - 1):
            idx = i * resolution + j
            
            # Triangle 1
            face_vertex_counts.append(3)
            face_vertex_indices.extend([
                idx, idx + 1, idx + resolution
            ])
            
            # Triangle 2
            face_vertex_counts.append(3)
            face_vertex_indices.extend([
                idx + 1, idx + resolution + 1, idx + resolution
            ])
    
    mesh.CreateFaceVertexCountsAttr(face_vertex_counts)
    mesh.CreateFaceVertexIndicesAttr(face_vertex_indices)
    
    # Add collision
    UsdPhysics.CollisionAPI.Apply(mesh.GetPrim())
    
    print("Terrain created!")
```

## Domain Randomization Pipeline

### Complete Randomization System

```python
import random
from omni.isaac.core.utils.prims import get_prim_at_path
from pxr import Gf

class DomainRandomizer:
    """Comprehensive domain randomization."""
    
    def __init__(self, world):
        self.world = world
        self.stage = world.stage
        
    def randomize_lighting(self):
        """Randomize scene lighting."""
        light_path = "/World/defaultLight"
        light = get_prim_at_path(light_path)
        
        if light:
            # Random intensity
            intensity = random.uniform(500, 3000)
            light.GetAttribute("intensity").Set(intensity)
            
            # Random color temperature
            temp = random.uniform(2500, 8000)
            light.GetAttribute("colorTemperature").Set(temp)
            
            # Random position
            x = random.uniform(-10, 10)
            y = random.uniform(-10, 10)
            z = random.uniform(5, 15)
            light.GetAttribute("xformOp:translate").Set(Gf.Vec3d(x, y, z))
    
    def randomize_materials(self, prim_path):
        """Randomize object materials."""
        prim = get_prim_at_path(prim_path)
        
        if prim:
            # Random color
            r = random.random()
            g = random.random()
            b = random.random()
            
            # Apply to material
            # (Simplified - actual implementation more complex)
            pass
    
    def randomize_physics(self, prim_path):
        """Randomize physics properties."""
        prim = get_prim_at_path(prim_path)
        
        if prim:
            # Random mass
            mass_api = UsdPhysics.MassAPI.Apply(prim)
            mass = random.uniform(0.5, 2.0)
            mass_api.GetMassAttr().Set(mass)
            
            # Random friction
            material_api = UsdPhysics.MaterialAPI.Apply(prim)
            friction = random.uniform(0.2, 1.0)
            material_api.CreateStaticFrictionAttr(friction)
            material_api.CreateDynamicFrictionAttr(friction * 0.8)
    
    def randomize_camera(self, camera_path):
        """Randomize camera parameters."""
        camera = get_prim_at_path(camera_path)
        
        if camera:
            # Random exposure
            exposure = random.uniform(-2.0, 2.0)
            camera.GetAttribute("exposure").Set(exposure)
            
            # Random focal length
            focal_length = random.uniform(18, 50)
            camera.GetAttribute("focalLength").Set(focal_length)
    
    def randomize_all(self):
        """Apply all randomizations."""
        self.randomize_lighting()
        
        # Randomize all objects
        for prim in self.stage.Traverse():
            if prim.IsA(UsdGeom.Mesh):
                self.randomize_materials(prim.GetPath())
                self.randomize_physics(prim.GetPath())
        
        # Randomize cameras
        for prim in self.stage.Traverse():
            if prim.IsA(UsdGeom.Camera):
                self.randomize_camera(prim.GetPath())

# Usage
randomizer = DomainRandomizer(world)

for episode in range(1000):
    randomizer.randomize_all()
    # Run episode
    # ...
```

## Synthetic Data Generation

### Complete Data Collection Pipeline

```python
import os
import json
import numpy as np
from PIL import Image
import omni.replicator.core as rep

class SyntheticDataCollector:
    """Collect synthetic training data."""
    
    def __init__(self, output_dir="synthetic_data"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(f"{output_dir}/rgb", exist_ok=True)
        os.makedirs(f"{output_dir}/depth", exist_ok=True)
        os.makedirs(f"{output_dir}/semantic", exist_ok=True)
        os.makedirs(f"{output_dir}/labels", exist_ok=True)
        
        self.frame_count = 0
        
    def setup_annotators(self, camera):
        """Setup all annotators."""
        rp = rep.create.render_product(camera, (1280, 720))
        
        self.rgb = rep.AnnotatorRegistry.get_annotator("rgb")
        self.depth = rep.AnnotatorRegistry.get_annotator("distance_to_camera")
        self.semantic = rep.AnnotatorRegistry.get_annotator("semantic_segmentation")
        self.bbox_2d = rep.AnnotatorRegistry.get_annotator("bounding_box_2d_tight")
        
        self.rgb.attach([rp])
        self.depth.attach([rp])
        self.semantic.attach([rp])
        self.bbox_2d.attach([rp])
    
    def capture_frame(self):
        """Capture and save one frame."""
        # Get data
        rgb_data = self.rgb.get_data()
        depth_data = self.depth.get_data()
        semantic_data = self.semantic.get_data()
        bbox_data = self.bbox_2d.get_data()
        
        # Save RGB
        rgb_image = Image.fromarray(rgb_data)
        rgb_image.save(f"{self.output_dir}/rgb/frame_{self.frame_count:06d}.png")
        
        # Save depth
        depth_normalized = (depth_data / depth_data.max() * 255).astype(np.uint8)
        depth_image = Image.fromarray(depth_normalized)
        depth_image.save(f"{self.output_dir}/depth/frame_{self.frame_count:06d}.png")
        
        # Save semantic
        semantic_image = Image.fromarray(semantic_data.astype(np.uint8))
        semantic_image.save(f"{self.output_dir}/semantic/frame_{self.frame_count:06d}.png")
        
        # Save bounding boxes (COCO format)
        annotations = {
            "image_id": self.frame_count,
            "file_name": f"frame_{self.frame_count:06d}.png",
            "annotations": []
        }
        
        if bbox_data:
            for bbox in bbox_data:
                annotations["annotations"].append({
                    "bbox": bbox["bbox"],
                    "category_id": bbox["semanticId"],
                    "area": bbox["bbox"][2] * bbox["bbox"][3]
                })
        
        with open(f"{self.output_dir}/labels/frame_{self.frame_count:06d}.json", "w") as f:
            json.dump(annotations, f)
        
        self.frame_count += 1
        
        return self.frame_count
    
    def generate_dataset(self, world, randomizer, num_frames=1000):
        """Generate complete dataset."""
        print(f"Generating {num_frames} frames...")
        
        for i in range(num_frames):
            # Randomize scene
            randomizer.randomize_all()
            
            # Step simulation
            world.step(render=True)
            
            # Capture frame
            self.capture_frame()
            
            if i % 100 == 0:
                print(f"Progress: {i}/{num_frames} frames")
        
        print(f"Dataset complete! {self.frame_count} frames saved to {self.output_dir}")

# Usage
collector = SyntheticDataCollector(output_dir="training_data")
collector.setup_annotators(camera)
collector.generate_dataset(world, randomizer, num_frames=10000)
```

## Sim-to-Real Transfer

### Best Practices

1. **Match Real Sensor Specs**
```python
# Real camera: Logitech C920
camera = Camera(
    resolution=(1920, 1080),
    frequency=30,
    horizontal_fov=78.0  # degrees
)
```

2. **Add Realistic Noise**
```python
# Camera noise
camera.add_motion_blur(intensity=0.5)
camera.add_gaussian_noise(mean=0.0, std=0.01)

# LiDAR noise
lidar.add_distance_noise(std=0.02)  # 2cm
```

3. **Domain Randomization**
- Vary lighting extensively
- Randomize textures and colors
- Add distractors and clutter
- Vary object poses

4. **Physics Tuning**
```python
# Match real robot dynamics
robot.set_joint_friction([0.1, 0.1, 0.1])
robot.set_joint_damping([0.5, 0.5, 0.5])
```

## Performance Optimization

### Multi-GPU Training

```python
import torch.distributed as dist

# Initialize distributed training
dist.init_process_group(backend="nccl")

# Create multiple Isaac Sim instances
num_gpus = torch.cuda.device_count()
envs_per_gpu = 4

for gpu_id in range(num_gpus):
    with torch.cuda.device(gpu_id):
        # Create environments on this GPU
        for env_id in range(envs_per_gpu):
            world = World(f"/World_GPU{gpu_id}_Env{env_id}")
            # Setup environment
```

### Headless Rendering

```python
# Maximum performance
simulation_app = SimulationApp({
    "headless": True,
    "width": 1280,
    "height": 720,
    "anti_aliasing": 0,
    "samples_per_pixel": 1,
    "denoiser": False,
    "subdiv_refinement_level": 0,
    "renderer": "RayTracedLighting",
    "experience": "omni.isaac.sim.python.kit"
})
```

## Summary

- Isaac Sim uses **USD** for scene description
- Create custom robots via **URDF import** or **programmatic USD**
- Advanced sensors include **RGB-D**, **3D LiDAR**, and **contact sensors**
- **Domain randomization** improves sim-to-real transfer
- **Synthetic data generation** trains vision models at scale
- Optimize with **headless mode** and **multi-GPU** setups

## Next Steps

In the next chapter, we'll explore navigation with Visual SLAM and path planning.

## Resources

- [Isaac Sim Python API](https://docs.omniverse.nvidia.com/py/isaacsim/)
- [USD Documentation](https://graphics.pixar.com/usd/docs/index.html)
- [Replicator Documentation](https://docs.omniverse.nvidia.com/prod_extensions/prod_extensions/ext_replicator.html)
