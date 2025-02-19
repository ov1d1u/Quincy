import struct
import sys
import numpy as np

# Given function
LEFT_CLOSE_ARM = 11
LEFT_FAR_ARM = 11
RIGHT_CLOSE_ARM = 11
RIGHT_FAR_ARM = 11
MOTOR_SPACE = 2.5

def compute_intersection(center1_x, center1_y, radius1, center2_x, center2_y, radius2):
    dx = center2_x - center1_x
    dy = center2_y - center1_y
    d = np.sqrt(dx**2 + dy**2)
    
    if d > (radius1 + radius2) or d < abs(radius1 - radius2):
        raise ValueError("No intersection between circles")
    
    a = (radius1**2 - radius2**2 + d**2) / (2 * d)
    h = np.sqrt(radius1**2 - a**2)
    
    midpoint_x = center1_x + (dx * a) / d
    midpoint_y = center1_y + (dy * a) / d
    
    perp_x = -dy * (h / d)
    perp_y = dx * (h / d)
    
    intersection1 = (midpoint_x + perp_x, midpoint_y + perp_y)
    intersection2 = (midpoint_x - perp_x, midpoint_y - perp_y)
    
    return [intersection1, intersection2]

def angles_to_coord(left_arm_angle, right_arm_angle):
    left_arm_angle_rad = np.radians(left_arm_angle)
    right_arm_angle_rad = np.radians(180 - right_arm_angle)

    # Left pivot calculation
    left_pivot_x = -MOTOR_SPACE/2 - np.cos(left_arm_angle_rad) * LEFT_CLOSE_ARM
    left_pivot_y = np.sin(left_arm_angle_rad) * LEFT_CLOSE_ARM

    # Right pivot calculation
    right_pivot_x = MOTOR_SPACE/2 + np.cos(right_arm_angle_rad) * RIGHT_CLOSE_ARM
    right_pivot_y = np.sin(right_arm_angle_rad) * RIGHT_CLOSE_ARM

    # Find target as intersection of two circles
    try:
        intersections = compute_intersection(
            left_pivot_x, left_pivot_y, LEFT_FAR_ARM,
            right_pivot_x, right_pivot_y, RIGHT_FAR_ARM
        )
    except ValueError as e:
        raise ValueError("No valid target position") from e

    # Select the intersection with positive y (below the pivots)
    valid = [(x, y) for x, y in intersections if y >= 0]
    if not valid:
        raise ValueError("No valid target below the pivots")
    target_x, target_y = valid[0]

    return (target_x, target_y)

def pmd_to_svg(pmd_data):
    index = 0
    paths = []

    # Read header
    magic_number = pmd_data[index]
    index += 1
    if magic_number != 1:
        raise ValueError("Invalid PMD file format.")

    num_segments = struct.unpack_from('<I', pmd_data, index)[0]
    index += 4

    # Read each segment
    for _ in range(num_segments):
        num_points = struct.unpack_from('<I', pmd_data, index)[0]
        index += 4

        path_data = []

        # Read each point in the segment
        for _ in range(num_points):
            left_angle = struct.unpack_from('<f', pmd_data, index)[0]
            index += 4
            right_angle = struct.unpack_from('<f', pmd_data, index)[0]
            index += 4

            # Convert angles to coordinates
            x, y = angles_to_coord(left_angle, right_angle)
            x = -x
            path_data.append(f"L {x} {y}")

        if path_data:
            path_data[0] = path_data[0].replace("L", "M", 1)
            paths.append(' '.join(path_data))

    return paths

def read_pmd_file(file_path):
    with open(file_path, 'rb') as file:
        return file.read()

def main(pmd_files, output_svg_path):
    svg_paths = []

    for file_path in pmd_files:
        try:
            pmd_data = read_pmd_file(file_path)
            paths = pmd_to_svg(pmd_data)
            for path_data in paths:
                filename = file_path.split('/')[-1]
                svg_paths.append((filename, path_data))
        except Exception as e:
            print(f"Error processing file {file_path}: {e}")

    svg_content = '<svg xmlns="http://www.w3.org/2000/svg" version="1.1">'
    for filename, path in svg_paths:
        svg_content += f'<path d="{path}" stroke="black" fill="none"><title>{filename}</title></path>'
    svg_content += '</svg>'

    with open(output_svg_path, 'w') as svg_file:
        svg_file.write(svg_content)
    print(f'Successfully written to {output_svg_path}')

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python pmd_to_svg.py input1.pmd input2.pmd ... output.svg")
    else:
        input_files = sys.argv[1:-1]  # All arguments except the last one
        output_file = sys.argv[-1]    # The last argument is the output SVG file
        main(input_files, output_file)