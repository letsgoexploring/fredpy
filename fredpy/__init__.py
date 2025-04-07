import requests
import dateutil
import datetime
import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import warnings
import statsmodels.api as sm
import time
tsa = sm.tsa

# Read recession data. First try to parse html table at nber.org
try:
    # Read HTML table at nber.org
    tables = pd.read_html('https://www.nber.org/research/data/us-business-cycle-expansions-and-contractions')

    # Remove the first row because there is no starting peak
    cycle_dates = tables[0]

    # Remove the first row that has not peak date
    cycle_dates = cycle_dates.drop(0).reset_index(drop=True)

    # Is a recession currently underway? Set today as the trough
    if not cycle_dates['Business Cycle Reference Dates','Trough Year'].iloc[-1].isdigit():
        
        today = pd.to_datetime('today').date()
        
        cycle_dates.loc[cycle_dates.index[-1],('Business Cycle Reference Dates','Trough Year')] = str(today.year)
        cycle_dates.loc[cycle_dates.index[-1],('Business Cycle Reference Dates','Trough Month')] = str(today.month_name())

    # Join month and year columns to produce datetime columns for peak and trough dates
    cycle_dates['peaks'] = pd.to_datetime(cycle_dates['Business Cycle Reference Dates','Peak Year'].astype(str).astype(str).str.replace('*','',regex=False) + '-' + cycle_dates['Business Cycle Reference Dates','Peak Month'].astype(str).str.replace('*','',regex=False))
    cycle_dates['troughs'] = pd.to_datetime(cycle_dates['Business Cycle Reference Dates','Trough Year'].astype(str).astype(str).str.replace('*','',regex=False) + '-' + cycle_dates['Business Cycle Reference Dates','Trough Month'].astype(str).str.replace('*','',regex=False))

    # Drop unnecessary columns
    cycle_dates = cycle_dates[['peaks','troughs']]

except:

    try:
        # Read table of NBER peak/trough dates on my GitHub page
        cycle_dates = pd.read_csv('https://raw.githubusercontent.com/letsgoexploring/fredpy-package/gh-pages/business%20cycle%20dates/business_cycle_dates.csv')

        # Is a recession currently underway? Set today as the trough
        if pd.isna(cycle_dates.troughs.iloc[-1]):
            cycle_dates.troughs.iloc[-1] = pd.to_datetime('today').strftime('%Y-%m-%d')
        
        # Overwrite  original columns with datetime values
        cycle_dates['peaks'] = pd.to_datetime(cycle_dates.peaks)
        cycle_dates['troughs'] = pd.to_datetime(cycle_dates.troughs)

    except:
        print('Internet connection required. Check connection.')

# API key attribute needs to be set

# Try to find file in OSX home directory
try:
    items = os.getcwd().split('/')[:3]
    items.append('fred_api_key.txt')
    path = '/'.join(items)
    with open(path,'r') as api_key_file:
        api_key = api_key_file.readline()

except:
    api_key=None

def load_api_key(path):
    try:
        # Try to load file from currect working directory
        with open(path,'r') as api_key_file:
            return api_key_file.readline()
    except:

        try:
            # Try to find file in OSX home directory
            items = os.getcwd().split('/')[:3]
            items.append(path)
            path = '/'.join(items)
            with open(path,'r') as api_key_file:
                return api_key_file.readline()

        except:
            path = os.path.join(os.getcwd(),path)
            with open(path,'r') as api_key_file:
                return api_key_file.readline()


# Initialize cache dictionary
series_cache = {}


######################################################################################################
# The series class and methods

