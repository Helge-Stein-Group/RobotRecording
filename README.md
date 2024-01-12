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

1. To setup simply call setup.bat, The setup script will install all required dependencies and create a virtual
   environment. Moreover, it creates RobotRecording batch script on your desktop
2. Double click the RobotRecording batch script to start the application

## Controller Keymap

Refer to the following image for the controller keymap:
![keymap.png](doc%2Fkeymap.png)



