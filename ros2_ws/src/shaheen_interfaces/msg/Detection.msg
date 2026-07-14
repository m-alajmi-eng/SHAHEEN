# A single detected runway hazard produced by the YOLOv8n perception node.
std_msgs/Header header        # stamp + camera frame_id
string label                  # detected class name (e.g. "FOD", "cone", "bird")
float32 confidence            # detection confidence, 0.0 - 1.0
geometry_msgs/Point position  # bounding-box centre in image pixels (x, y); z unused
float32 area                  # bounding-box area in pixels
