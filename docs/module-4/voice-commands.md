---
sidebar_position: 2
title: "Voice Commands and Speech Integration"
---

# Voice Commands: Natural Language Robot Control

## Introduction

Voice control is the most natural way for humans to interact with robots. Instead of programming or using controllers, users can simply speak commands like "go to the kitchen" or "pick up the red cup."

In this chapter, we'll build a complete voice-controlled robot system using:
- **Speech-to-Text**: Converting voice to text (Whisper, Google Speech)
- **Natural Language Understanding**: Parsing commands (LLMs)
- **ROS 2 Integration**: Executing robot actions
- **Text-to-Speech**: Robot feedback (optional)

## Speech-to-Text with OpenAI Whisper

**Whisper** is OpenAI's state-of-the-art speech recognition model.

### Installing Whisper

```bash
# Install Whisper
pip install openai-whisper

# Install audio dependencies
sudo apt install ffmpeg portaudio19-dev

# Install PyAudio for microphone input
pip install pyaudio
```

### Basic Whisper Usage

```python
import whisper
import numpy as np


class WhisperSTT:
    """Speech-to-Text using Whisper."""
    
    def __init__(self, model_size='base'):
        """
        Initialize Whisper model.
        
        Args:
            model_size: 'tiny', 'base', 'small', 'medium', 'large'
        """
        print(f"Loading Whisper {model_size} model...")
        self.model = whisper.load_model(model_size)
        print("Model loaded!")
    
    def transcribe_file(self, audio_file):
        """
        Transcribe audio file to text.
        
        Args:
            audio_file: Path to audio file (mp3, wav, etc.)
        
        Returns:
            Transcribed text
        """
        result = self.model.transcribe(audio_file)
        return result['text']
    
    def transcribe_array(self, audio_array, sample_rate=16000):
        """
        Transcribe numpy audio array.
        
        Args:
            audio_array: Audio samples as numpy array
            sample_rate: Sample rate in Hz
        
        Returns:
            Transcribed text
        """
        # Whisper expects float32 audio normalized to [-1, 1]
        if audio_array.dtype != np.float32:
            audio_array = audio_array.astype(np.float32) / 32768.0
        
        result = self.model.transcribe(audio_array)
        return result['text']


# Example usage
stt = WhisperSTT(model_size='base')
text = stt.transcribe_file('command.wav')
print(f"Transcribed: {text}")
```

## Real-Time Microphone Input

```python
import pyaudio
import numpy as np
import threading
import queue


class MicrophoneStream:
    """Real-time microphone audio stream."""
    
    def __init__(self, rate=16000, chunk_size=1024):
        self.rate = rate
        self.chunk_size = chunk_size
        self.audio_queue = queue.Queue()
        self.is_recording = False
        
        # Initialize PyAudio
        self.audio = pyaudio.PyAudio()
        
    def start(self):
        """Start recording from microphone."""
        self.is_recording = True
        
        self.stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.chunk_size,
            stream_callback=self._audio_callback
        )
        
        self.stream.start_stream()
        print("Microphone started")
    
    def stop(self):
        """Stop recording."""
        self.is_recording = False
        if hasattr(self, 'stream'):
            self.stream.stop_stream()
            self.stream.close()
        print("Microphone stopped")
    
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Callback for audio stream."""
        if self.is_recording:
            audio_data = np.frombuffer(in_data, dtype=np.int16)
            self.audio_queue.put(audio_data)
        return (in_data, pyaudio.paContinue)
    
    def read_chunk(self, timeout=1.0):
        """Read audio chunk from queue."""
        try:
            return self.audio_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def read_seconds(self, duration):
        """Read specified duration of audio."""
        num_chunks = int(duration * self.rate / self.chunk_size)
        chunks = []
        
        for _ in range(num_chunks):
            chunk = self.read_chunk()
            if chunk is not None:
                chunks.append(chunk)
        
        if chunks:
            return np.concatenate(chunks)
        return None
    
    def __del__(self):
        """Cleanup."""
        self.stop()
        self.audio.terminate()


# Example usage
mic = MicrophoneStream()
mic.start()

# Record 3 seconds
audio = mic.read_seconds(3)

mic.stop()

# Transcribe
stt = WhisperSTT()
text = stt.transcribe_array(audio)
print(f"You said: {text}")
```

## Voice-Activated Command System

