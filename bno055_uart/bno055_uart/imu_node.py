import math
import time
import serial
import adafruit_bno055
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu

class BNO055UARTNode(Node):
    def __init__(self):
        super().__init__('bno055_uart_node')
        self.declare_parameter('port', '/dev/ttyUSB0')
        self.declare_parameter('baudrate', 115200)

        port = self.get_parameter('port').get_parameter_value().string_value
        baud = self.get_parameter('baudrate').get_parameter_value().integer_value

        # open the FT232H UART
        self.uart = serial.Serial(port, baudrate=baud, timeout=1)
        # create the CircuitPython sensor over UART
        self.sensor = adafruit_bno055.BNO055_UART(self.uart)

        # wait for the BNO055 to boot
        time.sleep(1.0)

        # publisher for sensor_msgs/Imu
        self.pub = self.create_publisher(Imu, 'imu/data', 10)
        self.timer = self.create_timer(1/50.0, self.publish_imu)  # 50 Hz

    def publish_imu(self):
        msg = Imu()

        # orientation
        q = self.sensor.quaternion
        if q:
            msg.orientation.w, msg.orientation.x, msg.orientation.y, msg.orientation.z = q

        # angular velocity (°/s → rad/s)
        g = self.sensor.gyro
        if g:
            msg.angular_velocity.x = math.radians(g[0])
            msg.angular_velocity.y = math.radians(g[1])
            msg.angular_velocity.z = math.radians(g[2])

        # linear acceleration (g → m/s²)
        a = self.sensor.acceleration
        if a:
            msg.linear_acceleration.x = a[0] * 9.80665
            msg.linear_acceleration.y = a[1] * 9.80665
            msg.linear_acceleration.z = a[2] * 9.80665

        self.pub.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = BNO055UARTNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()