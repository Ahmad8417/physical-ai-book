import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

const sidebars: SidebarsConfig = {
  tutorialSidebar: [
    'intro',
    {
      type: 'category',
      label: '🤖 Module 1 — ROS 2',
      items: ['module-1/overview', 'module-1/nodes-topics', 'module-1/python-agents'],
    },
    {
      type: 'category',
      label: '🌐 Module 2 — Gazebo & Unity',
      items: ['module-2/overview', 'module-2/simulation', 'module-2/sensors'],
    },
    {
      type: 'category',
      label: '🧠 Module 3 — NVIDIA Isaac',
      items: ['module-3/overview', 'module-3/isaac-sim', 'module-3/navigation'],
    },
    {
      type: 'category',
      label: '🗣️ Module 4 — VLA',
      items: ['module-4/overview', 'module-4/voice-commands', 'module-4/capstone'],
    },
  ],
};

export default sidebars;