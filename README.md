# ElDriveMain

## Introduction

**Eldrive** is an innovative and socially driven team of six members working on an impactful project titled **"Autonomous Shuttle for the Elderly in Rural Bavaria."** Our mission is to support elderly individuals living in the Bavarian countryside who face difficulties in maintaining their mobility and social connections.

We aim to develop an **autonomous, on-demand, door-to-door shuttle service** that empowers elderly people to visit friends and family and stay engaged with their community all while preserving their independence and dignity. By combining advanced sensing, planning, and control technologies, Eldrive envisions a future where rural mobility challenges are addressed with cutting-edge autonomous solutions.

## Object Detection

- [Object detection evaluation](./objectdetection.md)

---

## Table of Contents


- [ElDriveMain](#eldrivemain)
  - [Introduction](#introduction)
  - [Object Detection](#object-detection)
  - [Table of Contents](#table-of-contents)
  - [Question Zero](#question-zero)
  - [Persona](#persona)
- [Project Management](#project-management)
  - [Team Features and Responsibilities](#team-features-and-responsibilities)
  - [User Story Map](#user-story-map)
  - [Effort Estimation \& Prioritization](#effort-estimation--prioritization)
  - [Milestones](#milestones)
  - [Use Case](#use-case)
  - [Scenario](#scenario)
- [Architecture](#architecture)
  - [Block Diagram (Sense-Plan-Act Architecture)](#block-diagram-sense-plan-act-architecture)
  - [State Diagram](#state-diagram)
  - [Activity Diagram](#activity-diagram)
  - [User Interface Concepts](#user-interface-concepts)
  - [Component Responsibilities](#component-responsibilities)
  - [License](#license)

---

## Question Zero

How can we assist the senior citizens who face difficulties visiting their friends and family by providing an autonomous on demand vehicle service that goes door to door in Bavarian countryside?

---

## Persona

**Emma Heller**, a 68-year-old retired teacher living alone in Kronach, enjoys visiting her friends and family.

<p align="center">
  <img src="eldrive/resource/images/Persona.jpg" alt="User Story Map" width="900"/>
</p>


---

# Project Management

## Team Features and Responsibilities
| Team Member              |   Feature              | Feature description|
|--------------------------|------------------------|--------------------|
|Lingaprasath Nagarajan    | User Authorization for Shuttle Access  |Users can easily access the vehicle using their login ID, and after boarding, they can monitor the ride progress. |
|Karthik Chowdary Nunna    | Booking a ride from an external Human-Machine interface|Users are provided with a user-friendly external Human-Machine Interface (HMI) that allows them to log in using a unique Login ID or QR code, select pre-saved destinations associated with family members or friends, and securely complete payment to book a ride. |
|Khadija Mahboob Alam      | Controlled Autonomous Mobility   |The shuttle autonomously transports users by adjusting its speed to road geometry,  slowing on sharp turns, maintaining steady motion on straight segments and comply with infrastructure traffic rules. |
|Stanislav Fomin    | Robust operations in different areas    | Users can rely on the shuttle to operate robust in environments with limited sensor availability, such as tunnel.|
|Rinkal Viradiya           | Obstacle Handling  | The shuttle detects obstacles along its planned path and reacts by safely stopping, with support for obstacle avoidance.|

## User Story Map 

An overview of key user journeys (users stories and acceptance criteria for Module 6) to guide the development of our autonomous shuttle service.

<p align="center">
  <img src="eldrive/resource/images/m6_user_story_map.png" alt="User Story Map" width="900"/>
</p>

To access complete User Story Map please use the given link: https://miro.com/app/board/uXjVGG8jPt4=/?moveToWidget=3458764658103298781&cot=14

---

## Effort Estimation & Prioritization (Module 5)

Impact vs Effort Estimation plot. Each quadrant describes the order of priority


<p align="center">
  <img src="eldrive/resource/images/effort_vs_impact_matrix_M5.jpeg" alt="" width="900"/>
</p>

To access excel sheet for effort estimation and prioritization please use the given link: https://hscoburgde-my.sharepoint.com/:x:/g/personal/lin4181s_hs-coburg_de/EW6HwFBG5mtDt3IzpJYsP18BwVi8ooWI2riMp9zd-m4URw?e=H1aAQs

---

## Milestones

An outline of Milestone 5 which highlights our key development phases, visualized through structured planning.

<p align="center">
  <img src="eldrive/resource/images/eldrive_milestones.png" alt="Milestones" width="900"/>
</p>

To access complete User Milestone please use the given link: https://miro.com/app/board/uXjVGG8jPt4=/?moveToWidget=3458764658438685028&cot=14

## Use Case 
Emma, a 68-year-old living in rural Kronach, uses the Eldrive application to book a shuttle ride to her daughter’s home in Lichtenfels. She selects a pre-registered ride option, reviews the details, and confirms the booking with her saved credit card, and sees a “Ride Confirmed” message.

## Scenario

Emma Heller, a 68-year-old woman living in a rural area of Kronach, wants to visit her daughter in Würzburg. She taps her phone’s QR-code to open the external Human-machine interface and selects “Kronach–Würzburg” from four pre-registered destinations. After completing the payment, she receives a confirmation message, “Ride confirmed,” and can track the shuttle’s live location.

The autonomous shuttle receives the booking request, departs from its dedicated parking space, follows the pre-planned route, passes through a tunnel, and obeys all traffic rules.

When the shuttle reaches the pick-up location, Emma authorizes boarding using a QR code and enters the vehicle. The onboard Human Machine Interface (HMI) welcomes her and displays route information, real-time location, and the estimated time of arrival (ETA). While passing Neuses, the shuttle detects an obstacle before entering Küps and comes to a complete stop. After the obstacle is cleared, the shuttle resumes its journey, passes Ebensfeld, and reaches the drop-off location in Würzburg. It parks safely, allows Emma to exit, and then returns to its parking area using the most efficient route.


<p align="center">
  <img src="eldrive/resource/images/m6_scenario.png" alt="Scenario Placeholder" width="600"/>
</p>

# Architecture

The architecture consists of the following diagrams:

- **Block Diagram**
- **State Diagram**
- **Activity Diagram**

Additionally, the responsibilities of the individual components are also listed here.

## Block Diagram (Sense-Plan-Act Architecture)

System architecture is illustrated in the mentioned block diagram, consisting of distinct functional layers like sense, plan and act. The sensors perceive the surroundings to assist the sense layer to process and interpret the environment, actuators execute the commands given via act layer. 

The **Sensor layer** foremost helps perceive the environment using several components like Lidar, Realsense camera and door actuator. Camera and Lidar are the sole agents to perceive the environment. A door sensor has been implemented to sense the status of the shuttle’s doors and boarding aid, if they are open or closed to identify the transition between shuttle’s states. We begin with the sense layer, that serves as the bridge between sensors and plan layer.
The Sense layer consists of Localization that identifies the shuttle’s position in real time. Object detection is employed to identify objects in its perception field. V2X receiver’s purpose is to interpret V2X messages like /cam, /spatem, /cpm, being transmitted via the V2X infrastructure, sort this information to respective following components that have further requirements of these messages. Map server consists of static map data, that helps server to interpret boarding points received from user end. Additionally, User authorization component, Card reader and Door sensor driver are new implementations amongst this layer. The Door sensor driver acts as a bridge between the Door sensor and plan layer to provide processed data into Boolean messages. Card reader translates User NFC card details to feed User authorization component with the user booking ID details. The User authorization component processes this info to grant or deny permission to open doors for users to board the shuttle. Based on all the sensed and processed information we move onto the plan layer, where the shuttle’s mobility is enabled.

The **Plan layer** comprehends the environment to identify vehicle state, decides to enable path planning and converts them into refined messages to assist act layer further. The decision maker expects input from door sensor driver to identify shuttle’s state. Object Detection module is supposed to inform Decision Maker of any objects detected on the path, so Decision Maker can be able to identify if it’s an obstacle or not. Decision Maker is the only component that expects input from Trajectory Controller from act layer to identify the shuttle’s state transition and enable or disable Path Planner. Further, access control in act layer is also given Boolean message from Decision Maker to enable or disable the doors and boarding aid. Path Planner expects permission from Decision Maker to plan path by deriving inputs from Localization, to be aware of ego vehicle position. Server provides the destination details; map server provides the local static map and road network information to Path Planner. Based on all these inputs, Path Planner plans a path from shuttle’s current position to the consecutive destinations being provided by the Server and forwards the message to Trajectory Controller on the act layer.

The **Act layer** comprises a Trajectory Controller, V2X Transmitter, and Access Controller. The Trajectory Controller takes the odometry data from Localization to know the current state of the vehicle (position, orientation, velocity) and another input as the planned path from the Path Planner and passes necessary messages to Ackermann Driver to control vehicle speed, steering angle and braking commands to be executed by the actuator layer. Further on, the Trajectory Controller informs the Decision Maker about the trajectory execution status, if it is completed. The V2X transmitter is expected to transmit a /CAM message that briefs the ego vehicle location in geodetic format, vehicle ID, vehicle length and width to inform the local V2X infrastructure. Access control simply passes Boolean messages to Door actuator, to enable or disable doors and boarding aid. 

Furthermore,the **User Interface (UI)** is a web-based frontend for the **ElDrive Shuttle System** a smart, accessible ride-booking platform designed especially for elderly users. The internal HMI which is also connected to ROS server. 

The UI connects to the ROS 2 backend via **Rosbridge WebSocket**, enabling real-time interaction between users, the server, and system components like the planner and decision maker.The **Server Node** is the central middleware connecting the **User Interface (UI), Path Planner, Decision Maker**, and **User Authorization** components.
It acts as a **bridge** interpreting messages from the web UI, processing user requests, and publishing commands and updates to the rest of the ROS 2 ecosystem.

The **Actuators layer** expect messages from the act layer to execute commands like steering, acceleration, and braking. Door actuator actuates the opening and closing operations of the door and boarding aid.

To access the Block diagram use the given link: https://miro.com/app/board/uXjVI4FV3gw=/?moveToWidget=3458764658113644529&cot=14

<p align="center">
  <img src="eldrive/resource/images/architecture_v6.jpg" alt="Block Diagram">
</p>

## State Diagram

The state diagram represents the various stages the shuttle transitions through during its operation. The journey begins in the **idle state**, where the shuttle remains stationary with its doors closed, awaiting incoming user requests. Once a request is received, the system begins planning an optimal route to the destination. After route planning is completed, the shuttle transitions into the **driving state**, navigating along the planned route.

Upon reaching the destination, the shuttle transitions to the **parking state**, where it searches for an appropriate parking spot and follows a planned trajectory to park safely. Once parked, the system proceeds to the **boarding/deboarding state**. Here, the shuttle opens its doors and activates boarding aids, allowing users to board or exit. It also verifies user authorization and ensures the boarding or deboarding process is complete.

After this process, the shuttle either returns to the **driving state** to continue its journey to the next stop or, if the final user has deboarded, transitions back to the **parking state**. From there, once securely parked, it enters the **idle state** again.

To follow the traffic rules, the shuttle during **driving state** stops at the signal when traffic ligt turns red (False) and resumes moving forward when traffic light turns back green (True).

<p align="center">
  <img src="eldrive/resource/images/state_diagram_M5.jpeg" alt="State Diagram" width="600" height="450">
</p>

## Activity Diagram

The elderly user makes a booking for the shuttle through the designated interface whenever in need; this action initiates a request including all required user details.

The system registers user information and determines a feasible route to the pick-up point, considering road conditions, traffic, and accessibility for the elderly user. The system generates confirmation of the ride, notifying the user that the ride is accepted and the shuttle is en route.

Before the system generates the confirmation, it enables the user to modify the pre-existing pick-up and drop-off locations to accommodate last-minute changes in destination or timing. Another request is raised and processed accordingly.

On confirmation by the user, the shuttle navigates to the pick-up location. During navigation, the system checks for interruptions such as obstacles and unexpected delays. If detected, the shuttle maneuvers to safely bypass them. The shuttle reaches the location and parks while waiting for the user.

Once parked at the pick-up or destination, user authorization is completed, and the shuttle automatically opens doors and enables boarding aids such as ramps or lifting platforms for the user. The shuttle ensures the user boards or deboards safely before withdrawing the boarding aid and closing doors, avoiding any mishap.

Upon completion of the ride, the shuttle waits for further requests. If a new request is raised, the shuttle sends confirmation and repeats the procedure as described.

<p align="center">
  <img src="eldrive/resource/images/Activity%20Diagram.jpg" alt="Activity Diagram">
</p>

## User Interface Concepts
To access External and Internal User Interfaces use the below links:

- [Extrenal UI](https://git.hs-coburg.de/eldrive/User_Interface_Concepts/src/branch/main/External_hmi.md) 
- [Internal UI](https://git.hs-coburg.de/eldrive/User_Interface_Concepts/src/branch/main/Internal_hmi.md)


## Component Responsibilities

| Components              | Authors (Responsible for Module 4)                   |
|-------------------------------|--------------------------|
| [Localization](https://git.hs-coburg.de/eldrive/Localization)                  | Stanislav Fomin          |
| [Trajectory Controller](https://git.hs-coburg.de/eldrive/TrajectoryController) | Khadija Mahboob Alam     |
| [Decision Maker](https://git.hs-coburg.de/eldrive/Decision_Maker)              | Rinkal Viradiya          |
| [Path Planner](https://git.hs-coburg.de/eldrive/Path_planner)                  | Lingaprasath Nagarajan   |
| [Internal HMI](https://git.hs-coburg.de/eldrive/Internal_User_Interface)                              | Karthik Chowdary Nunna   |




| Supporting Components                | Author                   |
|-------------------------------|--------------------------|
| [V2X Transmitter](https://git.hs-coburg.de/eldrive/V2X_Transmitter)            | Stanislav Fomin             |
| [Access controller](https://git.hs-coburg.de/eldrive/Access_controller) | Khadija Mahboob Alam     |
| [Signal Identifier](https://git.hs-coburg.de/eldrive/Signal_identifier)                  | Lingaprasath Nagarajan   |
| [V2X Receiver](https://git.hs-coburg.de/eldrive/V2X_receiver)                  | Lingaprasath Nagarajan   |
| [Server](https://git.hs-coburg.de/eldrive/Server)                              | Karthik Chowdary Nunna   |
| [User Authorization](https://git.hs-coburg.de/eldrive/User-authorization)                              | Karthik Chowdary Nunna   |
| [User Interface](https://git.hs-coburg.de/eldrive/User_Interface)                              | Karthik Chowdary Nunna   |
| [Obstacle Detection](https://git.hs-coburg.de/eldrive/Obstacle_detection)                              | Rinkal Viradiya   |
| [Obstacle Lane filter](https://git.hs-coburg.de/eldrive/obstacle_lane_filter)                              | Rinkal Viradiya   |
| [Sensor Fusion](https://git.hs-coburg.de/eldrive/sensor_fusion)                              | Rinkal Viradiya   |

## License

Licensed under the **Apache 2.0 License**. See [LICENSE](LICENSE) for details.
