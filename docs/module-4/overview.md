---
sidebar_position: 1
title: "Vision-Language-Action Overview"
---

# Module 4: Vision-Language-Action (VLA)

## Introduction

**Vision-Language-Action (VLA)** models represent the cutting edge of AI robotics. They combine:
- **Vision**: Understanding what the robot sees
- **Language**: Understanding human instructions
- **Action**: Executing physical tasks

VLA models enable robots to understand natural language commands like "pick up the red cup" and translate them into physical actions.

## The VLA Revolution

Traditional robots require:
- Explicit programming for each task
- Predefined motion primitives
- Structured environments

**VLA-powered robots** can:
- Understand natural language instructions
- Generalize to new objects and scenarios
- Learn from demonstrations
- Reason about their actions

```
┌─────────────────────────────────────────────────────┐
│              VLA Model Architecture                 │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Camera Image ──┐                                   │
│                 │                                   │
│                 ├──► Vision Encoder                 │
│                 │    (CNN/ViT)                      │
│  Voice Command ─┤         ↓                         │
│                 │                                   │
│                 ├──► Language Model                 │
│                 │    (LLM/Transformer)              │
│  Robot State ───┘         ↓                         │
│                                                     │
│                    Action Decoder                   │
│                    (Policy Network)                 │
│                           ↓                         │
│                    Robot Actions                    │
│                    (Joint positions,                │
│                     velocities)                     │
│                                                     │
└─────────────────────────────────────────────────────┘
```

## How VLA Models Work

### 1. Vision Component

Processes camera images to understand the scene:

```python
import torch
import torchvision.models as models
from PIL import Image
import torchvision.transforms as transforms


class VisionEncoder:
    """Encode visual observations."""
    
    def __init__(self):
        # Use pre-trained ResNet
        self.model = models.resnet50(pretrained=True)
        
        # Remove final classification layer
        self.model = torch.nn.Sequential(
            *list(self.model.children())[:-1]
        )
        
        self.model.eval()
        
        # Image preprocessing
        self.transform = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])
    
    def encode(self, image):
        """
        Encode image to feature vector.
        
        Args:
            image: PIL Image or numpy array
        
        Returns:
            Feature vector (2048-dim)
        """
        if not isinstance(image, Image.Image):
            image = Image.fromarray(image)
        
        # Preprocess
        img_tensor = self.transform(image).unsqueeze(0)
        
        # Encode
        with torch.no_grad():
            features = self.model(img_tensor)
        
        # Flatten
        features = features.squeeze()
        
        return features.numpy()
```

### 2. Language Component

Processes natural language instructions:

```python
from transformers import AutoTokenizer, AutoModel
import torch


class LanguageEncoder:
    """Encode language instructions."""
    
    def __init__(self, model_name='sentence-transformers/all-MiniLM-L6-v2'):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)
        self.model.eval()
    
    def encode(self, text):
        """
        Encode text to embedding vector.
        
        Args:
            text: String instruction
        
        Returns:
            Embedding vector (384-dim)
        """
        # Tokenize
        inputs = self.tokenizer(
            text,
            return_tensors='pt',
            padding=True,
            truncation=True,
            max_length=128
        )
        
        # Encode
        with torch.no_grad():
            outputs = self.model(**inputs)
        
        # Mean pooling
        embeddings = outputs.last_hidden_state.mean(dim=1)
        
        return embeddings.squeeze().numpy()
```

### 3. Action Component

Generates robot actions:

```python
import torch
import torch.nn as nn


class ActionDecoder(nn.Module):
    """Decode multimodal features to robot actions."""
    
    def __init__(self, vision_dim=2048, language_dim=384, action_dim=7):
        super().__init__()
        
        # Fusion layer
        self.fusion = nn.Sequential(
            nn.Linear(vision_dim + language_dim, 512),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(512, 256),
            nn.ReLU()
        )
        
        # Action head
        self.action_head = nn.Sequential(
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Linear(128, action_dim),
            nn.Tanh()  # Normalize actions to [-1, 1]
        )
    
    def forward(self, vision_features, language_features):
        """
        Generate actions from vision and language.
        
        Args:
            vision_features: (batch, vision_dim)
            language_features: (batch, language_dim)
        
        Returns:
            actions: (batch, action_dim)
        """
        # Concatenate features
        combined = torch.cat([vision_features, language_features], dim=1)
        
        # Fuse
        fused = self.fusion(combined)
        
        # Generate actions
        actions = self.action_head(fused)
        
        return actions
```

