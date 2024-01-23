# Dobot Robot Control with PlayStation 5 Controller

This repository facilitates controlling a Dobot Robot using a PlayStation 5 controller and recording sequences for later
playback.

## Getting Started

### Connecting the Controller

To connect the controller to your computer, you have two options:

- **USB Connection:**
    - Simply connect the controller via USB.

- **Bluetooth Connection:**
    - Pair the controller with the computer by following these steps:
        1. Press the **PS button** and the **Share button** simultaneously,
           located at the top right of the touchpad. This action will make the
           light on the controller flash blue.
        2. On your computer, search for Bluetooth devices and connect to the
           controller. Once connected, the light on the controller should stay
           solid blue. (This unfortunately does not allow to indicate the joints
           via the touchpad LEDs)

### Setup

The setup requires an exisiting python installation with pip and firefox.

1. Clone the repository
2. Run setup.bat, which
    3. Creates a virtual environment.
    4. Installs required dependencies
    5. Creates RobotRecording batch script on your desktop
2. Double-click the RobotRecording batch script to start the application

## Controller Keymap

Refer to the following image for the controller keymap:
![keymap.png](doc%2Fkeymap.png)

## Joint Mapping for Dobot M1 Pro

Specific Joint coding for M1 Pro in terms of joint number and color
![joints.png](doc%2Fjoints.png)

## User-Interface

The tool provides a web interface
![user_interface.png](doc%2Fuser_interface.png)

## Memory files

The recorded trajectories can be saved and loaded from json files, with the following format.

```
[
    {
        "Type": "POINT",
        "Value": [
            279.239335,
            32.770248,
            98.500513,
            -121.842974
        ],
        "Motion Type": "JOINT",
        "Valid": true
    },
    {
        "Type": "MOVEMENT",
        "Value": [
            -4.9609375,
            0.0,
            0.0,
            0.0
        ],
        "Motion Type": "JOINT",
        "Valid": true
    },
    {
        "Type": "MOVEMENT",
        "Value": [
            0.0,
            5.0,
            0.0,
            0.0
        ],
        "Motion Type": "LINEAR",
        "Valid": true
    },
]
```