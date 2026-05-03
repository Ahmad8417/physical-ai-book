import type {ReactNode} from 'react';
import clsx from 'clsx';
import Heading from '@theme/Heading';
import styles from './styles.module.css';

type FeatureItem = {
  title: string;
  Svg: React.ComponentType<React.ComponentProps<'svg'>>;
  description: ReactNode;
};

const FeatureList: FeatureItem[] = [
  {
    title: '🤖 ROS 2 Fundamentals',
    Svg: require('@site/static/img/undraw_docusaurus_mountain.svg').default,
    description: (
      <>
        Master the Robot Operating System 2 (ROS 2) - the industry standard for robotics.
        Learn nodes, topics, services, and how to build intelligent robot agents with Python.
      </>
    ),
  },
  {
    title: '🌐 Simulation & Digital Twins',
    Svg: require('@site/static/img/undraw_docusaurus_tree.svg').default,
    description: (
      <>
        Test your robots safely in Gazebo and NVIDIA Isaac Sim. Generate synthetic training
        data, simulate sensors, and perfect your algorithms before deploying to hardware.
      </>
    ),
  },
  {
    title: '🧠 AI-Powered Navigation',
    Svg: require('@site/static/img/undraw_docusaurus_react.svg').default,
    description: (
      <>
        Implement Visual SLAM, path planning, and obstacle avoidance. Use NVIDIA Isaac ROS
        for GPU-accelerated perception and Nav2 for autonomous navigation.
      </>
    ),
  },
  {
    title: '🗣️ Vision-Language-Action',
    Svg: require('@site/static/img/undraw_docusaurus_mountain.svg').default,
    description: (
      <>
        Control robots with natural language using VLA models. Integrate OpenAI Whisper
        for voice commands and build intelligent agents that understand and execute tasks.
      </>
    ),
  },
  {
    title: '🚀 Hands-On Projects',
    Svg: require('@site/static/img/undraw_docusaurus_tree.svg').default,
    description: (
      <>
        Build real systems from day one. Each module includes complete code examples,
        working demonstrations, and a capstone project: an autonomous humanoid robot.
      </>
    ),
  },
  {
    title: '🎓 Industry-Ready Skills',
    Svg: require('@site/static/img/undraw_docusaurus_react.svg').default,
    description: (
      <>
        Learn the exact tools and techniques used by leading robotics companies.
        From Boston Dynamics to Tesla, this is how modern robots are built.
      </>
    ),
  },
];

function Feature({title, Svg, description}: FeatureItem) {
  return (
    <div className={clsx('col col--4')}>
      <div className="text--center">
        <Svg className={styles.featureSvg} role="img" />
      </div>
      <div className="text--center padding-horiz--md">
        <Heading as="h3">{title}</Heading>
        <p>{description}</p>
      </div>
    </div>
  );
}

export default function HomepageFeatures(): ReactNode {
  return (
    <section className={styles.features}>
      <div className="container">
        <div className="row">
          {FeatureList.map((props, idx) => (
            <Feature key={idx} {...props} />
          ))}
        </div>
      </div>
    </section>
  );
}