```python
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import numpy as np
import threading


class VoiceCommandNode(Node):
    """ROS 2 node for voice command recognition."""
    
    def __init__(self):
        super().__init__('voice_command_node')
        
        # Publisher for recognized commands
        self.command_pub = self.create_publisher(
            String,
            '/voice_command',
            10
        )
        
        # Initialize STT
        self.stt = WhisperSTT(model_size='base')
        
        # Initialize microphone
        self.mic = MicrophoneStream()
        
        # Voice activity detection threshold
        self.vad_threshold = 500  # Adjust based on environment
        
        # Recording state
        self.is_listening = False
        
        self.get_logger().info('Voice command node started')
        
        # Start listening thread
        self.listen_thread = threading.Thread(target=self.listen_loop)
        self.listen_thread.daemon = True
        self.listen_thread.start()
    
    def detect_voice_activity(self, audio_chunk):
        """Simple voice activity detection."""
        # Calculate RMS energy
        rms = np.sqrt(np.mean(audio_chunk.astype(float)**2))
        return rms > self.vad_threshold
    
    def listen_loop(self):
        """Main listening loop."""
        self.mic.start()
        
        recording_buffer = []
        silence_counter = 0
        max_silence = 20  # ~2 seconds of silence
        
        while rclpy.ok():
            # Read audio chunk
            chunk = self.mic.read_chunk(timeout=0.1)
            
            if chunk is None:
                continue
            
            # Check for voice activity
            if self.detect_voice_activity(chunk):
                recording_buffer.append(chunk)
                silence_counter = 0
                
                if not self.is_listening:
                    self.is_listening = True
                    self.get_logger().info('Listening...')
            
            elif self.is_listening:
                recording_buffer.append(chunk)
                silence_counter += 1
                
                # End of speech detected
                if silence_counter >= max_silence:
                    self.process_recording(recording_buffer)
                    recording_buffer = []
                    silence_counter = 0
                    self.is_listening = False
    
    def process_recording(self, audio_chunks):
        """Process recorded audio."""
        if not audio_chunks:
            return
        
        # Concatenate chunks
        audio = np.concatenate(audio_chunks)
        
        # Transcribe
        self.get_logger().info('Transcribing...')
        text = self.stt.transcribe_array(audio)
        
        if text.strip():
            self.get_logger().info(f'Command: "{text}"')
            
            # Publish command
            msg = String()
            msg.data = text
            self.command_pub.publish(msg)
        else:
            self.get_logger().warn('No speech detected')
    
    def __del__(self):
        """Cleanup."""
        if hasattr(self, 'mic'):
            self.mic.stop()


def main(args=None):
    rclpy.init(args=args)
    node = VoiceCommandNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
```

## Natural Language Understanding

Parse voice commands into robot actions:

```python
from openai import OpenAI
import json
import re


class CommandParser:
    """Parse natural language commands into robot actions."""
    
    def __init__(self):
        self.client = OpenAI()
        
        # Define available actions
        self.actions = {
            'navigate': ['go', 'move', 'walk', 'travel'],
            'pick': ['pick', 'grab', 'take', 'get'],
            'place': ['place', 'put', 'drop', 'set'],
            'open': ['open'],
            'close': ['close', 'shut'],
            'stop': ['stop', 'halt', 'freeze']
        }
    
    def parse_simple(self, command):
        """
        Simple rule-based parsing.
        
        Returns:
            dict: {'action': str, 'target': str, 'location': str}
        """
        command_lower = command.lower()
        
        result = {
            'action': None,
            'target': None,
            'location': None
        }
        
        # Detect action
        for action, keywords in self.actions.items():
            for keyword in keywords:
                if keyword in command_lower:
                    result['action'] = action
                    break
            if result['action']:
                break
        
        # Extract target object (simple heuristic)
        # Look for "the X" pattern
        match = re.search(r'the\s+(\w+(?:\s+\w+)?)', command_lower)
        if match:
            result['target'] = match.group(1)
        
        # Extract location
        # Look for "to/in/on X" pattern
        match = re.search(r'(?:to|in|on)\s+(?:the\s+)?(\w+(?:\s+\w+)?)', command_lower)
        if match:
            result['location'] = match.group(1)
        
        return result
    
    def parse_llm(self, command):
        """
        LLM-based parsing for complex commands.
        
        Returns:
            dict: Structured command representation
        """
        prompt = f"""Parse this robot command into structured format:

Command: "{command}"

Extract:
- action: navigate, pick, place, open, close, stop
- target: object to interact with (if any)
- location: destination or placement location (if any)
- modifiers: color, size, position descriptors

Respond with JSON only:
{{"action": "...", "target": "...", "location": "...", "modifiers": {{}}}}

Examples:
"go to the kitchen" → {{"action": "navigate", "location": "kitchen"}}
"pick up the red cup" → {{"action": "pick", "target": "cup", "modifiers": {{"color": "red"}}}}
"place it on the table" → {{"action": "place", "location": "table"}}
"""

        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        
        result = json.loads(response.choices[0].message.content)
        return result
    
    def parse(self, command, use_llm=True):
        """
        Parse command using best available method.
        
        Args:
            command: Natural language command
            use_llm: Whether to use LLM (slower but more accurate)
        
        Returns:
            Parsed command dict
        """
        if use_llm:
            try:
                return self.parse_llm(command)
            except Exception as e:
                print(f"LLM parsing failed: {e}, falling back to simple")
                return self.parse_simple(command)
        else:
            return self.parse_simple(command)


# Example usage
parser = CommandParser()

commands = [
    "go to the kitchen",
    "pick up the red cup",
    "place it on the table",
    "open the door"
]

for cmd in commands:
    parsed = parser.parse(cmd)
    print(f"{cmd} → {parsed}")
```