class series:

    '''Defines a class for downloading, storing, and manipulating data from FRED.'''

    def __init__(self,series_id=None,observation_date=None,cache=True):

        '''Initializes an instance of the series class.

        Args:
            series_id (string):         unique FRED series ID. If series_id equals None, an empty series 
                                            object is created.
            observation_date (string):  MM-DD-YYYY or YYYY-MM-DD formatted state string. Indicates the final 
                                            date at which the series is observed. I.e., excludes revisions made
                                            after observation_date.
            cache (bool):               Whether to store a copy of the series for the current session to reduce 
                                            queries to the FRED API. Default: True

        Returns:
            None

        Attributes:
            data:                       (Pandas Series) data values with dates as index.
            date_range:                 (string) specifies the dates of the first and last observations.
            frequency:                  (string) data frequency. 'Daily', 'Weekly', 'Monthly', 'Quarterly', 'Semiannual', or 'Annual'.
            frequency_short:            (string) data frequency. Abbreviated. 'D', 'W', 'M', 'Q', 'SA, or 'A'.
            last_updated:               (string) date series was last updated.
            notes:                      (string) details about series. Not available for all series.
            observation_date:           (string) vintage date at which data are observed. YYYY-MM-DD
            release:                    (string) statistical release containing data.
            seasonal_adjustment:        (string) specifies whether the data has been seasonally adjusted.
            seasonal_adjustment_short:  (string) specifies whether the data has been seasonally adjusted. Abbreviated.
            series_id:                  (string) unique FRED series ID code.
            source:                     (string) original source of the data.
            t:                          (int) number corresponding to frequency: 365 for daily, 52 for weekly, 12 for monthly, 4 for quarterly, and 1 for annual.
            title:                      (string) title of the data series.
            units:                      (string) units of the data series.
            units_short:                (string) units of the data series. Abbreviated.
        '''

        # Verify API key is stored
        if api_key is None:
            raise ValueError('fredpy.api_key value not assigned. You need to provide your key for the FRED API.')

        # Observation date for request
        if observation_date is None:

            observation_date = datetime.datetime.today().strftime('%Y-%m-%d')

        else:

            observation_date = pd.to_datetime(observation_date).strftime('%Y-%m-%d')

        if type(series_id) == str:

            if series_id+'_'+observation_date in series_cache.keys() and cache:



                # self = series_cache[series_id+'_'+observation_date].copy()

                cached = series_cache[series_id+'_'+observation_date].copy()

                self.date_range = cached.date_range
                self.data = cached.data
                self.frequency = cached.frequency
                self.frequency_short = cached.frequency_short
                self.last_updated = cached.last_updated
                self.notes = cached.notes
                self.observation_date = cached.observation_date
                self.release = cached.release
                self.seasonal_adjustment = cached.seasonal_adjustment
                self.seasonal_adjustment_short = cached.seasonal_adjustment_short
                self.series_id = cached.series_id
                self.source = cached.source
                self.t = cached.t
                self.title = cached.title
                self.units = cached.units
                self.units_short = cached.units_short


            else:


                path = 'fred/series'

                parameters = {'series_id':series_id,
                  'realtime_start':observation_date,
                  'realtime_end':observation_date,
                  'file_type':'json'
                 }

                r = fred_api_request(api_key=api_key,path=path,parameters=parameters)
                results = r.json()

                self.series_id = series_id
                self.title = results['seriess'][0]['title']
                self.frequency = results['seriess'][0]['frequency']
                self.frequency_short = results['seriess'][0]['frequency_short']
                self.observation_date = datetime.datetime.strptime(observation_date,"%Y-%m-%d").strftime('%B %d, %Y')
                self.units = results['seriess'][0]['units']
                self.units_short = results['seriess'][0]['units_short']
                self.seasonal_adjustment = results['seriess'][0]['seasonal_adjustment']
                self.seasonal_adjustment_short = results['seriess'][0]['seasonal_adjustment_short']
                self.last_updated = results['seriess'][0]['last_updated']
                
                try:
                    self.notes = results['seriess'][0]['notes']
                except:
                    self.notes = ''

                obs_per_year = {'D':365,'W':52,'M':12,'Q':4,'SA':2,'A':1}
                try:
                    self.t = obs_per_year[self.frequency_short]
                except:
                    self.t = np.nan


                path = 'fred/series/observations'

                parameters = {'series_id':series_id,
                  'realtime_start':observation_date,
                  'realtime_end':observation_date,
                  'file_type':'json'
                 }

                r = fred_api_request(api_key=api_key,path=path,parameters=parameters)
                results = r.json()

                data = pd.DataFrame(results['observations'],columns =['date','value'])
                data = data.replace('.', np.nan)
                data['date'] = pd.to_datetime(data['date'])
                
                data = data.set_index('date')['value'].astype(float)

                # Try to infer frequency:
                try:
                    data = data.asfreq(pd.infer_freq(data.index))
                except:
                    pass

                self.data = data
                self.date_range = 'Range: '+str(self.data.index[0])[:10]+' to '+str(self.data.index[-1])[:10]



                path = 'fred/series/release'

                parameters = {'series_id':series_id,
                  'realtime_start':observation_date,
                  'realtime_end':observation_date,
                  'file_type':'json'
                 }

                r = fred_api_request(api_key=api_key,path=path,parameters=parameters)
                results = r.json()

                self.release = results['releases'][0]['name']
                release_id = results['releases'][0]['id']


                path = 'fred/release/sources'

                parameters = {'series_id':series_id,
                  'release_id':release_id,
                  'file_type':'json'
                 }

                r = fred_api_request(api_key=api_key,path=path,parameters=parameters)
                results = r.json()

                self.source = results['sources'][0]['name']

                if cache:

                    series_cache[series_id+'_'+observation_date] = self.copy()

        else:

            self.date_range = ''
            self.data = pd.Series([],pd.to_datetime([]),dtype=np.float64)
            self.frequency = ''
            self.frequency_short = ''
            self.last_updated = ''
            self.notes = ''
            self.observation_date = ''
            self.release = ''
            self.seasonal_adjustment = ''
            self.seasonal_adjustment_short = ''
            self.series_id = ''
            self.source = ''
            self.t = 0
            self.title = ''
            self.units = ''
            self.units_short = ''

    
    def apc(self,log=False,backward=True):

        '''Computes the percentage change in the data over one year.

        Args:
            log (bool):      If True, computes the percentage change as 100⋅log[x(t)/x(t-k)], where k is
                                 the number of observations per year.
                             If False (default), compute the percentage change as 100⋅[(x(t)/x(k−1)−1].
            backward (bool): If True (default), compute percentage change from the previous year. 
                                 If False, compute percentage change from current to next year.

        Returns:
            fredpy series
        '''

        new_series = self.copy()
        
        T = len(self.data)
        
        if backward==True:
            ratio = self.data/self.data.shift(self.t)
        else:
            ratio = self.data.shift(-self.t)/self.data
            
        if log==True:
            new_series.data = 100*np.log(ratio).dropna()
        else:
            new_series.data = 100*(ratio-1).dropna()
                               
        new_series.units = 'Percent'
        new_series.units_short = '%'
        new_series.title = 'Annual Percentage Change in '+self.title
        new_series.date_range = 'Range: '+str(new_series.data.index[0])[:10]+' to '+str(new_series.data.index[-1])[:10]

        return new_series

    
    def as_frequency(self,freq=None,method='mean'):

        '''Convert a fredpy series to a lower frequency.

        Args:
            freq (string):      Abbreviation of desired frequency: 'D','W','M','Q','A'
            method (string):    How to resample the data: 'first', 'last', 'mean' (default), 'median',
                                    'min', 'max', 'sum'
        Returns:
            fredpy series
        '''

        new_series = self.copy()

        obs_per_year = {'D':365,'W':52,'M':12,'Q':4,'A':1}
        map_of_freqency_abbreviations = {'D':'Daily','W':'Weekly','M':'Monthly','Q':'Quarterly','A':'Annual'}


        try:
            new_series.t = obs_per_year[freq]
            new_series.frequency_short=freq
            new_series.frequency=map_of_freqency_abbreviations[freq]

        except:
            raise ValueError("freq must be 'D', 'W', 'M', 'Q', or 'A'")

        if self.t<new_series.t:
            warnings.warn('Warning: You are converting series to a higher frequency and this method may not behave as you expect.')

        map_to_pandas_frequencies = {'D':'D','W':'W','M':'MS','Q':'QS','A':'AS'}

        if method == 'first':

            new_series.data = self.data.resample(map_to_pandas_frequencies[freq]).first()

        elif method == 'last':

            new_series.data = self.data.resample(map_to_pandas_frequencies[freq]).last()

        elif method == 'mean':

            new_series.data = self.data.resample(map_to_pandas_frequencies[freq]).mean()

        elif method == 'median':

            new_series.data = self.data.resample(map_to_pandas_frequencies[freq]).median()

        elif method == 'min':

            new_series.data = self.data.resample(map_to_pandas_frequencies[freq]).min()

        elif method == 'max':

            new_series.data = self.data.resample(map_to_pandas_frequencies[freq]).max()

        elif method == 'sum':

            new_series.data = self.data.resample(map_to_pandas_frequencies[freq]).sum()

        new_series.date_range = 'Range: '+str(new_series.data.index[0])[:10]+' to '+str(new_series.data.index[-1])[:10]

        return new_series

    
    def bp_filter(self,low=None,high=None,K=None):

        '''Computes the bandpass (Baxter-King) filter of the data. Returns two fredpy.series
        instances containing the cyclical and trend components of the data:

            new_series_cycle,new_series_trend

        .. Note: 
            In computing the bandpass filter, K observations are lost from each end of the
            original series to the data are 2K elements shorter than in the original series.

        Args:
            low (int):  Minimum period for oscillations. Default: None, recommendation used.
            high (int): Maximum period for oscillations. Default: None, recommendation used.
            K (int):    Lead-lag length of the filter. Default: None, recommendation used.

        Recommendations:

            Monthly data:   low=24, high=84, K=84
            Quarterly data: low=6, high=32, K=12
            Annual data:    low=1.5, high=8, K=3

        Returns:
            two fredpy.series instances
        '''

        new_series_cycle = self.copy()
        new_series_trend = self.copy()

        if all(v is None for v in [low, high, K]) and self.frequency_short=='M':
            low=24
            high=84
            K=84

        elif all(v is None for v in [low, high, K]) and self.frequency_short=='Q':
            low=6
            high=32
            K=12

        elif all(v is None for v in [low, high, K]) and self.frequency_short=='A':
            low=1.5
            high=8
            K=3



        # if low==6 and high==32 and K==12 and self.t !=4:
        #     print('Warning: data frequency is not quarterly!')
        # elif low==3 and high==8 and K==1.5 and self.t !=1:
        #     print('Warning: data frequency is not annual!')
            
        cycle = tsa.filters.bkfilter(self.data,low=low,high=high,K=K)
        actual = self.data.iloc[K:-K]
        trend = actual - cycle
        
        new_series_cycle.data = cycle
        new_series_cycle.units = 'Deviation relative to trend'
        new_series_cycle.units_short = 'Dev. rel. to trend'
        new_series_cycle.title = self.title+' - deviation relative to trend (bandpass filtered)'
        new_series_cycle.date_range = 'Range: '+str(new_series_cycle.data.index[0])[:10]+' to '+str(new_series_cycle.data.index[-1])[:10]

        new_series_trend.data = trend
        new_series_trend.title = self.title+' - trend (bandpass filtered)'
        new_series_trend.date_range = 'Range: '+str(new_series_trend.data.index[0])[:10]+' to '+str(new_series_trend.data.index[-1])[:10]

        return new_series_cycle,new_series_trend


    def cf_filter(self,low=None,high=None):

        '''Computes the Christiano-Fitzgerald (CF) filter of the data. Returns two fredpy.series
        instances containing the cyclical and trend components of the data:

            new_series_cycle,new_series_trend

        Args:
            low (int):  Minimum period for oscillations. Default: None. 18 for monthly data, 6 for quarterly 
                        data, and 2 for annual data.
            high (int): Maximum period for oscillations. Default: None. 96 for monthly data, 32 for quarterly 
                        data, and 8 for annual data.

        Recommendations:

            Monthly data:   low=18, high=96
            Quarterly data: low=6, high=32
            Annual data:    low=2, high=8

        Returns:
            two fredpy.series instances
        '''

        new_series_cycle = self.copy()
        new_series_trend = self.copy()

        if all(v is None for v in [low, high]) and self.frequency_short=='M':
            low=18
            high=96

        elif all(v is None for v in [low, high]) and self.frequency_short=='Q':
            low=6
            high=32

        elif all(v is None for v in [low, high]) and self.frequency_short=='A':
            low=2
            high=8

        # if low==6 and high==32 and self.t !=4:
        #     print('Warning: data frequency is not quarterly!')
        # elif low==1.5 and high==8 and self.t !=4:
        #     print('Warning: data frequency is not quarterly!')

        actual = self.data
        cycle, trend = tsa.filters.cffilter(self.data,low=low, high=high, drift=False)

        new_series_cycle.data = cycle
        new_series_cycle.units = 'Deviation relative to trend'
        new_series_cycle.units_short = 'Dev. rel. to trend'
        new_series_cycle.title = self.title+' - deviation relative to trend (CF filtered)'

        new_series_trend.data = trend
        new_series_trend.title = self.title+' - trend (CF filtered)'

        return new_series_cycle,new_series_trend

    
    def copy(self):

        '''Returns a copy of a series object.

        Args:

        Returs:
            fredpy series
        '''

        new_series = series()


        new_series.data = self.data.copy()
        new_series.date_range = self.date_range
        new_series.frequency = self.frequency
        new_series.frequency_short = self.frequency_short
        new_series.last_updated = self.last_updated
        new_series.notes = self.notes
        new_series.release = self.release
        new_series.seasonal_adjustment = self.seasonal_adjustment
        new_series.seasonal_adjustment_short = self.seasonal_adjustment_short
        new_series.series_id = self.series_id
        new_series.source = self.source
        new_series.t = self.t
        new_series.title = self.title
        new_series.units = self.units
        new_series.units_short = self.units_short

        return new_series


    def diff_filter(self):

        '''Computes the first difference filter of original series. Returns two fredpy.series
        instances containing the cyclical and trend components of the data:

            new_series_cycle,new_series_trend

        Note:
            In computing the first difference filter, the first observation from the original series is
            lost so data are 1 element shorter than in the original series.

        Args:

        Returns:
            two fredpy.series instances
        '''

        new_series_cycle = self.copy()
        new_series_trend = self.copy()

        new_series_cycle.data = self.data.diff().dropna() - self.data.diff().dropna().mean()
        new_series_cycle.units = 'Deviation relative to trend'
        new_series_cycle.units_short = 'Dev. rel. to trend'
        new_series_cycle.date_range = 'Range: '+str(new_series_cycle.data.index[0])[:10]+' to '+str(new_series_cycle.data.index[-1])[:10]

        new_series_trend.data = self.data.shift(1).dropna()
        new_series_trend.title = self.title+' - trend (first difference filtered)'
        new_series_trend.date_range = 'Range: '+str(new_series_trend.data.index[0])[:10]+' to '+str(new_series_trend.data.index[-1])[:10]

        return new_series_cycle,new_series_trend

    
    def divide(self,object2):

        '''Divides the data from the current fredpy series by the data from object2.

        Args:
            object2 (int, float, numpy ndarray, or similar or fredpy series)

        Note:
            You are responsibile for making sure that dividing the series makes sense.

        Returns:
            fredpy series
        '''

        return divide(self,object2)

    def drop_nan(self):

        '''Removes missing (NaN) values.

        Args:

        Returns:
            fredpy series
        '''

        new_series = self.copy()
        
        new_series.data = new_series.data.dropna()
        new_series.date_range = 'Range: '+str(new_series.data.index[0])[:10]+' to '+str(new_series.data.index[-1])[:10]

        return new_series


    def hp_filter(self,lamb=None,two_sided=True):

        '''Computes the Hodrick-Prescott (HP) filter of the data. Returns two fredpy.series
        instances containing the cyclical and trend components of the data:

            new_series_cycle,new_series_trend

        Args:
            lamb (int): The Hodrick-Prescott smoothing parameter. Default: None. Recommendations: 

                            104976000000 for daily data.
                            129600 for monthly data,
                            1600 for quarterly data,
                            6.25 for annual data,
                        
                        In general, set lambda to: 1600*[number of observations per quarter]**4
            two_sided (bool)    Whether to compute the two-sided HP filter or the one-sided filter 
                                used in STock and Watson (1999).
            
        Returns:
            two fredpy.series instances
        '''

        new_series_cycle = self.copy()
        new_series_trend = self.copy()


        if lamb is None and self.frequency_short=='M':
            lamb = 129600

        elif lamb is None and self.frequency_short=='Q':
            lamb = 1600

        elif lamb is None and self.frequency_short=='A':
            lamb = 6.25

        elif lamb is None and self.frequency_short=='D':
            lamb = 104976000000

        # if lamb==1600 and self.t !=4:
        #     print('Warning: data frequency is not quarterly!')
        # elif lamb==129600 and self.t !=12:
        #     print('Warning: data frequency is not monthly!')
        # elif lamb==6.25 and self.t !=1:
        #     print('Warning: data frequency is not annual!')
            
        
        if two_sided:
            cycle, trend = tsa.filters.hpfilter(self.data,lamb=lamb)
        else:

            n_obs = len(self.data)

            cycle = self.data.copy()
            cycle.iloc[:2] = 0
            trend = self.data.copy()

            trend[:2] = self.data.iloc[:2]

            for i in range(n_obs-2):
                iter_cycle, iter_trend = tsa.filters.hpfilter(self.data[:2+1+i],lamb=lamb)
                cycle.iloc[2+i] = iter_cycle.iloc[-1]
                trend.iloc[2+i] = iter_trend.iloc[-1]


        new_series_cycle.data = cycle
        new_series_cycle.units = 'Deviation relative to trend'
        new_series_cycle.units_short = 'Dev. rel. to trend'
        new_series_cycle.title = self.title+' - deviation relative to trend (HP filtered)'

        new_series_trend.title = self.title+' - trend (HP filtered)'
        new_series_trend.data = trend

        return new_series_cycle,new_series_trend

    
    def linear_filter(self):

        '''Computes a simple linear filter of the data using OLS. Returns two fredpy.series
        instances containing the cyclical and trend components of the data:

            new_series_cycle,new_series_trend

        Args:

        Returns:
            two fredpy.series instances
        '''

        new_series_cycle = self.copy()
        new_series_trend = self.copy()

        y = self.data
        time = np.arange(len(self.data))
        x = np.column_stack([time])
        x = sm.add_constant(x)
        model = sm.OLS(y,x)
        result= model.fit()
        pred  = result.predict(x)
        
        cycle= y-pred
        trend= pd.Series(pred,index=self.data.index)

        new_series_cycle.data = cycle
        new_series_cycle.units = 'Deviation relative to trend'
        new_series_cycle.units_short = 'Dev. rel. to trend'
        new_series_cycle.title = self.title+' - deviation relative to trend (linearly filtered via OLS)'

        new_series_trend.title = self.title+' - trend (linearly filtered via OLS)'
        new_series_trend.data = trend

        return new_series_cycle,new_series_trend

    
    def log(self):
        
        '''Computes the natural log of the data

        Args:

        Returns:
            fredpy series
        '''

        new_series = self.copy()

        new_series.data = np.log(new_series.data)
        new_series.units = 'Log '+new_series.units
        new_series.units_short = 'Log '+new_series.units_short
        new_series.title = 'Log '+new_series.title

        return new_series

    def ma(self,length,center=False):

        '''Computes a moving average with window equal to length. If center is True, then the 
        two-sided moving average is computed. Otherwise, the moving average will be one-sided.

        Args:
            length (int): window length of the one-sided moving average.
            center (bool): False (default) - one-sided MA. True - two-sided MA.

        Returns:
            fredpy series
        '''

        new_series = self.copy()

        new_series.data = new_series.data.rolling(window=length,center=center).mean().dropna()
        new_series.date_range = 'Range: '+str(new_series.data.index[0])[:10]+' to '+str(new_series.data.index[-1])[:10]
        if center:
            new_series.title = self.title+' (: one-sided moving average)'
        else:
            new_series.title = self.title+' (: two-sided moving average)'

        return new_series

    
    def minus(self,object2):

        '''Subtracts the data from object2 from the data from the current fredpy series.

        Args:
            object2 (int, float, numpy ndarray, or similar or fredpy series)

        Note:
            You are responsibile for making sure that adding the series makes sense.

        Returns:
            fredpy series
        '''

        return minus(self,object2)


    def pc(self,log=False,backward=True,annualized=False):

        '''Computes the percentage change in the data from the preceding period.

        Args:
            log (bool):        If True, computes the percentage change as 100⋅log[x(t)/x(t-1)]. 
                                   If False (default), compute the percentage change as 100⋅[x(t)/x(t−1)−1].
            backward (bool):   If True (default), compute percentage change from the previous period. 
                                   If False, compute percentage change from current to next period.
            annualized (bool): Default: False: If True, percentage change is computed at an annual rate. 
                                    E.g., if the data were monthly and log==True, then the annualized
                                    percentage change would be:
                                   
                                       100⋅12⋅log[x(t)/x(t−1)].

        Returns:
            fredpy series
        '''

        new_series = self.copy()
        
        T = len(self.data)
        if annualized:
            t = self.t
        else:
            t = 1
        
        if backward==True:
            ratio = self.data/self.data.shift(1)
        else:
            ratio = self.data.shift(-1)/self.data
            
        if log==True:
            new_series.data = 100*t*np.log(ratio).dropna()
        else:
            new_series.data = 100*(ratio**t-1).dropna()

        new_series.units = 'Percent'
        new_series.units_short = '%'
        new_series.title = 'Percentage Change in '+self.title
        new_series.date_range = 'Range: '+str(new_series.data.index[0])[:10]+' to '+str(new_series.data.index[-1])[:10]

        return new_series

    
    def per_capita(self,civ_pop = True):

        '''Transforms the data into per capita terms by dividing by a measure of the
            total population of the United States:

        Args:
            civ_pop (string): If civ_pop == True, use Civilian noninstitutional population defined as 
                                persons 16 years of age and older (Default). Else, use the total US 
                                population.

        Returns:
            fredpy series
        '''

        new_series = self.copy()

        if civ_pop ==True:
            population= series('CNP16OV').as_frequency(new_series.frequency_short)
        else:
            population= series('POP').as_frequency(new_series.frequency_short)
    
        new_series,population = window_equalize([new_series,population])

        new_series.data = new_series.data/population.data

        new_series.title = new_series.title+' Per Capita'
        new_series.units = new_series.units+' Per Thousand People'
        new_series.units_short = new_series.units_short+' Per Thousand People'
        new_series.date_range = 'Range: '+str(new_series.data.index[0])[:10]+' to '+str(new_series.data.index[-1])[:10]

        return new_series

    
    def plot(self,**kwargs):

        '''Equivalent to calling .plot() method on the self.data Pandas Series object.'''

        self.data.plot(**kwargs)


    def plus(self,object2):

        '''Adds the data from the current fredpy series to the data from object2.

        Args:
            object2 (int, float, numpy ndarray, or similar or fredpy series)

        Note:
            You are responsibile for making sure that adding the series makes sense.

        Returns:
            fredpy series
        '''

        return plus(self,object2)

    
    def recent(self,N):

        '''Restrict the data to the most recent N observations.

        Args:
            N (int): Number of periods to include in the data window.

        Returns:
            fredpy series
        '''

        new_series = self.copy()

        new_series.data  =new_series.data.iloc[-N:]
        new_series.date_range = 'Range: '+str(new_series.data.index[0])[:10]+' to '+str(new_series.data.index[-1])[:10]

        return new_series

    
    def recessions(self,ax=None,color='0.5',alpha=0.5):
        
        '''Creates recession bars for plots. Unless 'ax' is specified, be used after 
        a plot has been made but before either (1) a new plot is created or (2) a 
        show command is issued.

        Args:
            ax (matplotlib.axes._subplots.AxesSubplot): Matplotlib axis object to plot recession bars. Default: None
            color (string):                             Color of the bars. Default: '0.5'
            alpha (float):                              Transparency of the recession bars. Must be between 0 and 1 
                                                        Default: 0.5

        Returns:
        '''

        series_peaks = []
        series_troughs = []

        start = self.data.index[0]
        end = self.data.index[-1]

        recessions(start=start,end=end,ax=ax,color=color,alpha=alpha)

        # for k in range(len(cycle_dates)):
            
        #     if cycle_dates['peaks'].loc[k]<date_begin and date_begin < cycle_dates['troughs'].loc[k]:
        #         series_peaks.append(date_begin)
        #         series_troughs.append(cycle_dates['troughs'].loc[k])
            
                
        #     elif date_begin < cycle_dates['peaks'].loc[k] and date_end > cycle_dates['troughs'].loc[k]:
        #         series_peaks.append(cycle_dates['peaks'].loc[k])
        #         series_troughs.append(cycle_dates['troughs'].loc[k])
                
        #     elif cycle_dates['peaks'].loc[k]<date_end and cycle_dates['troughs'].loc[k] > date_end:
        #         series_peaks.append(cycle_dates['peaks'].loc[k])
        #         series_troughs.append(date_end)

        # for k in range(len(series_peaks)):
        #     plt.axvspan(series_peaks[k], series_troughs[k], edgecolor= color, facecolor=color, alpha=alpha)

    
    def times(self,object2):

        '''Multiplies the data from the current fredpy series with the data from object2.

        Args:
            object2 (int, float, numpy ndarray, or similar or fredpy series)

        Note:
            You are responsibile for making sure that adding the series makes sense.

        Returns:
            fredpy series
        '''

        return times(self,object2)


    def window(self,start_end):

        '''Restricts the data to a specified date window.

        Args:

            start_end (list):   is an ordered pair: start_end = [start, end]

                                    start is the date of the minimum date
                                    end is the date of the maximum date
        
                                both are strings in either 'yyyy-mm-dd' or 'mm-dd-yyyy' format

        Returns:
            fredpy series
        '''

        new_series = self.copy()

        new_series.data = new_series.data.loc[start_end[0]:start_end[1]]

        if len(new_series.data)>0:
            new_series.date_range = 'Range: '+str(new_series.data.index[0])[:10]+' to '+str(new_series.data.index[-1])[:10]
        else:
            new_series.date_range = 'Range: Null'


        return new_series

