import setting

# ------ Function to get command from face gesture ----------
# -----------------------------------------------------------
def determine_command(latest_center, screen_center, dead_zone_x, dead_zone_y):
    if latest_center is None or screen_center is None:
        return "STAY"
    
    dx = latest_center[0] - screen_center[0]
    dy = latest_center[1] - screen_center[1]

    def no_move(theta, dead_zone):
        return 0 if (abs(theta) < dead_zone) else theta
    
    dx, dy = no_move(dx, dead_zone_x), no_move(dy, dead_zone_y)

    if (abs(dx) == 0 and abs(dy) == 0): return "STAY"
    else:
        if (dy < 0 and dx == 0): return "UP"
        if (dy < 0 and dx > 0): return "UPRIGHT"
        if (dx > 0 and dy == 0): return "RIGHT"
        if (dy > 0 and dx > 0): return "DOWNRIGHT"
        if (dy > 0 and dx == 0): return "DOWN"
        if (dy > 0 and dx < 0): return "DOWNLEFT"
        if (dx < 0 and dy == 0): return "LEFT"
        if (dy < 0 and dx < 0): return "UPLEFT"


def to_px(landmark, w, h):
    return int(landmark.x * w), int(landmark.y * h)        

def avg_points(points):
    pts = setting.np.array(points, dtype=setting.np.float32)
    c = pts.mean(axis=0)
    return int(c[0]), int(c[1])

def ema_update(prev_xy, new_xy, alpha):
    if prev_xy is None: 
        return new_xy
    return (
        # (1 - SMOOTH_ALPHA) * current_coordinates + SMOOTH_ALPHA * next_coordinates
        # The lower the SMOOTH_ALPHA, the less adjustment of current_coordinates
        int((1 - alpha) * prev_xy[0] + alpha * new_xy[0]),
        int((1 - alpha) * prev_xy[1] + alpha * new_xy[1]),
    )

