"""
Unit conversion utilities for the JOULE process calculator.
"""

def celsius_to_kelvin(T_celsius):
    """
    Konvertiert Temperatur von Celsius nach Kelvin
    
    Parameter:
    T_celsius : float
        Temperatur in °C
        
    Returns:
    float
        Temperatur in K
    """
    return T_celsius + 273.15


def kelvin_to_celsius(T_kelvin):
    """
    Konvertiert Temperatur von Kelvin nach Celsius
    
    Parameter:
    T_kelvin : float
        Temperatur in K
        
    Returns:
    float
        Temperatur in °C
    """
    return T_kelvin - 273.15


def bar_to_pascal(p_bar):
    """
    Konvertiert Druck von Bar nach Pascal
    
    Parameter:
    p_bar : float
        Druck in bar
        
    Returns:
    float
        Druck in Pa
    """
    return p_bar * 1e5


def pascal_to_bar(p_pascal):
    """
    Konvertiert Druck von Pascal nach Bar
    
    Parameter:
    p_pascal : float
        Druck in Pa
        
    Returns:
    float
        Druck in bar
    """
    return p_pascal / 1e5