######################################################################################################
# Additional functions

def divide(object1,object2):

    '''Divides the data from the object1 by the data from object2.

    Args:
        object1 (int, float, numpy ndarray, or similar or fredpy series)
        object2 (int, float, numpy ndarray, or similar or fredpy series)

    Note:
        You are responsibile for making sure that adding the series makes sense.

    Returns:
        fredpy series
    '''

    if not isinstance(object1, series) and not isinstance(object2, series):

        return object1/object2

    elif not isinstance(object1, series) and isinstance(object2, series):

        new_series = object2.copy()
        new_series.data = object1/new_series.data

        return new_series

    elif not isinstance(object2, series) and isinstance(object1, series):

        new_series = object1.copy()
        new_series.data = new_series.data/object2

        return new_series

    else:

        if not object1.data.index.equals(object2.data.index):

            raise ValueError('object1 and object2 do not have the same observation dates')

        else:

            new_series = series()

            new_series.title = object1.title +' divided by '+object2.title
            if object1.source == object2.source:
                new_series.source = object1.source
            else:
                new_series.source = object1.source +' and '+object2.source
            new_series.frequency = object1.frequency
            new_series.frequency_short = object1.frequency_short
            new_series.units = object1.units +' / '+object2.units
            new_series.units_short = object1.units_short +' / '+object2.units_short
            new_series.t = object1.t
            new_series.date_range = object1.date_range

            if object1.seasonal_adjustment == object2.seasonal_adjustment:
                new_series.seasonal_adjustment = object1.seasonal_adjustment
                new_series.seasonal_adjustment_short = object1.seasonal_adjustment_short
            else:
                new_series.seasonal_adjustment = object1.seasonal_adjustment +' and '+object2.seasonal_adjustment
                new_series.seasonal_adjustment_short = object1.seasonal_adjustment_short +' and '+object2.seasonal_adjustment_short

            if object1.last_updated == object2.last_updated:
                new_series.last_updated = object1.last_updated
            else:
                new_series.last_updated = object1.last_updated +' and '+object2.last_updated

            if object1.release == object2.release:
                new_series.release = object1.release
            else:
                new_series.release = object1.release +' and '+object2.release
                
            new_series.series_id = object1.series_id +' and '+object2.series_id
            new_series.data  = object1.data/object2.data

            return new_series



    
    
