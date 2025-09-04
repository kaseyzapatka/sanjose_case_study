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



#
# Create mapping function
# ----------------------------------------
# Create a choropleth map that plots a station point and buffer overlays.
# Can optionally save the figure to a file and add notes at the bottom.

# libraries
import matplotlib.pyplot as plt
import mapclassify

# mapping function
def choropleth_map(
    gdf,                                    # data with geometry
    column,                                 # column to display
    title,                                  # title
    station_gdf=None,                       # station overlay
    buffer_gdf=None,                        # buffer overlay
    k=5,                                    # number of classes
    cmap="Blues",                           # color scheme
    save=False,                             # save figure
    filename="../output/choropleth_map.pdf", # file name
    notes=None                              # notes
):    
    # ensure consistent CRS
    gdf = gdf.to_crs(epsg=4269)
    if station_gdf is not None:
        station_gdf = station_gdf.to_crs(epsg=4269)
    if buffer_gdf is not None:
        buffer_gdf = buffer_gdf.to_crs(epsg=4269)
    
    fig, ax = plt.subplots(figsize=(10, 10))
    ax.axis("off")
    
    # main choropleth map
    gdf.plot(
        ax=ax,
        column=column,
        scheme="NaturalBreaks",
        k=k,
        legend=True,
        cmap=cmap,
        edgecolor="black",
        linewidth=0.5
    )
    
    # station overlay
    if station_gdf is not None:
        station_gdf.plot(
            ax=ax, color="black", marker=".", markersize=100, label="Station"
        )
    
    # 2 mile radius overlay
    if buffer_gdf is not None:
        buffer_gdf.boundary.plot(
            ax=ax, color="blue", linestyle="--", linewidth=2, label="Buffer"
        )
    
    # title
    ax.set_title(title, fontsize=14)
    
    # footnotes 
    if notes:
        fig.text(0.1, 0.01, notes, ha='left', fontsize=10)
    
    # save
    if save:
        plt.savefig(filename, format="pdf", bbox_inches="tight")
        print(f"Figure saved as {filename}")

    
    plt.show()
