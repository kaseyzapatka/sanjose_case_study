#
# spatial join function
# --------------------------------------

# import necessary libraries
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import geopandas as gpd
from shapely.geometry import Point


# define spatial join function
def sjoin_parcels_to_zd(parcels, zoning, how="largest"):
    """
    Spatially join parcels with zoning districts (zd), ensuring only one zoning 
    district per parcel.
    
    Parameters
    ----------
    parcels : gpd.GeoDataFrame
        Parcels GeoDataFrame
    zd : gpd.GeoDataFrame
        Zoning districts GeoDataFrame
    how : str, optional
        Method to resolve overlaps. Options:
        - "largest" : keep the zoning district with the largest area of overlap
        - "first"   : keep the first zoning district encountered
        
    Returns
    -------
    gpd.GeoDataFrame
        Parcels with one zoning district assigned (NaN if no overlap)
    """
    
    # Ensure same CRS
    if parcels.crs != zoning.crs:
        zoning = zoning.to_crs(parcels.crs)
    
    # Spatial join (parcels may appear multiple times if overlapping multiple zd)
    joined = gpd.sjoin(parcels, zoning, how="left", predicate="intersects")
    
    if how == "largest":
        # Compute intersection area safely
        def get_overlap_area(row):
            if pd.isna(row.index_right):  # no zoning match
                return 0
            return row.geometry.intersection(zoning.loc[row.index_right, "geometry"]).area
        
        joined["overlap_area"] = joined.apply(get_overlap_area, axis=1)
        
        # Keep zoning district with largest overlap per parcel - THIS DOESNT WORK SINCE THE INDEX NEEDS TO BE RESET. DELETE IN LATER ITERATIONS
        joined = joined.loc[joined.groupby(joined.index)["overlap_area"].idxmax()]
    
    elif how == "first":
        # Just keep the first zoning district encountered per parcel
        joined = joined.loc[~joined.index.duplicated(keep="first")]
    
    else:
        raise ValueError("how must be 'largest' or 'first'")
    
    return joined.drop(columns=["index_right"], errors="ignore")