def fred_api_request(api_key,path,parameters):
    
    '''Queries the FRED API. Returns a requests.models.Response object if successful, otherwise will
    raise an error with a message that is hopefully helpful. Reference for API querries: 

    https://fred.stlouisfed.org/docs/api/fred/

        Args:
            api_key (string):   32-character alpha-numeric string.
            path (string):      API path.  List of available paths here: 

        Returns:
            requests.models.Response

        Attributes:
            None
    '''
    
    

    status_code = None
    request_count = 0

    while request_count <= 10:

        request_url = 'https://api.stlouisfed.org/'+path+'?'+'api_key='+str(api_key)+'&'

        for key in parameters.keys():
            request_url+=key+'='+str(parameters[key])+'&'
            

        r = requests.get(request_url)

        status_code = r.status_code

        if status_code == 200:
            break

        elif status_code == 429:
            print('FRED API error: API limit exceeded in API query (status code: '+str(status_code)+'). Retry in '+str(5+request_count)+' seconds.')
            time.sleep(5+request_count)

        elif status_code == 504:
            print('FRED API error: Gateway Time-out< in API query (status code: '+str(status_code)+'). Retry in '+str(5+request_count)+' seconds.')
            time.sleep(5+request_count)


        else:
            r.raise_for_status()

        request_count+=1

    if request_count >10 and status_code != 200:

        raise Exception('Unknown FRED API error. Status code: ',status_code)

    return r


