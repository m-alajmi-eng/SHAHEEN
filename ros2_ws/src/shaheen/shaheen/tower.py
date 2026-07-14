"""
SHAHEEN KKIA tower - clearance service (Day 4, request/response).

Provides a std_srvs/Trigger service that the mission supervisor calls before
starting a runway inspection. This maps SHAHEEN's existing tower radio exchange
("Requesting clearance for Runway Inspection..." / "Clearance GRANTED") onto a
real ROS 2 service: the supervisor asks, waits, and proceeds only if granted.

The response is controlled by a parameter so a denied-clearance abort can be
demonstrated without code changes.
"""

import rclpy
from rclpy.node import Node
from std_srvs.srv import Trigger


class Tower(Node):
    def __init__(self):
        super().__init__('tower')
        self.declare_parameter('grant_clearance', True)
        self.srv = self.create_service(
            Trigger, '/shaheen/request_clearance', self.on_request)
        self.get_logger().info('KKIA tower ready - clearance service up')

    def on_request(self, request, response):
        grant = bool(self.get_parameter('grant_clearance').value)
        response.success = grant
        response.message = (
            'Clearance GRANTED. Runway clear. Proceed.' if grant
            else 'ACCESS DENIED. Incoming traffic. Hold position.')
        self.get_logger().info(f'Clearance requested -> {response.message}')
        return response


def main(args=None):
    rclpy.init(args=args)
    node = Tower()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
