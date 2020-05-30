def temp_averaging(filepath, temp_type, new_filepath):
	"""Write a csv with the averaged day and night temperatures.
	
	Parameters
	----------
	filepath : str
		Path to the file to average
	temp_type : str
		'SurfSkinTemp' or 'SurfAirTemp'
	new_filepath : str
		Path to save the file
		
	Returns
	-------
	None
	"""
	
	#Get data
	df = pd.read_csv(filepath)
	avg_temp = np.zeros(len(df['ascending/Data Fields/' + temp_type + '_A']))
	day_dat = df['ascending/Data Fields/' + temp_type + '_A']
	night_dat = df['descending/Data Fields/' + temp_type + '_D']
	date = df['date'][0]
	
	#Average day and night temperatures
	for i in range(len(avg_temp)):
		if day_dat[i] == -9999. and night_dat[i] == -9999.:
			avg_temp[i] = -9999.
		elif day_dat[i] == -9999. and night_dat[i] != -9999.:
			avg_temp[i] = night_dat[i]
		elif night_dat[i] == -9999. and day_dat[i] != -9999:
			avg_temp[i] = day_dat[i]
		else:
			avg_temp[i] = np.mean((day_dat[i], night_dat[i]))
			
	#Create new DataFrame
	new_df = pd.DataFrame({'location/Data Fields/latitude': df['location/Data Fields/Latitude'], 
						'location/Data Fields/longitude': df['location/Data Fields/Longitude'], 
						'Average' + temp_type: avg_temp,
						'date': df['date']})
	#Write to csv
	new_df.to_csv(new_filepath + 'AIRS_Average' + temp_type + '_global_daily_' + date + '.csv')