def get_vintage_dates(series_id):

    '''Returns vintage dates for series available from ALFRED.

    Args:
        series_id (string): unique FRED series ID.

    Returns:
        list'''

    request_url = 'https://api.stlouisfed.org/fred/series/vintagedates?series_id=GDPDEF&api_key='+api_key+'&file_type=json'
    r = requests.get(request_url)
    results = r.json()

    return results['vintage_dates']


def minus(object1,object2):

    '''Subtracts the data from object2 from the data from object1.

    Args:
        object1 (int, float, numpy ndarray, or similar or fredpy series)
        object2 (int, float, numpy ndarray, or similar or fredpy series)

    Note:
        You are responsibile for making sure that adding the series makes sense.

    Returns:
        fredpy series
    '''

    if not isinstance(object1, series) and not isinstance(object2, series):

        return object1-object2

    elif not isinstance(object1, series) and isinstance(object2, series):

        new_series = object2.copy()
        new_series.data = object1-new_series.data

        return new_series

    elif not isinstance(object2, series) and isinstance(object1, series):

        new_series = object1.copy()
        new_series.data = new_series.data-object2

        return new_series

    else:

        if not object1.data.index.equals(object2.data.index):

            raise ValueError('object1 and object2 do not have the same observation dates')

        else:

            new_series = series()

            new_series.title = object1.title +' minus '+object2.title
            if object1.source == object2.source:
                new_series.source = object1.source
            else:
                new_series.source = object1.source +' and '+object2.source
            new_series.frequency = object1.frequency
            new_series.frequency_short = object1.frequency_short
            new_series.units = object1.units +' - '+object2.units
            new_series.units_short = object1.units_short +' - '+object2.units_short
            new_series.t = object1.t
            new_series.date_range = object1.date_range

            if object1.seasonal_adjustment == object2.seasonal_adjustment:
                new_series.seasonal_adjustment = object1.seasonal_adjustment
                new_series.seasonal_adjustment_short = object1.seasonal_adjustment_short
            else:
                new_series.seasonal_adjustment = object1.seasonal_adjustment +' and '+object2.seasonal_adjustment
                new_series.seasonal_adjustment_short = object1.seasonal_adjustment_short +' and '+object2.seasonal_adjustment_short

            if object1.last_updated == object2.last_updated:
                new_series.last_updated = object1.last_updated
            else:
                new_series.last_updated = object1.last_updated +' and '+object2.last_updated

            if object1.release == object2.release:
                new_series.release = object1.release
            else:
                new_series.release = object1.release +' and '+object2.release
                
            new_series.series_id = object1.series_id +' and '+object2.series_id
            new_series.data  = object1.data-object2.data

            return new_series


