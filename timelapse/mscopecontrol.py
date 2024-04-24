# led0 - excitation, default 0
# ewl - focus distance, default 0
# gain - gain, default "Low"
# frameRate - frame rate, default 30

import time

def set_led(m, val):
    '''Set the LED on the miniscope 'm' to the value 'val' (0 - 100).'''
    if 0 <= val <= 100:
        time.sleep(1)
        print('Setting excitation control to {}'.format(val))
        m.set_control_value('led0', val)
        time.sleep(1)
    else:
        print("Please input a value between 0 and 100.")

def set_focus(m, val):
    '''Set the focus/EWL on the miniscope 'm' to the value 'val' (-127 - +127).'''
    if -127 <= val <= 127:
        time.sleep(1)
        print('Setting focus control to {}'.format(val))
        m.set_control_value('ewl', val)
        time.sleep(1)
    else:
        print("Please input a value between -127 and 127.")

def set_gain(m, val):
    '''Set the gain on the miniscope 'm' to the value 'val' (0 - 2).
    0 --> 'Low', 1 --> 'Medium', 2 --> 'High'.'''
    if 0 <= val <= 2:
        time.sleep(1)
        print('Setting gain control to {}'.format(val))
        m.set_control_value('gain', val)
        time.sleep(1)
    else:
        print("Please input a value between 0 and 2.")
