#!/usr/bin/env python

import rospy
from std_msgs.msg import String
import os

def callback(data):
    rospy.loginfo(f"Received message: {data.data}")
    if data.data == "1":
        try:
            rospy.loginfo("Attempting to delete model...")
            result = os.system('rosservice call /gazebo/delete_model "{model_name: \'wall_115.3_42.8_1.5\'}"')
            if result == 0:
                rospy.loginfo("Deleted model: wall_115.3_42.8_1.5")
            else:
                rospy.logerr(f"Failed to delete model with result code: {result}")
        except Exception as e:
            rospy.logerr(f"Failed to delete model: {e}")

def listener():
    rospy.init_node('auto_door_listener', anonymous=True)
    rospy.Subscriber('auto_door', String, callback)
    rospy.loginfo("Listening to 'auto_door' topic...")
    rospy.spin()

if __name__ == '__main__':
    try:
        listener()
    except rospy.ROSInterruptException:
        pass
