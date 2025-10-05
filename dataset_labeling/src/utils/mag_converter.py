import numpy as np
from pathlib import Path
from numpy.typing import NDArray

def read_geomagnetic_grid(file_path: Path) -> NDArray:
    """
    Reads the geomagnetic coordinate grid from a file.

    Assumes structure as:

    #Lat, Lon, MLat, MLon
     -90.0    -180.0   -74.5    18.0
     -90.0    -179.0   -74.5    18.0
     -90.0    -178.0   -74.5    18.0
     -90.0    -177.0   -74.5    18.0
    
    Returns:
        data: numpy array with columns [Lat, Lon, MLat, MLon]
    """
    return np.loadtxt(file_path, comments="#")


def bilinear_interpolate(
    lat: float, 
    lon: float, 
    grid: NDArray, 
    latstep: float=1.0, 
    lonstep: float=1.0
)-> tuple[float, float]: 
    """
    Interpolates the geomagnetic coordinates for a given geographical location.

    Args:
        lat (float): Latitude in degrees
        lon (float): Longitude in degrees
        grid (np.ndarray): Numpy array with columns [Lat, Lon, MLat, MLon]
        latstep (float): Latitude in degrees
        lonstep (float): Longitude in degrees

    Returns:
        tuple: (interpolated MLat, MLon)
    """

    # Handle poles: return exact value without interpolation
    if lat == 90.0 or lat == -90.0:
        # Find the closest match (lon may be any value at poles)
        pole_rows = grid[grid[:, 0] == lat]
        if pole_rows.size == 0:
            raise ValueError(f"No data found for pole at latitude {lat}")
        # Return the first match (all longitudes at the pole are equivalent)
        return pole_rows[0][2], pole_rows[0][3]

    # -180 and 180 is the same point 
    lon = ((lon + 180) % 360) - 180

    # Round lat/lon down to nearest integer grid
    lat0 = np.floor(lat)
    lon0 = np.floor(lon)
    lat1 = lat0 + 1
    lon1 = lon0 + 1

    # Get four corner points
    mask = (
        ((grid[:, 0] == lat0) & (grid[:, 1] == lon0)) |
        ((grid[:, 0] == lat0) & (grid[:, 1] == lon1)) |
        ((grid[:, 0] == lat1) & (grid[:, 1] == lon0)) |
        ((grid[:, 0] == lat1) & (grid[:, 1] == lon1))
    )
    neighbors = grid[mask]

    if neighbors.shape[0] != 4:
        raise ValueError("Could not find a full 2x2 grid for interpolation.")

    # Sort neighbors by (lat, lon)
    neighbors = sorted(neighbors, key=lambda x: (x[0], x[1]))
    Q11 = neighbors[0]
    Q12 = neighbors[1]
    Q21 = neighbors[2]
    Q22 = neighbors[3]

    # Bilinear interpolation formula
    def interpolate(x, y, Q11, Q12, Q21, Q22):
        x1, y1 = Q11[0], Q11[1]
        x2, y2 = Q22[0], Q22[1]
        if x2 == x1 or y2 == y1:
            return Q11[2], Q11[3]  # Avoid division by zero
        fx = (x - x1) / (x2 - x1)
        fy = (y - y1) / (y2 - y1)
        
        _y = (
            Q11[2] * (1 - fx) * (1 - fy) +
            Q21[2] * fx * (1 - fy) +
            Q12[2] * (1 - fx) * fy +
            Q22[2] * fx * fy
        )
        _x = (
            Q11[3] * (1 - fx) * (1 - fy) +
            Q21[3] * fx * (1 - fy) +
            Q12[3] * (1 - fx) * fy +
            Q22[3] * fx * fy
        )
        return _y, _x

    return interpolate(lat, lon, Q11, Q12, Q21, Q22)