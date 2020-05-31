"""Usage: file_parser.py [-h][--filepath=<arg>][--wanted_tables=<arg>][--new_table=<arg>]

Examples:
	Filepath: e.g. input --cluster='/path/to/file'
	Wanted tables: e.g. input --scale_factor='[[]'Global_Projection'], ['North_Polar_Projection', 'South_Polar_Projection']]'
	New tables: e.g. input --element='[[True], [False, True]]'

-h  Help file
--filepath=<arg>  Path to desired file
--wanted_tables=<arg> Data that you want from the file
--new_tables=<arg>  Whether the tables have been imported before or not
"""

#Imports
from docopt import docopt
import h5py
import netCDF4
import numpy as np
import pandas as pd
import rasterio
import os
import re
from datetime import datetime

def all_names(open_file):
    """Return the names of all of the groups in an HDF5 file.
    Uses h5py's Group.visit() function to recursively visit all of the groups in the file
    and append their names to a list.

    Parameters
    ----------
    open_file : HDF5 file
    	The currently open HDF5 file that is being read

    Returns
    -------
    names : lst
    	A list of strings representing the names of all of the groups in the HDF5 file
    """

    names = []

    def name_lister(name):
        names.append(name)

    open_file.visit(name_lister)
    return names

def hdf5_parser(filepath, filenames, wanted_tables, new_table = False):
    """Return a list of dataframes containing the desired data from an HDF5 file, the names of those tables,
    and whether the tables have been imported before or not.

    Parameters
    ----------
    filepath : HDF5 file
        The path to the desired HDF5 file
    wanted_tables : List[List[str]]
        A list of lists of strings representing the names of the desired tables
    new_table : List[bool]
        Describes whether the tables have been imported before or not

    Returns
    -------
    wanted_dfs : List[DataFrame]
        A list of pandas dataframes containing the desired data from the HDF5 file
    keys : List[List[str]]
        A list of lists of strings representing the names of the tables
    new_table : List[List[bool]]
        Describes whether the tables have been imported before or not
    """

    file = h5py.File(filepath, 'r')

    #Get data from wanted tables, keeping appropriate links
    data = [[] for i in range(len(wanted_tables))]
    for i in range(len(wanted_tables)):
    	for j in range(len(wanted_tables[i])):
    		data[i].append(file[wanted_tables[i][j]][()])

    #Transform multi-dimensional arrays into lists
    listed_dat = [{} for i in range(len(data))]
    for i in range(len(data)):
    	for j in range(len(data[i])):
    		sublst = []
    		for k in range(len(data[i][j])):
    			for l in range(len(data[i][j].T)):
    				sublst.append(data[i][j][k][l])
    		#sublst = np.array(sublst)
    		listed_dat[i][wanted_tables[i][j]] = sublst

    #Get date
    try:
    	match = re.search(r'\d{4}\d{2}\d{2}', filepath)
    	date = datetime.strptime(match.group(), '%Y%m%d').date()
    except ValueError:
    	match = re.search(r'\d{4}.\d{2}.\d{2}', filepath)
    	date = datetime.strptime(match.group(), '%Y.%m.%d').date()
    date_str = str(date).replace('-', '_')

    #Transform to dataframes
    wanted_dfs = []
    keys = [[] for i in range(len(wanted_tables))]
    for i in range(len(listed_dat)):
    	try:
    		wanted_dfs.append(pd.DataFrame.from_dict(listed_dat[i]))
    		keys[i].append(wanted_tables[i])
    	except Exception:
    		print('Cannot transform to DataFrame, keeping as dictionary.')
    		wanted_dfs.append(listed_dat[i])
    		keys[i].append(wanted_tables[i])

    #Make dates the same length as the rest of the data
    dates = [[] for i in range(len(wanted_dfs))]
    for i in range(len(wanted_dfs)):
    	for j in range(len(wanted_dfs[i])):
    		dates[i].append(date_str)

    #Append dates to the dataframes
    final_wanted_dfs = [[] for i in range(len(wanted_dfs))]
    for i in range(len(wanted_dfs)):
    	final_wanted_dfs[i].append(pd.concat([wanted_dfs[i], pd.DataFrame({'date': dates[i]})], axis=1))
    	keys[i].append('date')

    file.close()

    #Write to csv
    csv_names = []
    for i in range(len(final_wanted_dfs)):
    	csv_names.append(filenames[i] + date_str)

    for i in range(len(final_wanted_dfs)):
    	for j in range(len(final_wanted_dfs[i])):
    		final_wanted_dfs[i][j].to_csv(csv_names[i] + '.csv')

    return final_wanted_dfs, keys, new_table

def netcdf4_parser(filepath, wanted_tables, new_table = False):
    """Return a list of dataframes containing the desired data from a NetCDF4 file.  Also return whether the
    tables have been imported before or not.

    Parameters
    ----------
    filepath : NetCDF4 file
    	The path to the desired NetCDF4 file
    wanted_tables : List[List[str]]
    	A list of lists of strings representing the names of the desired tables
    new_table : List[bool]
    	Describes whether the tables have been imported before or not

    Returns
    -------
    wanted_dfs : List[DataFrame]
    	A list of pandas dataframes containing the desired data from the NetCDF4 file
    keys : List[List[str]]
        A list of lists of strings representing the names of the tables
    new_table : List[List[bool]]
    	Describes whether the tables have been imported before or not
    """

    file = netCDF4.Dataset(filepath, 'r')
    dicts = [{} for i in range(len(wanted_tables))]
    keys = [[] for i in range(len(wanted_tables))]
    for i in range(len(wanted_tables)):
        for j in range(len(wanted_tables[i])):
            dicts[i][wanted_tables[i][j]] = file[wanted_tables[i][j]][:]
            keys[i].append(wanted_tables[i][j])


    wanted_dfs = []
    for i in range(len(dicts)):
        try:
            wanted_dfs.append(pd.DataFrame.from_dict(dicts[i]))
        except Exception:
            wanted_dfs.append(dicts[i])
    file.close()
    return wanted_dfs, keys, new_table