## Complete VLA System

```python
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, JointState
from std_msgs.msg import String
from cv_bridge import CvBridge
import numpy as np
import torch


class VLAController(Node):
    """Complete VLA-based robot controller."""
    
    def __init__(self):
        super().__init__('vla_controller')
        
        # Initialize encoders
        self.vision_encoder = VisionEncoder()
        self.language_encoder = LanguageEncoder()
        
        # Initialize action decoder
        self.action_decoder = ActionDecoder()
        self.action_decoder.load_state_dict(
            torch.load('vla_model.pth')
        )
        self.action_decoder.eval()
        
        # ROS interfaces
        self.bridge = CvBridge()
        
        self.image_sub = self.create_subscription(
            Image,
            '/camera/image',
            self.image_callback,
            10
        )
        
        self.command_sub = self.create_subscription(
            String,
            '/voice_command',
            self.command_callback,
            10
        )
        
        self.joint_pub = self.create_publisher(
            JointState,
            '/joint_commands',
            10
        )
        
        # State
        self.latest_image = None
        self.current_command = None
        
        # Control loop
        self.timer = self.create_timer(0.1, self.control_loop)
        
        self.get_logger().info('VLA Controller initialized')
    
    def image_callback(self, msg):
        """Store latest camera image."""
        self.latest_image = self.bridge.imgmsg_to_cv2(msg, 'rgb8')
    
    def command_callback(self, msg):
        """Receive voice command."""
        self.current_command = msg.data
        self.get_logger().info(f'Command: {self.current_command}')
    
    def control_loop(self):
        """Main VLA control loop."""
        if self.latest_image is None or self.current_command is None:
            return
        
        # Encode vision
        vision_features = self.vision_encoder.encode(self.latest_image)
        vision_tensor = torch.FloatTensor(vision_features).unsqueeze(0)
        
        # Encode language
        language_features = self.language_encoder.encode(self.current_command)
        language_tensor = torch.FloatTensor(language_features).unsqueeze(0)
        
        # Generate actions
        with torch.no_grad():
            actions = self.action_decoder(vision_tensor, language_tensor)
        
        actions = actions.squeeze().numpy()
        
        # Publish joint commands
        joint_msg = JointState()
        joint_msg.header.stamp = self.get_clock().now().to_msg()
        joint_msg.name = [
            'joint1', 'joint2', 'joint3', 'joint4',
            'joint5', 'joint6', 'joint7'
        ]
        joint_msg.position = actions.tolist()
        
        self.joint_pub.publish(joint_msg)
        
        self.get_logger().debug(f'Actions: {actions}')


def main(args=None):
    rclpy.init(args=args)
    controller = VLAController()
    rclpy.spin(controller)
    controller.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
```

## State-of-the-Art VLA Models

### 1. RT-1 (Robotics Transformer)

Google's VLA model trained on 130k robot demonstrations.

**Key features**:
- Transformer architecture
- Multi-task learning
- Generalizes to new objects

### 2. RT-2 (Robotics Transformer 2)

Combines vision-language models with robot control.

**Key features**:
- Built on PaLM-E
- Web-scale training data
- Emergent reasoning capabilities

### 3. OpenVLA

Open-source VLA model from Stanford.

**Installation**:
```bash
pip install openvla
```

**Usage**:
```python
from openvla import OpenVLA

# Load model
model = OpenVLA.from_pretrained("openvla-7b")

# Generate action
action = model.predict(
    image=camera_image,
    instruction="pick up the red block"
)
```

## Training a VLA Model

### Data Collection

```python
import h5py
import numpy as np


class VLADataCollector:
    """Collect training data for VLA model."""
    
    def __init__(self, output_file='vla_dataset.h5'):
        self.output_file = output_file
        self.episodes = []
    
    def start_episode(self):
        """Start a new episode."""
        self.current_episode = {
            'images': [],
            'actions': [],
            'instruction': None
        }
    
    def add_step(self, image, action):
        """Add a step to current episode."""
        self.current_episode['images'].append(image)
        self.current_episode['actions'].append(action)
    
    def end_episode(self, instruction):
        """End episode and save."""
        self.current_episode['instruction'] = instruction
        self.episodes.append(self.current_episode)
        self.current_episode = None
    
    def save(self):
        """Save dataset to HDF5."""
        with h5py.File(self.output_file, 'w') as f:
            for i, episode in enumerate(self.episodes):
                grp = f.create_group(f'episode_{i}')
                
                # Save images
                images = np.array(episode['images'])
                grp.create_dataset('images', data=images)
                
                # Save actions
                actions = np.array(episode['actions'])
                grp.create_dataset('actions', data=actions)
                
                # Save instruction
                grp.attrs['instruction'] = episode['instruction']
        
        print(f'Saved {len(self.episodes)} episodes to {self.output_file}')
```