def plus(object1,object2):

    '''Adds the data from object1 to the data from object2.

    Args:
        object1 (int, float, numpy ndarray, or similar or fredpy series)
        object2 (int, float, numpy ndarray, or similar or fredpy series)

    Note:
        You are responsibile for making sure that adding the series makes sense.

    Returns:
        fredpy series
    '''

    if not isinstance(object1, series) and not isinstance(object2, series):

        return object1+object2

    elif not isinstance(object1, series) and isinstance(object2, series):

        new_series = object2.copy()
        new_series.data = new_series.data+object1

        return new_series

    elif not isinstance(object2, series) and isinstance(object1, series):

        new_series = object1.copy()
        new_series.data = new_series.data+object2

        return new_series

    else:

        if not object1.data.index.equals(object2.data.index):

            raise ValueError('object1 and object2 do not have the same observation dates')

        else:

            new_series = series()

            new_series.title = object1.title +' plus '+object2.title
            if object1.source == object2.source:
                new_series.source = object1.source
            else:
                new_series.source = object1.source +' and '+object2.source
            new_series.frequency = object1.frequency
            new_series.frequency_short = object1.frequency_short
            new_series.units = object1.units +' + '+object2.units
            new_series.units_short = object1.units_short +' + '+object2.units_short
            new_series.t = object1.t
            new_series.date_range = object1.date_range

            if object1.seasonal_adjustment == object2.seasonal_adjustment:
                new_series.seasonal_adjustment = object1.seasonal_adjustment
                new_series.seasonal_adjustment_short = object1.seasonal_adjustment_short
            else:
                new_series.seasonal_adjustment = object1.seasonal_adjustment +' and '+object2.seasonal_adjustment
                new_series.seasonal_adjustment_short = object1.seasonal_adjustment_short +' and '+object2.seasonal_adjustment_short

            if object1.last_updated == object2.last_updated:
                new_series.last_updated = object1.last_updated
            else:
                new_series.last_updated = object1.last_updated +' and '+object2.last_updated

            if object1.release == object2.release:
                new_series.release = object1.release
            else:
                new_series.release = object1.release +' and '+object2.release
                
            new_series.series_id = object1.series_id +' and '+object2.series_id
            new_series.data  = object1.data+object2.data

            return new_series

