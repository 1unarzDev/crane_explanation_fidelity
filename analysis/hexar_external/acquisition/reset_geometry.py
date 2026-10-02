"""Pure measured reset position/heading check; not physical goal attainment."""
import math

POSITION_TOLERANCE_M=.05
HEADING_TOLERANCE_RAD=.05


def review(position,quaternion,target_xy,target_yaw):
    if len(position)!=3 or len(quaternion)!=4 or len(target_xy)!=2:
        raise ValueError('XYZ position, XYZW quaternion and XY reset target required')
    values=(*position,*quaternion,*target_xy,target_yaw)
    if any(type(v) not in (int,float) or not math.isfinite(v) for v in values):
        raise ValueError('finite measured reset geometry required')
    x,y,z,w=quaternion
    if abs(x*x+y*y+z*z+w*w-1)>1e-3:
        raise ValueError('normalized measured quaternion required')
    yaw=math.atan2(2*(w*z+x*y),1-2*(y*y+z*z))
    heading_error=abs(math.atan2(math.sin(yaw-target_yaw),math.cos(yaw-target_yaw)))
    position_error=math.hypot(position[0]-target_xy[0],position[1]-target_xy[1])
    return dict(x=position[0],y=position[1],z=position[2],yaw_rad=yaw,
        quaternion_xyzw=list(quaternion),error_m=position_error,heading_error_rad=heading_error,
        position_in_tolerance=position_error<=POSITION_TOLERANCE_M,
        heading_in_tolerance=heading_error<=HEADING_TOLERANCE_RAD,
        in_tolerance=position_error<=POSITION_TOLERANCE_M and heading_error<=HEADING_TOLERANCE_RAD,
        source='Gazebo GetEntityState world pose; reset only, not goal arrival')
