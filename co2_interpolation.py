def CO2_interpolation(filepath, new_filepath):
	"""Write a csv for each day in the month with the interpolated CO2 data.
	
	Parameters
	----------
	filepath : str
		Path to all CO2 files
	new_filepath : str
		Path to save interpolated files
		
	Returns
	-------
	None
	"""
	
	#Get all files and read into DataFrames
	files = os.listdir(filepath)
	all_files = []
	for i in range(len(files)):
		all_files.append(pd.read_csv(filepath + files[i]))
		
	#Sort files by date
	sorted_files = sorted(all_files,key=lambda x:x["date"].max(axis=0))
	
	#Get each date (1 per file)
	dates = []
	for i in range(len(sorted_files)):
		dates.append(sorted_files[i]['date'][0])
		
	#Get the years and the months
	yrs = []
	mos = []
	for i in range(len(dates)):
		yrs.append(int(dates[i][0:4]))
		mos.append(int(dates[i][5:7]))
		
	#Get the number of days in each month (excluding the first day, which will be the original file)
	monthranges = []
	for i in range(len(dates)):
		monthranges.append(monthrange(yrs[i], mos[i]))
	num_days = []
	for i in range(len(monthranges)):
		num_days.append(monthranges[i][1] - 1)
		
	#Get all of the data in the files
	CO2_data = []
	lat_data = []
	long_data = []
	for i in range(len(sorted_files)):
		CO2_data.append(sorted_files[i]['Data/latticeInformation/XCO2Average'])
		lat_data.append(sorted_files[i]['Data/geolocation/latitude'])
		long_data.append(sorted_files[i]['Data/geolocation/longitude'])
		
	#Interpolate each month
	interps = [[] for i in range(len(num_days)-1)]
	xvals = []
	xs = []
	for i in range(len(num_days)):
		xvals.append(np.linspace(0, num_days[i], num_days[i]))
		xs.append([0, num_days[i]])
		
	for i in range(0, len(num_days)-1):
		for j in range(len(CO2_data[i])):
			if CO2_data[i][j] == -9999. and CO2_data[i+1][j] == -9999.:
				interps[i].append(np.full(num_days[i], -9999.))
			elif CO2_data[i][j] == -9999. and CO2_data[i+1][j] != -9999.:
				interps[i].append(np.interp(xvals[i], xs[i], [np.mean(CO2_data[i][CO2_data[i] != -9999.]), CO2_data[i+1][j]]))
			elif CO2_data[i+1][j] == -9999. and CO2_data[i][j] != -9999:
				interps[i].append(np.interp(xvals[i], xs[i], [CO2_data[i][j], np.mean(CO2_data[i+1][CO2_data[i+1] != -9999.])]))
			else:
				interps[i].append(np.interp(xvals[i], xs[i], [CO2_data[i][j], CO2_data[i+1][j]]))
	for i in range(len(interps)):
		interps[i] = np.array(interps[i])
		
	#Make arrays of the correct length for all of the dates to add to the DataFrames
	full_dates = [[] for i in range(len(interps))]
	for i in range(len(interps)):
		for j in range(len(interps[i].T)):
			if len(str(j + 2)) == 1:
				full_dates[i].append(np.full(len(interps[i]), dates[i][0:4] + '_' + dates[i][5:7] + '_' + str(0) + str(j + 2)))
			else: 
				full_dates[i].append(np.full(len(interps[i]), dates[i][0:4] + '_' + dates[i][5:7] + '_' + str(j + 2)))
				
	#Create new DataFrames
	new_dfs = [[] for i in range(len(interps))]
	for i in range(len(interps)):
		for j in range(len(interps[i].T)):
			new_dfs[i].append(pd.DataFrame({'Data/geolocation/latitude': lat_data[i],
											'Data/geolocation/longitude': long_data[i],
											'Data/latticeInformation/XCO2Average': interps[i][:,j],
											'date': full_dates[i][j]}))
											
	#Write to csv
	for i in range(len(new_dfs)):
		for j in range(len(new_dfs[i])):
			new_dfs[i][j].to_csv(new_filepath + full_dates[i][j][0] + '.csv')