import numpy as np
from config import HM, RE_KM

def az_el_to_lat_lon(s_lat, s_lon, az, el,  hm=HM, R=RE_KM):
    """
    Calculates subionospheric point and deltas from site
    Parameters:
        s_lat, slon - site latitude and longitude in radians
        hm - ionposheric maximum height (km)
        az, el - azimuth and elevation of the site-sattelite line of sight in
            radians
        R - Earth radius (km)
    """
    #TODO use meters
    psi = np.pi / 2 - el - np.arcsin(np.cos(el) * R / (R + hm))
    lat = bi = np.arcsin(np.sin(s_lat) * np.cos(psi) + np.cos(s_lat) * np.sin(psi) * np.cos(az))
    lon = s_lon + np.arcsin(np.sin(psi) * np.sin(az) / np.cos(bi))

    lon = lon - 2 * np.pi if lon > np.pi else lon
    lon = lon + 2 * np.pi if lon < -np.pi else lon
    return lat, lon