def recessions(start=None,end=None,ax=None,color='0.5',alpha=0.5):
        
    '''Creates recession bars for time series plots.
    
    Args:
        start (NoneType, string, or Timestamp):     Starting date. Default: None
        end (NoneType, string, or Timestamp):       Ending date. Default: None
        ax (matplotlib.axes._subplots.AxesSubplot): Matplotlib axis object to plot recession bars. Default: None
        color (string):                             Color of the bars. Default: '0.5'
        alpha (float):                              Transparency of the recession bars. Must be between 0 and 1 
                                                        Default: 0.5
    Returns:
    '''

    series_peaks = []
    series_troughs = []

    if start is None:
        start = cycle_dates.iloc[0]['peaks']
        
    elif type(start) == str:
        start = pd.to_datetime(start)
        
    if end is None:
        end = pd.to_datetime('today')
        
    elif type(end) == str:
        end = pd.to_datetime(end)

    for k in range(len(cycle_dates)):

        if cycle_dates['peaks'].loc[k]<start and start < cycle_dates['troughs'].loc[k]:
            series_peaks.append(start)
            series_troughs.append(cycle_dates['troughs'].loc[k])


        elif start < cycle_dates['peaks'].loc[k] and end > cycle_dates['troughs'].loc[k]:
            series_peaks.append(cycle_dates['peaks'].loc[k])
            series_troughs.append(cycle_dates['troughs'].loc[k])

        elif cycle_dates['peaks'].loc[k]<end and cycle_dates['troughs'].loc[k] > end:
            series_peaks.append(cycle_dates['peaks'].loc[k])
            series_troughs.append(end)

    for k in range(len(series_peaks)):
        if ax is None:
            plt.axvspan(series_peaks[k], series_troughs[k], edgecolor= color, facecolor=color, alpha=alpha)
        else:
            ax.axvspan(series_peaks[k], series_troughs[k], edgecolor= color, facecolor=color, alpha=alpha)

