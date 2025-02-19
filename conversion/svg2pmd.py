import xml.etree.ElementTree as ET
import struct
import numpy as np
import os

# Constants for angle conversion
LEFT_CLOSE_ARM = 11
LEFT_FAR_ARM = 11
RIGHT_CLOSE_ARM = 11
RIGHT_FAR_ARM = 11
MOTOR_SPACE = 2.5

def angles_to_coord(left_arm_angle, right_arm_angle):
    ''' Function inputs the motor angle relative to a perpindicular line from
    the robot body (in degrees)

    OUTPUT:
    x and y coordinates of the target node in cm

    Coordinate system:
    -center of robot (between to motors) is origin
    -left is negative values
    -right is positive values
    -down is positive values
    '''

    # Converting to radians
    left_arm_angle_rad = (left_arm_angle) * (np.pi / 180)
    right_arm_angle_rad = (180-right_arm_angle) * (np.pi / 180)

    # Finding coord for left pivot
    opp_left = np.cos(left_arm_angle_rad) * LEFT_CLOSE_ARM
    adj_left = np.sin(left_arm_angle_rad) * LEFT_CLOSE_ARM

    opp_left = -(opp_left + (MOTOR_SPACE / 2)) # Adjusting for space b/w motors

    # Finding coord for right pivot
    opp_right = np.cos(right_arm_angle_rad) * RIGHT_CLOSE_ARM
    adj_right = np.sin(right_arm_angle_rad) * RIGHT_CLOSE_ARM

    opp_right = opp_right + (MOTOR_SPACE / 2)

    # Finding triangle height (base is between to pivots and peak is the target)
    a = np.absolute(opp_right - opp_left)
    b = np.absolute(adj_right - adj_left)
    base = np.sqrt((a**2) + (b**2))

    _c = RIGHT_FAR_ARM
    _a = base / 2
    if _c > _a:
        height = np.sqrt((_c**2) - (_a**2))
    else:
        height = np.sqrt((_a**2) - (_c**2))

    # Finding midpoint between two pivots
    mid_x = (opp_right + opp_left) / 2
    mid_y = (adj_right + adj_left) / 2

    # Finding direction from midpoint to target
    end_angle = np.arctan(mid_x / mid_y)

    # Calculating target coord
    x_add = np.sin(end_angle) * height
    y_add = np.cos(end_angle) * height

    x = mid_x + x_add
    y = mid_y + y_add

    return x, y

def coord_to_angles(x, y):
    from scipy.optimize import minimize

    def error(angles):
        left, right = angles
        x_calc, y_calc = angles_to_coord(left, right)
        return (x_calc - x)**2 + (y_calc - y)**2

    # Initial guess based on typical configurations
    initial_guess = [45.0, 135.0]
    result = minimize(error, initial_guess, method='Nelder-Mead', tol=1e-6)
    if result.success:
        return (result.x[0], result.x[1])
    else:
        # Fallback to another method or adjust initial guess
        result = minimize(error, initial_guess, method='Powell', tol=1e-6)
        if result.success:
            return (result.x[0], result.x[1])
        else:
            raise ValueError(f"Optimization failed for coordinates ({x}, {y})")

def parse_svg(svg_path):
    tree = ET.parse(svg_path)
    root = tree.getroot()

    paths_by_file = {}

    # Iterate over path elements
    for path in root.iter('{http://www.w3.org/2000/svg}path'):
        title = path.find('{http://www.w3.org/2000/svg}title').text
        data = path.attrib['d']
        
        print(f'Parsing {title}')

        if title not in paths_by_file:
            paths_by_file[title] = []

        # Determine the format based on the presence of commas
        if ',' in data:
            # Inkscape format: coordinates separated by commas
            path_commands = data.replace(',', ' ').split()
        else:
            # Standard format: coordinates separated by spaces
            path_commands = data.split()

        # Parse path data assuming "M x y L ..." and converting it to (x, y) points
        points = [(float(path_commands[i + 1]), float(path_commands[i + 2])) 
                  for i in range(0, len(path_commands) - 1, 3) 
                  if path_commands[i] in ('M', 'L')]

        paths_by_file[title].append([(coord_to_angles(-x, y)) for x, y in points])

    return paths_by_file

def write_pmd(file_name, segments):
    with open(file_name, 'wb') as file:
        # Write header with magic number 1 and segment count
        file.write(struct.pack('<BI', 1, len(segments)))
        
        for segment in segments:
            # Write the number of points in each segment
            file.write(struct.pack('<I', len(segment)))

            for left_angle, right_angle in segment:
                # Write each point's angles as 4-byte floats
                file.write(struct.pack('<ff', left_angle, right_angle))

def main(input_svg, output_directory):
    paths_by_file = parse_svg(input_svg)

    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    
    for file_name, segments in paths_by_file.items():
        output_file_path = os.path.join(output_directory, file_name)
        write_pmd(output_file_path, segments)
        print(f'Written to {output_file_path}')

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python svg_to_pmd.py input.svg output_directory")
    else:
        main(sys.argv[1], sys.argv[2])