def geotiff_parser(filepath, wanted_tables, new_table = False):
    """Return a list of dataframes containing the desired data from a GeoTIFF file.  Also return whether the
    tables have been imported before or not.

    Parameters
    ----------
    filepath : GeoTIFF file
    	The path to the desired GeoTIFF file
    wanted_tables : List[List[str]]
    	A list of lists of strings representing the names of the desired tables
    new_table : List[bool]
    	Describes whether the tables have been imported before or not

    Returns
    -------
    wanted_dfs : List[DataFrame]
    	A list of pandas dataframes containing the desired data from the GeoTIFF file
    keys : List[List[str]]
        A list of lists of strings representing the names of the tables
    new_table : List[List[bool]]
    	Describes whether the tables have been imported before or not
    """

    file = rasterio.open(filepath)

    wanted_dfs = []
    keys = [[] for i in range(len(wanted_tables))]
    for i in range(len(wanted_tables)):
        for j in range(len(wanted_tables[i])):
            wanted_dfs.append(pd.DataFrame(file.read(wanted_tables[i][j])))
            keys[i].append(wanted_tables[i][j])
    file.close()

    return wanted_dfs, keys, new_table

def textfile_parser(filepath, wanted_tables, new_table = False):
    """Return a list of dataframes containing the desired data from a text file.  Also return whether the
    tables have been imported before or not.

    Parameters
    ----------
    filepath : text file
    	The path to the desired text file
    wanted_tables : List[List[str]]
    	A list of lists of strings representing the names of the desired tables
    new_table : List[bool]
    	Describes whether the tables have been imported before or not

    Returns
    -------
    wanted_dfs : List[DataFrame]
    	A list of pandas dataframes containing the desired data from the text file
    keys : List[List[str]]
        A list of lists of strings representing the names of the tables
    new_table : List[List[bool]]
    	Describes whether the tables have been imported before or not
    """

    file = pd.read_csv(filepath)

    dicts = [{} for i in range(len(wanted_tables))]
    keys = [[] for i in range(len(wanted_tables))]
    for i in range(len(wanted_tables)):
        for j in range(len(wanted_tables[i])):
            dicts[i][wanted_tables[i][j]] = file[wanted_tables[i][j]]
            keys[i].append(wanted_tables[i][j])

    wanted_dfs = []
    for i in range(len(dicts)):
        wanted_dfs.append(pd.DataFrame.from_dict(dicts[i]))

    return wanted_dfs, keys, new_table

def file_parser(filepath, filenames, wanted_tables, new_table = False):
    """Return a list of dataframes containing the desired data from a file.  Also return whether the
    tables have been imported before or not.

    If the filetype is not one that has been predefined here, returns an error.

    Parameters
    ----------
    filepath : file
    	The path to the desired file
    wanted_tables : List[str]
    	A list of lists of strings representing the names of the desired tables
    new_table : List[List[bool]]
    	Describes whether the tables have been imported before or not

    Returns
    -------
    output_tables : List[DataFrame]
    	A list of pandas dataframes containing the desired data from the file
    output_keys : List[List[str]]
        A list of lists of strings representing the names of the tables
    new_table : List[List[bool]]
    	Describes whether the tables have been imported before or not
    """

    #Read HDF4 files
    if filepath.endswith('.hdf') or filepath.endswith('.hdf4') or filepath.endswith('.h4'):
        #Convert HDF4 to HDF5
        os.system('chmod u+x h4toh5')
        os.system('./h4toh5 ' + filepath)
        path = ''
        suffixes = ['.hdf', '.hdf4', '.h4']
        for i in suffixes:
            if filepath.endswith(i):
                path = filepath[:-len(i)] + '.h5'
        #Read HDF5 file
        output_tables, output_keys, new_tables = hdf5_parser(path, filenames, wanted_tables, new_table)
        return output_tables, output_keys, new_tables
    #Read HDF5 files
    elif filepath.endswith('.hdf5') or filepath.endswith('.h5') or filepath.endswith('.he5'):
        output_tables, output_keys, new_tables = hdf5_parser(filepath, filenames, wanted_tables, new_table)
        return output_tables, output_keys, new_tables
    #Read NetCDF4 files
    elif filepath.endswith('.nc') or filepath.endswith('.netcdf') or filepath.endswith('.netcdf4'): #I think these files only have extension .nc but put others to be safe
        output_tables, output_keys, new_tables = netcdf4_parser(filepath, wanted_tables, new_table)
        return output_tables, output_keys, new_tables
    #Read GeoTIFF files
    elif filepath.endswith('.tif') or filepath.endswith('.tiff'):
        output_tables, output_keys, new_tables = geotiff_parser(filepath, wanted_tables, new_table)
        return output_tables, output_keys, new_tables
    #Read textfiles
    elif filepath.endswith('.txt') or filepath.endswith('.csv'):
        output_tables, output_keys, new_tables = textfile_parser(filepath, wanted_tables)
        return output_tables, output_keys, new_tables
    else:
        print('Unknown file type, cannot be parsed.')

if __name__ == '__main__':
	arguments = docopt(__doc__)

	output_tables, output_keys, new_tables = file_parser(arguments['--filepath'], arguments[--wanted_tables], arguments[--new_table])