## Complete Voice-Controlled Robot

```python
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from geometry_msgs.msg import Twist, PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator
import math


class VoiceControlledRobot(Node):
    """Complete voice-controlled robot system."""
    
    def __init__(self):
        super().__init__('voice_controlled_robot')
        
        # Command parser
        self.parser = CommandParser()
        
        # Navigator for navigation commands
        self.navigator = BasicNavigator()
        
        # Subscribe to voice commands
        self.command_sub = self.create_subscription(
            String,
            '/voice_command',
            self.command_callback,
            10
        )
        
        # Publisher for velocity commands
        self.vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        
        # Known locations (predefined map)
        self.locations = {
            'kitchen': (5.0, 3.0, 0.0),
            'living room': (2.0, 2.0, 0.0),
            'bedroom': (8.0, 5.0, 1.57),
            'door': (1.0, 0.0, 0.0)
        }
        
        self.get_logger().info('Voice-controlled robot ready!')
    
    def command_callback(self, msg):
        """Process voice command."""
        command_text = msg.data
        self.get_logger().info(f'Processing: "{command_text}"')
        
        # Parse command
        parsed = self.parser.parse(command_text)
        
        # Execute action
        if parsed['action'] == 'navigate':
            self.execute_navigate(parsed)
        
        elif parsed['action'] == 'pick':
            self.execute_pick(parsed)
        
        elif parsed['action'] == 'place':
            self.execute_place(parsed)
        
        elif parsed['action'] == 'stop':
            self.execute_stop()
        
        else:
            self.get_logger().warn(f"Unknown action: {parsed['action']}")
    
    def execute_navigate(self, parsed):
        """Execute navigation command."""
        location_name = parsed.get('location')
        
        if not location_name:
            self.get_logger().error('No location specified')
            return
        
        # Look up location
        if location_name in self.locations:
            x, y, theta = self.locations[location_name]
            
            self.get_logger().info(f'Navigating to {location_name}')
            
            # Create goal pose
            goal = PoseStamped()
            goal.header.frame_id = 'map'
            goal.header.stamp = self.navigator.get_clock().now().to_msg()
            goal.pose.position.x = x
            goal.pose.position.y = y
            goal.pose.orientation.z = math.sin(theta / 2.0)
            goal.pose.orientation.w = math.cos(theta / 2.0)
            
            # Send goal
            self.navigator.goToPose(goal)
            
        else:
            self.get_logger().error(f'Unknown location: {location_name}')
    
    def execute_pick(self, parsed):
        """Execute pick command."""
        target = parsed.get('target')
        modifiers = parsed.get('modifiers', {})
        
        self.get_logger().info(f'Picking up {target} {modifiers}')
        
        # In a real system, this would:
        # 1. Detect object using vision
        # 2. Plan grasp
        # 3. Execute pick motion
        
        # Placeholder
        self.get_logger().info('Pick action not yet implemented')
    
    def execute_place(self, parsed):
        """Execute place command."""
        location = parsed.get('location')
        
        self.get_logger().info(f'Placing object on {location}')
        
        # Placeholder
        self.get_logger().info('Place action not yet implemented')
    
    def execute_stop(self):
        """Stop all motion."""
        self.get_logger().info('Stopping')
        
        # Stop navigation
        self.navigator.cancelTask()
        
        # Stop motors
        stop_cmd = Twist()
        self.vel_pub.publish(stop_cmd)


def main(args=None):
    rclpy.init(args=args)
    robot = VoiceControlledRobot()
    rclpy.spin(robot)
    robot.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
```

## Text-to-Speech Feedback

Give the robot a voice:

```python
from gtts import gTTS
import pygame
import io


class TextToSpeech:
    """Text-to-Speech for robot feedback."""
    
    def __init__(self):
        pygame.mixer.init()
    
    def speak(self, text, lang='en'):
        """
        Speak text using Google TTS.
        
        Args:
            text: Text to speak
            lang: Language code ('en', 'es', 'fr', etc.)
        """
        # Generate speech
        tts = gTTS(text=text, lang=lang, slow=False)
        
        # Save to memory buffer
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        
        # Play audio
        pygame.mixer.music.load(fp)
        pygame.mixer.music.play()
        
        # Wait for completion
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)


# Example usage
tts = TextToSpeech()
tts.speak("Hello, I am your robot assistant")
tts.speak("Navigating to the kitchen")
tts.speak("Task complete")
```

