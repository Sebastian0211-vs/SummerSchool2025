import math

def get_intersection_between_two_circles(A1, B1, C1, A2, B2, C2):
    """
    Find intersection points between two circles using direct analytical solution.
    Circles in expanded form: x^2 + y^2 + Ax + By + C = 0
    """
    
    # Calculate coefficients for the linear equation from subtracting the two circle equations
    # (A1 - A2)x + (B1 - B2)y + (C1 - C2) = 0
    a = A1 - A2
    b = B1 - B2
    c = C1 - C2
    
    # Check if circles are identical
    if abs(a) < 1e-10 and abs(b) < 1e-10 and abs(c) < 1e-10:
        return []
    
    # Check if lines are parallel (a = b = 0 but c != 0) (both constants)
    if abs(a) < 1e-10 and abs(b) < 1e-10:
        return []
    
    # Choose which variable to solve for to avoid division by near-zero values
    if abs(b) > 1e-10:
        # Substitution into first circle equation: x² + y² + A1*x + B1*y + C1 = 0

        # y = -(ax + c)/b
        # x^2 + (-(ax + c)/b)^2 + A1*x + B1*(-(ax + c)/b) + C1 = 0
        # x^2 + (ax + c)^2/b^2 + A1*x - B1*(ax + c)/b + C1 = 0

        # Expand (ax + c)^2/b^2 = (a^2*x^2 + 2*a*c*x + c^2)/b^2

        # Multiply everything by b^2 to clear denominators:
        # b^2*x^2 + (ax + c)^2 + A1*b^2*x - B1*b*(ax + c) + C1*b^2 = 0
        # b^2*x^2 + a^2*x^2 + 2*a*c*x + c^2 + A1*b^2*x - B1*b*a*x - B1*b*c + C1*b^2 = 0
        
        # Collect terms: (b^2 + a^2)x^2 + (2*a*c + A1*b^2 - B1*b*a)x + (c^2 - B1*b*c + C1*b^2) = 0
        quad_a = b*b + a*a
        quad_b = 2*a*c + A1*b*b - B1*b*a
        quad_c = c*c - B1*b*c + C1*b*b
        
        # Solve quadratic equation using discriminent
        discriminant = quad_b*quad_b - 4*quad_a*quad_c
        
        if discriminant < 0:
            return []
        
        sqrt_disc = math.sqrt(discriminant)
        x1 = (-quad_b + sqrt_disc) / (2*quad_a)
        x2 = (-quad_b - sqrt_disc) / (2*quad_a)
        
        # Calculate corresponding y values
        y1 = -(a*x1 + c) / b
        y2 = -(a*x2 + c) / b
        
        if abs(discriminant) < 1e-10:
            return [(x1, y1)]
        else:
            return [(x1, y1), (x2, y2)]
    
    else:  
        # Solve for x in terms of y: x = -(by + c)/a
        # Substitute x = -(by + c)/a into first circle equation
        quad_a = a*a + b*b
        quad_b = 2*b*c + B1*a*a - A1*a*b
        quad_c = c*c - A1*a*c + C1*a*a
        
        # Solve quadratic equation using discriminent
        discriminant = quad_b*quad_b - 4*quad_a*quad_c
        
        if discriminant < 0:
            return []  # No real solutions
        
        sqrt_disc = math.sqrt(discriminant)
        y1 = (-quad_b + sqrt_disc) / (2*quad_a)
        y2 = (-quad_b - sqrt_disc) / (2*quad_a)
        
        # Calculate corresponding x values
        x1 = -(b*y1 + c) / a
        x2 = -(b*y2 + c) / a
        
        if abs(discriminant) < 1e-10:
            return [(x1, y1)]
        else: 
            return [(x1, y1), (x2, y2)]