def times(object1,object2):

    '''Multiplies the data from object1 with the data from object2.

    Args:
        object1 (int, float, numpy ndarray, or similar or fredpy series)
        object2 (int, float, numpy ndarray, or similar or fredpy series)


    Note:
        You are responsibile for making sure that multipying the series makes sense.

    Returns:
        fredpy series
    '''

    if not isinstance(object1, series) and not isinstance(object2, series):

        return object1*object2

    elif not isinstance(object1, series) and isinstance(object2, series):

        new_series = object2.copy()
        new_series.data = new_series.data*object1

        return new_series

    elif not isinstance(object2, series) and isinstance(object1, series):

        new_series = object1.copy()
        new_series.data = new_series.data*object2

        return new_series

    else:

        if not object1.data.index.equals(object2.data.index):

            raise ValueError('object1 and object2 do not have the same observation dates')

        else:

            new_series = series()

            new_series.title = object1.title +' times '+object2.title
            if object1.source == object2.source:
                new_series.source = object1.source
            else:
                new_series.source = object1.source +' and '+object2.source
            new_series.frequency = object1.frequency
            new_series.frequency_short = object1.frequency_short
            new_series.units = object1.units +' * '+object2.units
            new_series.units_short = object1.units_short +' * '+object2.units_short
            new_series.t = object1.t
            new_series.date_range = object1.date_range

            if object1.seasonal_adjustment == object2.seasonal_adjustment:
                new_series.seasonal_adjustment = object1.seasonal_adjustment
                new_series.seasonal_adjustment_short = object1.seasonal_adjustment_short
            else:
                new_series.seasonal_adjustment = object1.seasonal_adjustment +' and '+object2.seasonal_adjustment
                new_series.seasonal_adjustment_short = object1.seasonal_adjustment_short +' and '+object2.seasonal_adjustment_short

            if object1.last_updated == object2.last_updated:
                new_series.last_updated = object1.last_updated
            else:
                new_series.last_updated = object1.last_updated +' and '+object2.last_updated

            if object1.release == object2.release:
                new_series.release = object1.release
            else:
                new_series.release = object1.release +' and '+object2.release
                
            new_series.series_id = object1.series_id +' and '+object2.series_id
            new_series.data  = object1.data*object2.data

            return new_series


def to_fred_series(data,dates,frequency='',frequency_short='',last_updated='',notes='',release='',seasonal_adjustment='',seasonal_adjustment_short='',series_id='',source='',t=0,title='',units='',units_short=''):
    
    '''Create a FRED object from a set of data obtained from a different source.

    Args:
        data (numpy ndarray):                   Data
        dates (list or numpy ndarray):          Elements must be strings in 'MM-DD-YYYY' format
        frequency (string):                     Observation frequency. Options: '', 'Daily', 'Weekly', 'Monthly', 'Quarterly', or 'Annual'. Default: ''
        frequency_short (string):               Observation frequency abbreviated. Options: '', 'D', 'W', 'M', 'Q', or 'A'. Default: ''
        last_updated (string):                  Date data was last updated. Default = ''
        notes (string):                         Default: ''
        release (string):                       Notes about data. Default: ''
        seasonal_adjustment (string):           Default: ''
        seasonal_adjustment_short (string):     Default: ''
        series_id (string):                     FRED series ID. Default: ''
        source (string):                        Original source of data. Default: ''
        t (int):                                Number of observations per year. Default: 0
        title (string):                         Title of the data. Default: ''
        units (string):                         Default: ''
        units_short (string):                   Default: ''
        '''
    

    f = series()
    f.data = pd.Series(data,pd.to_datetime(dates))

    if frequency in ['Daily','Weekly','Monthly','Quarterly','Annual']:

        if frequency == 'Daily':
            t=365
            frequency_short = 'D'
        elif frequency == 'Weekly':
            t=52
            frequency_short = 'W'
        elif frequency == 'Monthly':
            t=12
            frequency_short = 'M'
        elif frequency == 'Quarterly':
            t=4
            frequency_short = 'Q'
        else:
            t=1
            frequency_short = 'A'

    elif frequency_short in ['D','W','M','Q','A']:

        if frequency_short == 'D':
            t=365
            frequency = 'Daily'
        elif frequency_short == 'W':
            t=52
            frequency = 'Weekly'
        elif frequency_short == 'M':
            t=12
            frequency = 'Monthly'
        elif frequency_short == 'Q':
            t=4
            frequency = 'Quarterly'
        else:
            t=1
            frequency = 'Annual'

    f.frequency = frequency
    f.frequency_short = frequency_short
    f.last_updated = last_updated
    f.notes = notes
    f.release = release
    f.seasonal_adjustment = seasonal_adjustment
    f.seasonal_adjustment_short = seasonal_adjustment_short
    f.series_id = series_id
    f.source = source
    f.title = title
    f.units = units
    f.units_short = units_short
    f.t = t
    f.date_range = 'Range: '+str(f.data.index[0])[:10]+' to '+str(f.data.index[-1])[:10]
    return f

def window_equalize(series_list):

    '''Adjusts the date windows for a collection of fredpy.series objects to the 
    smallest common date window.

    Args:
        series_list (list): A list of fredpy.series objects

    Returns:
        list
    '''

    minimums = []
    maximums = []
    for s in series_list:
        minimums.append(s.data.index[0])
        maximums.append(s.data.index[-1])

    start_end = [np.max(minimums),np.min(maximums)]

    new_list = []
    for s in series_list:

        new_list.append(s.window(start_end))

    return new_list