### Training Loop

```python
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader


class VLADataset(Dataset):
    """Dataset for VLA training."""
    
    def __init__(self, h5_file):
        self.file = h5py.File(h5_file, 'r')
        self.episodes = list(self.file.keys())
    
    def __len__(self):
        return len(self.episodes)
    
    def __getitem__(self, idx):
        episode = self.file[self.episodes[idx]]
        
        # Random timestep
        t = np.random.randint(len(episode['images']))
        
        image = episode['images'][t]
        action = episode['actions'][t]
        instruction = episode.attrs['instruction']
        
        return {
            'image': torch.FloatTensor(image),
            'instruction': instruction,
            'action': torch.FloatTensor(action)
        }


def train_vla_model(model, dataset, epochs=100):
    """Train VLA model."""
    dataloader = DataLoader(dataset, batch_size=32, shuffle=True)
    
    optimizer = optim.Adam(model.parameters(), lr=1e-4)
    criterion = nn.MSELoss()
    
    vision_encoder = VisionEncoder()
    language_encoder = LanguageEncoder()
    
    for epoch in range(epochs):
        total_loss = 0
        
        for batch in dataloader:
            # Encode inputs
            vision_features = []
            language_features = []
            
            for i in range(len(batch['image'])):
                img = batch['image'][i].numpy()
                text = batch['instruction'][i]
                
                vision_features.append(vision_encoder.encode(img))
                language_features.append(language_encoder.encode(text))
            
            vision_tensor = torch.FloatTensor(vision_features)
            language_tensor = torch.FloatTensor(language_features)
            actions_target = batch['action']
            
            # Forward pass
            actions_pred = model(vision_tensor, language_tensor)
            
            # Compute loss
            loss = criterion(actions_pred, actions_target)
            
            # Backward pass
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
        
        avg_loss = total_loss / len(dataloader)
        print(f'Epoch {epoch+1}/{epochs}, Loss: {avg_loss:.4f}')
    
    # Save model
    torch.save(model.state_dict(), 'vla_model.pth')
    print('Model saved!')
```

## Integrating LLMs for Reasoning

Use large language models for high-level reasoning:

```python
from openai import OpenAI
import json


class LLMReasoner:
    """Use LLM for task planning and reasoning."""
    
    def __init__(self):
        self.client = OpenAI()
    
    def plan_task(self, instruction, scene_description):
        """
        Break down instruction into subtasks.
        
        Args:
            instruction: High-level command
            scene_description: What the robot sees
        
        Returns:
            List of subtasks
        """
        prompt = f"""You are a robot task planner.

Instruction: {instruction}
Scene: {scene_description}

Break down the instruction into a sequence of atomic robot actions.
Each action should be one of:
- navigate_to(object)
- pick_up(object)
- place_on(location)
- open(object)
- close(object)

Respond with JSON:
{{"subtasks": ["action1", "action2", ...]}}
"""

        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        
        result = json.loads(response.choices[0].message.content)
        return result['subtasks']
    
    def handle_failure(self, subtask, error):
        """Reason about failure and suggest recovery."""
        prompt = f"""The robot failed to execute: {subtask}
Error: {error}

Suggest a recovery action or alternative approach.
"""

        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5
        )
        
        return response.choices[0].message.content
```

## Summary

- **VLA models** combine vision, language, and action for intelligent robots
- They enable **natural language control** of robots
- **Vision encoders** process camera images
- **Language encoders** understand instructions
- **Action decoders** generate robot commands
- State-of-the-art models: **RT-1**, **RT-2**, **OpenVLA**
- Training requires **demonstration data** and **multimodal learning**
- **LLMs** can provide high-level reasoning and planning

## Next Steps

In the next chapters, we'll:
- Integrate voice commands with speech recognition
- Build a complete autonomous humanoid robot system

## Resources

- [RT-1 Paper](https://robotics-transformer.github.io/)
- [RT-2 Paper](https://robotics-transformer2.github.io/)
- [OpenVLA](https://openvla.github.io/)
- [PaLM-E](https://palm-e.github.io/)