## Multi-Language Support

```python
class MultilingualVoiceControl:
    """Support multiple languages."""
    
    def __init__(self):
        self.supported_languages = {
            'en': 'English',
            'es': 'Spanish',
            'fr': 'French',
            'de': 'German',
            'zh': 'Chinese',
            'ja': 'Japanese',
            'ar': 'Arabic',
            'ur': 'Urdu'
        }
        
        self.current_language = 'en'
    
    def set_language(self, lang_code):
        """Set active language."""
        if lang_code in self.supported_languages:
            self.current_language = lang_code
            print(f"Language set to {self.supported_languages[lang_code]}")
        else:
            print(f"Language {lang_code} not supported")
    
    def transcribe(self, audio, whisper_model):
        """Transcribe with language detection."""
        result = whisper_model.transcribe(
            audio,
            language=self.current_language
        )
        
        detected_lang = result.get('language', 'unknown')
        print(f"Detected language: {detected_lang}")
        
        return result['text']
```

## Wake Word Detection

Activate robot with a wake word like "Hey Robot":

```python
import pvporcupine
import struct


class WakeWordDetector:
    """Detect wake word to activate robot."""
    
    def __init__(self, access_key, keyword='jarvis'):
        """
        Initialize Porcupine wake word detector.
        
        Args:
            access_key: Picovoice access key
            keyword: Wake word ('jarvis', 'alexa', 'computer', etc.)
        """
        self.porcupine = pvporcupine.create(
            access_key=access_key,
            keywords=[keyword]
        )
        
        self.keyword = keyword
    
    def detect(self, audio_chunk):
        """
        Check if wake word is in audio chunk.
        
        Args:
            audio_chunk: Audio samples (int16)
        
        Returns:
            True if wake word detected
        """
        # Porcupine expects specific frame length
        if len(audio_chunk) != self.porcupine.frame_length:
            return False
        
        keyword_index = self.porcupine.process(audio_chunk)
        return keyword_index >= 0
    
    def __del__(self):
        """Cleanup."""
        if hasattr(self, 'porcupine'):
            self.porcupine.delete()


# Usage in voice command node
class WakeWordVoiceNode(Node):
    """Voice node with wake word activation."""
    
    def __init__(self):
        super().__init__('wake_word_voice_node')
        
        # Wake word detector
        self.wake_word = WakeWordDetector(
            access_key='YOUR_ACCESS_KEY',
            keyword='jarvis'
        )
        
        self.is_active = False
        
        # Rest of initialization...
    
    def listen_loop(self):
        """Listen for wake word, then commands."""
        self.mic.start()
        
        while rclpy.ok():
            chunk = self.mic.read_chunk()
            
            if chunk is None:
                continue
            
            # Check for wake word
            if not self.is_active:
                if self.wake_word.detect(chunk):
                    self.is_active = True
                    self.get_logger().info('Wake word detected! Listening...')
                    self.tts.speak("Yes?")
            
            else:
                # Process command
                # ... (same as before)
                pass
```

## Best Practices

### 1. Noise Robustness

```python
# Use noise reduction
import noisereduce as nr

def reduce_noise(audio, sample_rate):
    """Remove background noise."""
    return nr.reduce_noise(y=audio, sr=sample_rate)
```

### 2. Confirmation Feedback

```python
def confirm_command(self, parsed_command):
    """Ask user to confirm command."""
    action = parsed_command['action']
    target = parsed_command.get('target', '')
    location = parsed_command.get('location', '')
    
    confirmation = f"Do you want me to {action}"
    if target:
        confirmation += f" the {target}"
    if location:
        confirmation += f" to the {location}"
    confirmation += "?"
    
    self.tts.speak(confirmation)
    
    # Wait for "yes" or "no"
    # ...
```

### 3. Error Handling

```python
def handle_recognition_error(self):
    """Handle speech recognition failures."""
    responses = [
        "Sorry, I didn't catch that",
        "Could you repeat that?",
        "I didn't understand"
    ]
    
    self.tts.speak(random.choice(responses))
```

## Summary

- **Whisper** provides state-of-the-art speech recognition
- **Voice Activity Detection** triggers recording
- **Natural Language Understanding** parses commands
- **ROS 2 integration** executes robot actions
- **Text-to-Speech** provides feedback
- **Wake words** activate the robot
- **Multi-language support** enables global deployment

## Next Steps

In the final chapter, we'll build a complete autonomous humanoid robot capstone project.

## Resources

- [OpenAI Whisper](https://github.com/openai/whisper)
- [Picovoice Porcupine](https://picovoice.ai/platform/porcupine/)
- [gTTS Documentation](https://gtts.readthedocs.io/)
- [PyAudio Documentation](https://people.csail.mit.edu/hubert/pyaudio/)
